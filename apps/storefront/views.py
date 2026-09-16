import logging

from django.conf import settings
from django.db import IntegrityError, OperationalError
from django.db.models import F, Prefetch
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.catalog.models import (
    Offer,
    OfferClick,
    OfferFamilyPlacement,
    OfferObservation,
    ProductFamily,
)
from apps.catalog.services.public_eligibility import public_eligibility_q

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
    return render(request, "storefront/home.html", context)


def product_family_detail(request, slug):
    family = get_object_or_404(_family_queryset(), slug=slug)
    _prepare_family(family)
    context = {
        "family": family,
        **_seo_context(
            request.path,
            f"{family.name} | Lowcost Europa",
            f"Ofertas atuais e informação factual para {family.name}.",
        ),
    }
    return render(request, "storefront/product_family_detail.html", context)


def institutional_page(request, page):
    page_title, meta_description = INSTITUTIONAL_PAGES[page]
    context = {
        "page_key": page,
        **_seo_context(request.path, page_title, meta_description),
    }
    return render(request, f"storefront/{page}.html", context)


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
