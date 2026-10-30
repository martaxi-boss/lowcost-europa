from dataclasses import dataclass
from typing import Iterable

from django.db.models import OuterRef, Q, Subquery
from django.db.models.functions import Trim

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


def observation_history_queryset():
    return OfferObservation.objects.order_by("-observed_at", "-pk")


def _has_valid_price(observation: OfferObservation) -> bool:
    return observation.price is not None and bool((observation.currency or "").strip())


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
    observations: Iterable[OfferObservation],
) -> PublicOfferObservationData:
    history = list(observations)
    return PublicOfferObservationData(
        price_observation=_first_matching(history, _has_valid_price),
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
