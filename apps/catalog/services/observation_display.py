from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable

from django.conf import settings
from django.db.models import OuterRef, Q, Subquery
from django.db.models.functions import Trim
from django.utils import timezone

from apps.catalog.models import OfferObservation


@dataclass(frozen=True)
class PublicOfferObservationData:
    price_observation: OfferObservation | None
    rating_observation: OfferObservation | None
    sales_observation: OfferObservation | None
    commission_observation: OfferObservation | None
    logistics_observation: OfferObservation | None

    @property
    def logistics_text(self) -> str | None:
        return logistics_text(self.logistics_observation)


def _latest_fact_id(condition, *, require_currency=False):
    """Select the latest observation for one fact and offer."""
    candidates = OfferObservation.objects.filter(offer_id=OuterRef("offer_id")).exclude(
        destination_country="ES"
    ).filter(
        condition
    )
    if require_currency:
        candidates = candidates.annotate(
            clean_currency=Trim("currency")
        ).exclude(clean_currency="")
    return Subquery(candidates.order_by("-observed_at", "-pk").values("pk")[:1])


def observation_history_queryset(*, require_recent_price=None):
    """Load no more than five historical factual rows for each visible offer."""
    if require_recent_price is None:
        require_recent_price = settings.PUBLIC_RECENT_PRICE_REQUIRED
    if require_recent_price:
        # Keep public price rendering aligned with the exact evidence gate.
        # The latest non-EUR, zero or future observation is not a public price.
        as_of = timezone.now()
        price = _latest_fact_id(
            Q(
                price__gt=0,
                currency__iexact="EUR",
                observed_at__gte=as_of - timedelta(hours=24),
                observed_at__lte=as_of,
            )
        )
    else:
        price = _latest_fact_id(
            Q(price__isnull=False, currency__isnull=False), require_currency=True
        )
    rating = _latest_fact_id(Q(evaluation_rate_percent__isnull=False))
    sales = _latest_fact_id(Q(sales_count__isnull=False))
    commission = _latest_fact_id(Q(commission_rate__isnull=False))
    logistics = _latest_fact_id(
        Q(search_delivery_days__isnull=False) | Q(delivery_days__isnull=False)
    )
    return OfferObservation.objects.filter(
        Q(pk=price) | Q(pk=rating) | Q(pk=sales) | Q(pk=commission)
        | Q(pk=logistics)
    ).order_by("-observed_at", "-pk")


def _has_valid_price(
    observation: OfferObservation, *, require_recent_price=None
) -> bool:
    currency = (observation.currency or "").strip()
    if observation.price is None or not currency:
        return False
    if require_recent_price is None:
        require_recent_price = settings.PUBLIC_RECENT_PRICE_REQUIRED
    if not require_recent_price:
        return True
    as_of = timezone.now()
    return bool(
        observation.price > 0
        and currency.upper() == "EUR"
        and currency == observation.currency
        and as_of - timedelta(hours=24) <= observation.observed_at <= as_of
    )


def _has_renderable_logistics(observation: OfferObservation) -> bool:
    # The current UI only has factual rendering rules for normalized numeric days.
    # Raw text fields remain attached to the real observation but are not parsed here.
    return (
        observation.search_delivery_days is not None
        or observation.delivery_days is not None
    )


def _first_matching(
    observations: Iterable[OfferObservation],
    predicate,
) -> OfferObservation | None:
    for observation in observations:
        if predicate(observation):
            return observation
    return None


def build_observation_display(
    observations: Iterable[OfferObservation], *, require_recent_price=None
) -> PublicOfferObservationData:
    # Spanish observations are private market evidence, never a replacement for
    # the existing Portuguese storefront's price/logistics or publication gate.
    history = [item for item in observations if item.destination_country != "ES"]
    return PublicOfferObservationData(
        price_observation=_first_matching(
            history,
            lambda observation: _has_valid_price(
                observation, require_recent_price=require_recent_price
            ),
        ),
        rating_observation=_first_matching(
            history,
            lambda observation: observation.evaluation_rate_percent is not None,
        ),
        sales_observation=_first_matching(
            history,
            lambda observation: observation.sales_count is not None,
        ),
        commission_observation=_first_matching(
            history,
            lambda observation: observation.commission_rate is not None,
        ),
        logistics_observation=_first_matching(history, _has_renderable_logistics),
    )


def logistics_text(observation: OfferObservation | None) -> str | None:
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
