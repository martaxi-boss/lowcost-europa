import logging

from django.db import IntegrityError, OperationalError
from django.db.models import Prefetch
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from apps.catalog.models import Offer, OfferClick, OfferObservation, ProductFamily

logger = logging.getLogger(__name__)

PUBLIC_STATUS_LABELS = {
    ProductFamily.Status.NEW: "Em preparação",
    ProductFamily.Status.TESTING: "Em avaliação",
    ProductFamily.Status.OBSERVATION: "Em observação",
    ProductFamily.Status.RETIRED: "Indisponível",
}


def _family_queryset():
    observations = OfferObservation.objects.order_by("-observed_at", "-pk")[:1]
    offers = Offer.objects.filter(is_active=True).order_by(
        "-is_primary", "-last_seen_at", "-pk"
    ).prefetch_related(
        Prefetch("observations", queryset=observations, to_attr="latest_observations")
    )
    return ProductFamily.objects.prefetch_related(
        Prefetch("offers", queryset=offers, to_attr="active_offers")
    )


def _prepare_family(family):
    family.public_status = PUBLIC_STATUS_LABELS.get(family.status, "Em avaliação")
    for offer in family.active_offers:
        offer.latest_observation = (
            offer.latest_observations[0] if offer.latest_observations else None
        )
        offer.logistics_text = _logistics_text(offer.latest_observation)
        offer.can_redirect = bool(
            family.status != ProductFamily.Status.RETIRED and offer.affiliate_url
        )
    family.display_offer = next(
        (offer for offer in family.active_offers if offer.is_primary),
        family.active_offers[0] if family.active_offers else None,
    )
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


def home(request):
    families = [
        _prepare_family(family)
        for family in _family_queryset().exclude(status=ProductFamily.Status.RETIRED)
    ]
    return render(
        request,
        "storefront/home.html",
        {
            "families": families,
            "page_title": "Lowcost Europa",
            "meta_description": (
                "Produtos selecionados com informação factual de preço, oferta e logística."
            ),
        },
    )


def product_family_detail(request, slug):
    family = get_object_or_404(_family_queryset(), slug=slug)
    _prepare_family(family)
    return render(
        request,
        "storefront/product_family_detail.html",
        {
            "family": family,
            "page_title": f"{family.name} | Lowcost Europa",
            "meta_description": f"Ofertas atuais e informação factual para {family.name}.",
        },
    )


def offer_go(request, offer_id):
    eligible = Offer.objects.select_related("product_family").filter(
        pk=offer_id,
        is_active=True,
        product_family__isnull=False,
    ).exclude(product_family__status=ProductFamily.Status.RETIRED)
    offer = get_object_or_404(eligible)
    if not offer.affiliate_url:
        raise Http404

    destination = offer.affiliate_url
    try:
        OfferClick.objects.create(offer=offer)
    except (IntegrityError, OperationalError):
        logger.warning("Offer click persistence failed offer_id=%s", offer.pk)
    return HttpResponseRedirect(destination)
