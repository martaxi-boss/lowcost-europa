from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render

from apps.catalog.models import Offer, OfferObservation, ProductFamily

PUBLIC_STATUS_LABELS = {
    ProductFamily.Status.NEW: "Em preparação",
    ProductFamily.Status.TESTING: "Em avaliação",
    ProductFamily.Status.OBSERVATION: "Em observação",
    ProductFamily.Status.RETIRED: "Indisponível",
}


def _family_queryset():
    observations = OfferObservation.objects.order_by("-observed_at")
    offers = Offer.objects.filter(is_active=True).prefetch_related(
        Prefetch("observations", queryset=observations, to_attr="ordered_observations")
    )
    return ProductFamily.objects.prefetch_related(
        Prefetch("offers", queryset=offers, to_attr="active_offers")
    )


def _prepare_family(family):
    family.public_status = PUBLIC_STATUS_LABELS.get(family.status, "Em avaliação")
    for offer in family.active_offers:
        offer.latest_observation = (
            offer.ordered_observations[0] if offer.ordered_observations else None
        )
        offer.logistics_text = _logistics_text(offer.latest_observation)
    family.primary_offer = family.active_offers[0] if family.active_offers else None
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
    families = [_prepare_family(family) for family in _family_queryset()]
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
