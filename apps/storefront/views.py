import logging

from django.conf import settings
from django.db import IntegrityError, OperationalError
from django.db.models import F, Prefetch
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.cache import patch_vary_headers

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
    public_eligibility_q,
)

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
    offer.logistics_text = offer.observation_display.logistics_text
    offer.can_redirect = bool(family.status != ProductFamily.Status.RETIRED and offer.affiliate_url)
    offer.approved_candidate = (
        offer.approved_candidates_for_display[0] if offer.approved_candidates_for_display else None
    )
    return offer


def _prepare_family(family):
    family.public_status = PUBLIC_STATUS_LABELS.get(family.status, "Em avaliação")
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



def _public_indexing_active():
    return settings.PUBLIC_INDEXING_ENABLED and bool(settings.PUBLIC_SITE_URL)



def _seo_context(path, page_title, meta_description):
    indexing_active = _public_indexing_active()
    canonical_url = f"{settings.PUBLIC_SITE_URL}{path}" if indexing_active else None
    robots_directive = "index, follow" if indexing_active else "noindex, nofollow"
    return {
        "page_title": page_title,
        "meta_description": meta_description,
        "canonical_url": canonical_url,
        "robots_directive": robots_directive,
    }


def _render_storefront(request, template, context):
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
            request.path,
            "Lowcost Europa",
            "Produtos selecionados com informação factual de preço, oferta e logística.",
        ),
    }
    return _render_storefront(request, "storefront/home.html", context)


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
    rejected = [c for c in candidates if c.status == OfferCandidate.Status.REJECTED]
    approved = [c for c in candidates if c.status == OfferCandidate.Status.APPROVED]
    for candidate in approved:
        offer = candidate.approved_offer
        candidate.protocol_fresh = bool(offer and is_protocol_verified(offer))
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
    context = {
        "family": family,
        **_owner_family_context(request, family),
        **_seo_context(
            request.path,
            f"{family.name} | Lowcost Europa",
            f"Ofertas atuais e informação factual para {family.name}.",
        ),
    }
    return _render_storefront(request, "storefront/product_family_detail.html", context)


def institutional_page(request, page):
    page_title, meta_description = INSTITUTIONAL_PAGES[page]
    context = {
        "page_key": page,
        **_seo_context(request.path, page_title, meta_description),
    }
    return _render_storefront(request, f"storefront/{page}.html", context)


def whatsapp_contact(request):
    return HttpResponseRedirect(WHATSAPP_DESTINATION)


def robots_txt(request):
    if _public_indexing_active():
        body = "User-agent: *\nAllow: /\n"
        body += f"Sitemap: {settings.PUBLIC_SITE_URL}{reverse('storefront:sitemap')}\n"
    else:
        body = "User-agent: *\nDisallow: /\n"
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


def sitemap_xml(request):
    base_url = settings.PUBLIC_SITE_URL or request.build_absolute_uri("/").rstrip("/")
    paths = [
        reverse("storefront:home"),
        reverse("storefront:como-funciona"),
        reverse("storefront:afiliados"),
        reverse("storefront:privacidade"),
        reverse("storefront:termos"),
        reverse("storefront:contacto"),
    ]
    paths.extend(
        reverse("storefront:product-family-detail", kwargs={"slug": slug})
        for slug in ProductFamily.objects.exclude(status=ProductFamily.Status.RETIRED)
        .order_by("slug")
        .values_list("slug", flat=True)
    )
    urls = "".join(f"<url><loc>{base_url}{path}</loc></url>" for path in paths)
    body = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    return HttpResponse(body, content_type="application/xml")


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
    if not offer.affiliate_url:
        raise Http404

    destination = offer.affiliate_url
    try:
        OfferClick.objects.create(offer=offer)
    except (IntegrityError, OperationalError):
        logger.warning("Offer click persistence failed offer_id=%s", offer.pk)
    return HttpResponseRedirect(destination)
