import json
import logging
import unicodedata
from datetime import timedelta

from django.conf import settings
from django.core.paginator import Paginator
from django.db import IntegrityError, OperationalError
from django.db.models import F, Prefetch
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.cache import patch_vary_headers
from django.views.decorators.http import require_safe

from apps.catalog.models import (
    Offer,
    OfferCandidate,
    OfferClick,
    OfferFamilyPlacement,
    ProductFamily,
)
from apps.catalog.services.candidate_approval import OWNER_REJECTION_REASON_CHOICES
from apps.catalog.services.observation_display import (
    build_observation_display,
    observation_history_queryset,
)
from apps.catalog.services.public_eligibility import (
    is_protocol_verified,
    is_ship_from_verified,
    public_eligibility_q,
)
from apps.catalog.services.weekly_discovery import PENDING_CAP_PER_FAMILY
from apps.integrations.aliexpress.affiliate_url import is_https_affiliate_url
from apps.storefront.seo import PRIVATE_PATH_PREFIXES, public_indexing_active
from apps.storefront.seo_editorial import guide_for_category
from apps.storefront.seo_locales import (
    alternate_public_urls,
    home_page_url,
    localized_public_path,
    requested_seo_locale,
)
from apps.storefront.ui_translations import translate_ui

LEGACY_FAMILY_REDIRECTS = {
    "depilacao-laser-triple-wave": "diodo-laser-remocao-tatuagens-pigmentacao",
    "remocao-tatuagens-pigmentacao": "diodo-laser-remocao-tatuagens-pigmentacao",
}

logger = logging.getLogger(__name__)

WHATSAPP_DESTINATION = (
    "https://wa.me/351965471236"
    "?text=Ol%C3%A1%2C%20vi%20um%20equipamento%20no%20Lowcost%20Europa%20"
    "e%20gostava%20de%20esclarecer%20uma%20d%C3%BAvida."
)

PUBLIC_STATUS_LABELS = {
    ProductFamily.Status.NEW: "Em preparação",
    ProductFamily.Status.TESTING: "Em avaliação",
    ProductFamily.Status.OBSERVATION: "Em observação",
    ProductFamily.Status.RETIRED: "Indisponível",
}

INSTITUTIONAL_PAGES = {
    "como-funciona": (
        "Como funciona | Lowcost Europa",
        "Como o Lowcost Europa seleciona ofertas e encaminha a compra para o vendedor.",
    ),
    "afiliados": (
        "Afiliados | Lowcost Europa",
        "Transparência sobre a relação de afiliado do Lowcost Europa.",
    ),
    "privacidade": (
        "Privacidade | Lowcost Europa",
        "Informação sobre registos de encaminhamento e logs técnicos no Lowcost Europa.",
    ),
    "termos": (
        "Termos de Utilização | Lowcost Europa",
        "Informação sobre a utilização do Lowcost Europa, encaminhamento para vendedores externos "
        "e relação de afiliado.",
    ),
    "contacto": (
        "Contacto | Lowcost Europa",
        "Contactos institucionais do Lowcost Europa para informação, "
        "transparência e correções factuais.",
    ),
}


def _family_queryset():
    placements = (
        OfferFamilyPlacement.objects.filter(public_eligibility_q(prefix="offer__"))
        .select_related("offer")
        .prefetch_related(
            Prefetch(
                "offer__observations",
                queryset=observation_history_queryset(),
                to_attr="observation_history",
            ),
            Prefetch(
                "offer__approved_candidates",
                queryset=OfferCandidate.objects.filter(status=OfferCandidate.Status.APPROVED).order_by(
                    "pk"
                ),
                to_attr="approved_candidates_for_display",
            ),
        )
        .order_by(
            F("selection_position").asc(nulls_last=True),
            "display_order",
            "-offer__last_seen_at",
            "-offer__pk",
        )
    )
    return ProductFamily.objects.order_by("display_order", "name", "pk").prefetch_related(
        Prefetch("offer_placements", queryset=placements, to_attr="public_placements")
    )


def _prepare_offer(offer, family):
    offer.observation_display = build_observation_display(offer.observation_history)
    # A presentation notice only, never an expiry or a publication gate.
    cutoff = timezone.now() - timedelta(days=7)
    price = offer.observation_display.price_observation
    logistics = offer.observation_display.logistics_observation
    offer.price_observation_old = bool(price and price.observed_at < cutoff)
    offer.logistics_observation_old = bool(logistics and logistics.observed_at < cutoff)
    offer.logistics_text = offer.observation_display.logistics_text
    offer.owner_origin_verified = is_ship_from_verified(offer)
    offer.can_redirect = bool(family.status != ProductFamily.Status.RETIRED and offer.affiliate_url)
    offer.approved_candidate = (
        offer.approved_candidates_for_display[0] if offer.approved_candidates_for_display else None
    )
    return offer


def _prepare_family(family):
    from django.utils.translation import get_language

    lang = get_language()
    family.public_status = translate_ui(
        PUBLIC_STATUS_LABELS.get(family.status, "Em avaliação"), lang
    )
    if family.status == ProductFamily.Status.NEW and family.public_placements:
        family.public_status = translate_ui("Seleção em avaliação", lang)
    if family.status == ProductFamily.Status.RETIRED:
        placements = []
    else:
        placements = family.public_placements

    for placement in placements:
        _prepare_offer(placement.offer, family)

    family.selection_placements = [
        placement for placement in placements if placement.selection_position is not None
    ]
    family.other_placements = [
        placement for placement in placements if placement.selection_position is None
    ]
    family.active_offers = [placement.offer for placement in placements]
    family.display_offer = placements[0].offer if placements else None
    return family



def _json_ld(data):
    """Encode trusted schema values without allowing inline script injection."""
    return (
        json.dumps(data, ensure_ascii=True, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def _seo_context(request, page_title, meta_description, *, kind=None, category=None):
    path = request.path
    indexing_active = public_indexing_active(request)
    canonical_url = f"{settings.PUBLIC_SITE_URL}{path}" if indexing_active else None
    robots_directive = "index, follow" if indexing_active else "noindex, nofollow"
    alternates = (
        alternate_public_urls(path, settings.PUBLIC_SITE_URL)
        if indexing_active and settings.LOCALE_SEO_ENABLED
        else []
    )
    structured = None
    if indexing_active and kind == "home":
        structured = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "Organization",
                    "name": "Lowcost Europa",
                    "url": settings.PUBLIC_SITE_URL + "/",
                },
                {
                    "@type": "WebSite",
                    "name": "Lowcost Europa",
                    "url": settings.PUBLIC_SITE_URL + "/",
                },
            ],
        }
    elif indexing_active and kind == "category" and category:
        structured = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Lowcost Europa",
                    "item": settings.PUBLIC_SITE_URL + home_page_url(request),
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": category,
                    "item": canonical_url,
                },
            ],
        }
    return {
        "page_title": page_title,
        "meta_description": meta_description,
        "canonical_url": canonical_url,
        "robots_directive": robots_directive,
        "seo_alternates": alternates,
        "structured_data_json": _json_ld(structured) if structured else None,
    }


def _render_storefront(request, template, context):
    context["social_image_url"] = request.build_absolute_uri(
        static("storefront/lowcost-europa-brand-main.webp")
    )
    context["geo_language_enabled"] = settings.GEO_LANGUAGE_ENABLED
    context["seo_locale_explicit"] = bool(requested_seo_locale(request.path_info))
    context["public_operator"] = settings.PUBLIC_OPERATOR
    response = render(request, template, context)
    if request.user.is_authenticated and request.user.is_staff:
        response["Cache-Control"] = "private, no-store"
        response["X-Robots-Tag"] = "noindex, nofollow"
        patch_vary_headers(response, ("Cookie",))
    return response


def home(request):
    families = [
        _prepare_family(family)
        for family in _family_queryset().exclude(status=ProductFamily.Status.RETIRED)
    ]
    context = {
        "families": families,
        **_seo_context(
            request,
            translate_ui(
                "Lowcost Europa | Equipamentos de estética profissional",
                getattr(request, "LANGUAGE_CODE", "pt-pt"),
            ),
            {
                "pt-pt": (
                    "Explore equipamentos de estética profissional, preços observados "
                    "e informação de entrega sem promessas não verificadas."
                ),
                "es": (
                    "Explora equipos de estética profesional, precios observados "
                    "e información de entrega sin promesas no verificadas."
                ),
                "en": (
                    "Explore professional beauty equipment, observed prices "
                    "and available delivery information."
                ),
                "fr": (
                    "Découvrez des équipements d’esthétique professionnelle, "
                    "des prix observés et les informations de livraison disponibles."
                ),
                "de": (
                    "Entdecken Sie professionelle Kosmetikgeräte, beobachtete "
                    "Preise und verfügbare Lieferinformationen."
                ),
            }.get(
                getattr(request, "LANGUAGE_CODE", "pt-pt"),
                "Equipamentos de estética profissional com informação factual.",
            ),
            kind="home",
        ),
    }
    return _render_storefront(request, "storefront/home.html", context)


def locale_home(request, locale):
    """Reversible market launch: no indexed locale URL before QA activation."""
    if not settings.LOCALE_SEO_ENABLED or locale not in {"pt", "es"}:
        raise Http404
    return home(request)


def locale_product_family_detail(request, locale, slug):
    if not settings.LOCALE_SEO_ENABLED or locale not in {"pt", "es"}:
        raise Http404
    return product_family_detail(request, slug)


def _search_key(value):
    """Accent-insensitive visitor search, without exposing unpublished listings."""
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(character)
    )


@require_safe
def search(request):
    """Public, read-only search over the same strictly eligible family offers."""
    phrase = request.GET.get("q", "").strip()[:100]
    normalized = _search_key(phrase)
    terms = normalized.split()
    matches = []
    if terms:
        families = _family_queryset().exclude(status=ProductFamily.Status.RETIRED)
        for family in families:
            _prepare_family(family)
            for placement in family.selection_placements + family.other_placements:
                offer = placement.offer
                haystack = _search_key(f"{family.name} {offer.title or ''}")
                if all(term in haystack for term in terms):
                    matches.append({"family": family, "offer": offer, "placement": placement})

    pages = Paginator(matches, 24)
    page = pages.get_page(request.GET.get("page"))
    context = {
        "query": phrase,
        "result_count": len(matches),
        "page": page,
        **_seo_context(
            request,
            "Pesquisar equipamentos | Lowcost Europa",
            "Pesquisa de ofertas editoriais elegíveis no catálogo Lowcost Europa.",
        ),
    }
    # Search-result permutations must never be indexed, even after launch.
    context["robots_directive"] = "noindex, nofollow"
    context["canonical_url"] = None
    response = _render_storefront(request, "storefront/search.html", context)
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response


def _owner_family_context(request, family):
    if not (request.user.is_authenticated and request.user.is_staff):
        return {}

    preview_public = request.GET.get("owner_preview") == "public"
    if preview_public:
        return {
            "owner_preview_public": True,
            "owner_return_to_management": f"{request.path}?gestao=montra#gestao-owner",
        }
    if family.status == ProductFamily.Status.RETIRED:
        return {"owner_mode": True, "owner_active_tab": "montra"}

    active_tab = request.GET.get("gestao", "montra")
    allowed_tabs = {"montra", "rever", "aprovados", "retirados", "revalidar", "rejeitados"}
    if active_tab not in allowed_tabs:
        active_tab = "montra"

    candidates = list(
        OfferCandidate.objects.filter(product_family=family)
        .select_related("approved_offer")
        .order_by("status", "-last_observed_at", "pk")
    )
    pending = [c for c in candidates if c.status == OfferCandidate.Status.PENDING]
    requested_order = request.GET.get("ordem", "")
    pending_order = (
        requested_order
        if requested_order in {"antigos", "recentes"}
        else ("antigos" if len(pending) >= PENDING_CAP_PER_FAMILY else "recentes")
    )
    pending.sort(
        key=lambda c: (c.last_observed_at, c.pk),
        reverse=(pending_order == "recentes"),
    )
    rejected = [c for c in candidates if c.status == OfferCandidate.Status.REJECTED]
    approved = [c for c in candidates if c.status == OfferCandidate.Status.APPROVED]
    published_offer_ids = set(
        OfferFamilyPlacement.objects.filter(product_family=family)
        .filter(public_eligibility_q(prefix="offer__"))
        .values_list("offer_id", flat=True)
    )
    for candidate in approved:
        offer = candidate.approved_offer
        candidate.protocol_fresh = bool(offer and is_protocol_verified(offer))
        candidate.origin_verified = bool(offer and is_ship_from_verified(offer))
        if not offer:
            candidate.owner_state_label = "Aprovado"
        elif not offer.is_active:
            candidate.owner_state_label = "Indisponível"
        elif not candidate.protocol_fresh:
            candidate.owner_state_label = "Revalidação necessária"
        elif offer.owner_hidden and offer.editorial_events.filter(action="HIDE").exists():
            candidate.owner_state_label = "Retirado da montra"
        elif offer.owner_hidden:
            candidate.owner_state_label = "Aprovado fora da montra"
        elif offer.pk not in published_offer_ids:
            candidate.owner_state_label = "Fora da montra — validar preço e promoção"
        else:
            candidate.owner_state_label = "Na montra"

    hidden = [
        c
        for c in approved
        if c.approved_offer
        and c.approved_offer.owner_hidden
        and c.approved_offer.editorial_events.filter(action="HIDE").exists()
    ]
    approved_hidden = [
        c
        for c in approved
        if c.approved_offer
        and c.approved_offer.owner_hidden
        and c.protocol_fresh
        and not c.approved_offer.editorial_events.filter(action="HIDE").exists()
    ]
    stale = [c for c in approved if c.approved_offer and not c.protocol_fresh]
    selected_candidates = {
        "rever": pending,
        "aprovados": approved_hidden,
        "rejeitados": rejected,
        "retirados": hidden,
        "revalidar": stale,
    }.get(active_tab, [])

    current_query = f"?gestao={active_tab}"
    if active_tab == "rever":
        current_query += f"&ordem={pending_order}"
    return {
        "owner_mode": True,
        "owner_active_tab": active_tab,
        "owner_selected_candidates": selected_candidates,
        "owner_rejection_reason_choices": OWNER_REJECTION_REASON_CHOICES,
        "owner_target_families": ProductFamily.objects.exclude(status=ProductFamily.Status.RETIRED)
        .exclude(pk=family.pk)
        .order_by("display_order", "name", "pk"),
        "owner_storefront_count": len(family.public_placements),
        "owner_pending_count": len(pending),
        "owner_pending_order": pending_order,
        "owner_queue_blocked": len(pending) >= PENDING_CAP_PER_FAMILY,
        "owner_pending_cap": PENDING_CAP_PER_FAMILY,
        "owner_to_review_for_search": max(0, len(pending) - PENDING_CAP_PER_FAMILY + 1),
        "owner_approved_count": len(approved_hidden),
        "owner_hidden_count": len(hidden),
        "owner_revalidate_count": len(stale),
        "owner_rejected_count": len(rejected),
        "owner_return_url": f"{request.path}{current_query}#gestao-owner",
        "owner_preview_url": f"{request.path}?owner_preview=public",
        "owner_error": request.session.pop("owner_panel_error", ""),
        "owner_notice": request.session.pop("owner_panel_notice", ""),
    }


def product_family_detail(request, slug):
    redirect_slug = LEGACY_FAMILY_REDIRECTS.get(slug)
    if redirect_slug and ProductFamily.objects.filter(slug=redirect_slug).exists():
        return redirect("storefront:product-family-detail", slug=redirect_slug)
    family = get_object_or_404(_family_queryset(), slug=slug)
    _prepare_family(family)
    language = getattr(request, "LANGUAGE_CODE", "pt-pt")
    guide = guide_for_category(family.slug, language)
    page_title = (
        guide["title"]
        if guide
        else f"{translate_ui(family.name, language)} | Lowcost Europa"
    )
    meta_description = (
        guide["description"]
        if guide
        else (
            f"Explora opciones y datos observados de {translate_ui(family.name, 'es')}. "
            "Precios y disponibilidad sujetos a confirmación del vendedor."
            if language == "es"
            else f"Compare ofertas e informação observada para {family.name}. "
                 "Confirme preço e disponibilidade no parceiro."
        )
    )
    context = {
        "family": family,
        "family_seo_guide": guide,
        **_owner_family_context(request, family),
        **_seo_context(
            request,
            page_title,
            meta_description,
            kind="category",
            category=translate_ui(family.name, getattr(request, "LANGUAGE_CODE", "pt-pt")),
        ),
    }
    if family.status == ProductFamily.Status.RETIRED:
        context["robots_directive"] = "noindex, nofollow"
        context["canonical_url"] = None
        context["seo_alternates"] = []
        context["structured_data_json"] = None
    response = _render_storefront(request, "storefront/product_family_detail.html", context)
    if family.status == ProductFamily.Status.RETIRED:
        response["X-Robots-Tag"] = "noindex, nofollow"
    return response


def institutional_page(request, page):
    page_title, meta_description = INSTITUTIONAL_PAGES[page]
    context = {
        "page_key": page,
        **_seo_context(request, page_title, meta_description),
    }
    return _render_storefront(request, f"storefront/{page}.html", context)


def whatsapp_contact(request):
    return HttpResponseRedirect(WHATSAPP_DESTINATION)


@require_safe
def indexnow_key(request, key):
    # The protocol requires a public proof file; keep configuration out of source/logs.
    if (not public_indexing_active(request) or not settings.INDEXNOW_KEY
            or key != settings.INDEXNOW_KEY):
        raise Http404
    response = HttpResponse(key, content_type="text/plain; charset=utf-8")
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response


def robots_txt(request):
    if public_indexing_active(request):
        body = "User-agent: *\nAllow: /\n"
        body += "".join(f"Disallow: {path}\n" for path in PRIVATE_PATH_PREFIXES)
        body += "Disallow: /pesquisar/\n"
        body += f"Sitemap: {settings.PUBLIC_SITE_URL}{reverse('storefront:sitemap')}\n"
    else:
        body = "User-agent: *\nDisallow: /\n"
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


def _sitemap_urls(request):
    base_url = settings.PUBLIC_SITE_URL or request.build_absolute_uri("/").rstrip("/")
    paths = [
        reverse("storefront:home"),
        reverse("storefront:como-funciona"),
        reverse("storefront:afiliados"),
        reverse("storefront:privacidade"),
        reverse("storefront:termos"),
        reverse("storefront:contacto"),
    ]
    slugs = list(
        ProductFamily.objects.exclude(status=ProductFamily.Status.RETIRED)
        .order_by("slug").values_list("slug", flat=True)
    )
    paths.extend(
        reverse("storefront:product-family-detail", kwargs={"slug": slug})
        for slug in slugs
    )
    if settings.LOCALE_SEO_ENABLED and public_indexing_active(request):
        # Keep the existing 11 URLs and add only real, stable PT/ES pages.
        for locale in ("pt", "es"):
            paths.append(localized_public_path("/", locale))
            paths.extend(
                localized_public_path(
                    reverse("storefront:product-family-detail", kwargs={"slug": slug}),
                    locale,
                )
                for slug in slugs
            )
    return [f"{base_url}{path}" for path in paths]


def sitemap_xml(request):
    urls = "".join(f"<url><loc>{url}</loc></url>" for url in _sitemap_urls(request))
    body = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    return HttpResponse(body, content_type="application/xml")


@require_safe
def sitemap_txt(request):
    """Alternative Google-supported format using the same public URL source."""
    return HttpResponse("\n".join(_sitemap_urls(request)) + "\n",
                        content_type="text/plain; charset=utf-8")


def _should_record_offer_click(request):
    """Exclude speculative requests, not claim to identify unique human buyers."""
    if request.method != "GET":
        return False
    purpose = " ".join(
        (
            request.headers.get("Sec-Purpose", ""),
            request.headers.get("Purpose", ""),
            request.headers.get("X-Moz", ""),
        )
    ).lower()
    return "prefetch" not in purpose and "prerender" not in purpose


@require_safe
def offer_go(request, offer_id):
    eligible = Offer.objects.filter(
        public_eligibility_q(),
        pk=offer_id,
        family_placements__product_family__status__in=[
            ProductFamily.Status.NEW,
            ProductFamily.Status.TESTING,
            ProductFamily.Status.VERIFIED,
            ProductFamily.Status.PROVEN,
            ProductFamily.Status.WINNER,
            ProductFamily.Status.OBSERVATION,
        ],
    ).distinct()
    offer = get_object_or_404(eligible)
    if not is_https_affiliate_url(offer.affiliate_url):
        raise Http404

    destination = offer.affiliate_url
    if _should_record_offer_click(request):
        try:
            OfferClick.objects.create(offer=offer)
        except (IntegrityError, OperationalError):
            logger.warning("Offer click persistence failed offer_id=%s", offer.pk)
    response = HttpResponseRedirect(destination)
    response["Cache-Control"] = "private, no-store"
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response
