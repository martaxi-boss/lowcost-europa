import logging

from django.conf import settings
from django.db import IntegrityError, OperationalError
from django.db.models import F, Prefetch
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.cache import patch_vary_headers

from apps.catalog.models import (
    CandidateDecision,
    Offer,
    OfferCandidate,
    OfferClick,
    OfferFamilyPlacement,
    OfferObservation,
    ProductFamily,
)
from apps.catalog.services.public_eligibility import (
    is_protocol_verification_fresh,
    public_eligibility_q,
)

LEGACY_FAMILY_REDIRECTS = {
    "depilacao-laser-triple-wave": "diodo-laser-remocao-tatuagens-pigmentacao",
    "remocao-tatuagens-pigmentacao": "diodo-laser-remocao-tatuagens-pigmentacao",
}

logger = logging.getLogger(__name__)

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
        "Informação factual sobre tracking de cliques, cookies e logs técnicos.",
    ),
    "termos": (
        "Termos — pré-lançamento | Lowcost Europa",
        "Estrutura de termos ainda não pronta para lançamento público.",
    ),
    "contacto": (
        "Contacto | Lowcost Europa",
        "Contactos institucionais do Lowcost Europa para informação, "
        "transparência e correções factuais.",
    ),
}


def _family_queryset():
    observations = OfferObservation.objects.order_by("-observed_at", "-pk")[:1]
    placements = (
        OfferFamilyPlacement.objects.filter(public_eligibility_q(prefix="offer__"))
        .select_related("offer")
        .prefetch_related(
            Prefetch(
                "offer__observations",
                queryset=observations,
                to_attr="latest_observations",
            )
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
    offer.latest_observation = offer.latest_observations[0] if offer.latest_observations else None
    offer.logistics_text = _logistics_text(offer.latest_observation)
    offer.can_redirect = bool(family.status != ProductFamily.Status.RETIRED and offer.affiliate_url)
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


def _logistics_text(observation):
    if observation is None:
        return None
    search_days = observation.search_delivery_days
    detail_days = observation.delivery_days
    if search_days is not None and detail_days is not None:
        if search_days == detail_days:
            return f"Pesquisa e detalhe indicaram {search_days} dias"
        return "As fontes apresentam estimativas diferentes"
    if search_days is not None:
        return f"Estimativa indicada pela pesquisa: {search_days} dias"
    if detail_days is not None:
        return f"Estimativa indicada no detalhe: {detail_days} dias"
    return None


def _public_indexing_active():
    return settings.PUBLIC_INDEXING_ENABLED and bool(settings.PUBLIC_SITE_URL)


OWNER_SEMANTIC_REJECTION_CHOICES = (
    (CandidateDecision.Reason.WRONG_FAMILY, "Produto da família errada"),
    (CandidateDecision.Reason.ACCESSORY_OR_PART, "Acessório / peça / consumível"),
    (CandidateDecision.Reason.POOR_LISTING, "Produto/listagem sem qualidade suficiente"),
    (CandidateDecision.Reason.OTHER, "Outro motivo semântico/comercial"),
)

def _seo_context(path, page_title, meta_description):
    base_url = settings.PUBLIC_SITE_URL
    canonical_url = f"{base_url}{path}" if base_url else None
    robots_directive = "index, follow" if _public_indexing_active() else "noindex, nofollow"
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
        candidate.protocol_fresh = bool(offer and is_protocol_verification_fresh(offer))
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
        "owner_review_signals": CandidateDecision.ReviewSignal.choices,
        "semantic_rejection_choices": OWNER_SEMANTIC_REJECTION_CHOICES,
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
