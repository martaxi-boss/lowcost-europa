from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable

from django.conf import settings
from django.db.models import OuterRef, Q, Subquery
from django.db.models.functions import Trim
from django.utils import timezone

from apps.catalog.models import Offer, OfferObservation


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


def _latest_fact_id(condition, *, require_currency=False, outer_ref="offer_id", exclude_es=True):
    """Select the latest observation for one fact and offer."""
    candidates = OfferObservation.objects.filter(offer_id=OuterRef(outer_ref)).filter(condition)
    if exclude_es:
        candidates = candidates.exclude(destination_country="ES")
    if require_currency:
        candidates = candidates.annotate(
            clean_currency=Trim("currency")
        ).exclude(clean_currency="")
    return Subquery(candidates.order_by("-observed_at", "-pk").values("pk")[:1])


def _fact_ids(*, require_recent_price=None, outer_ref="offer_id", as_of=None):
    """Share the exact historical fact-selection rules between read paths."""
    if require_recent_price is None:
        require_recent_price = settings.PUBLIC_RECENT_PRICE_REQUIRED
    if require_recent_price:
        # Keep public price rendering aligned with the exact evidence gate.
        # The latest non-EUR, zero or future observation is not a public price.
        as_of = as_of or timezone.now()
        # Manual owner links are exempt from the 24-hour publication gate.
        # Keep their latest genuine PT/EUR price (with its original timestamp),
        # even when the availability-only monitor adds newer null-price rows.
        # Automatic offers still require a recent price and cannot borrow one.
        price = _latest_fact_id(
            Q(
                price__gt=0,
                currency__iexact="EUR",
                observed_at__gte=as_of - timedelta(hours=24),
                observed_at__lte=as_of,
            )
            | Q(
                offer__source=Offer.Source.ALIEXPRESS_OWNER,
                price__gt=0,
                currency__iexact="EUR",
                observed_at__lte=as_of,
            ),
            outer_ref=outer_ref,
        )
    else:
        price = _latest_fact_id(
            Q(price__isnull=False, currency__isnull=False), require_currency=True,
            outer_ref=outer_ref,
        )
    return {
        "fact_price": price,
        "fact_rating": _latest_fact_id(Q(evaluation_rate_percent__isnull=False), outer_ref=outer_ref),
        "fact_sales": _latest_fact_id(Q(sales_count__isnull=False), outer_ref=outer_ref),
        "fact_commission": _latest_fact_id(Q(commission_rate__isnull=False), outer_ref=outer_ref),
        "fact_logistics": _latest_fact_id(
            Q(search_delivery_days__isnull=False) | Q(delivery_days__isnull=False),
            outer_ref=outer_ref,
        ),
    }


def observation_history_queryset(*, require_recent_price=None):
    """Reference queryset: no more than five historical factual rows per offer."""
    condition = Q()
    for fact in _fact_ids(require_recent_price=require_recent_price).values():
        condition |= Q(pk=fact)
    return OfferObservation.objects.filter(condition).order_by("-observed_at", "-pk")


def load_public_observation_histories(offers, *, include_es_price=False, require_recent_price=None):
    """Select facts once per visible offer, then fetch only their distinct rows.

    The old observation-driven query repeatedly evaluated five correlated
    lookups for every historical observation (including availability-only rows).
    Starting from the bounded set of public Offer IDs avoids that outer scan.
    Two set-based queries, no cache, no data/schema changes, no per-offer queries.
    Multiple placements of an offer receive the same factual rows.
    """
    offers = list(offers)
    offer_ids = {offer.pk for offer in offers}
    if not offer_ids:
        return
    as_of = timezone.now()
    facts = _fact_ids(require_recent_price=require_recent_price, outer_ref="pk", as_of=as_of)
    if include_es_price:
        facts["fact_es_price"] = _latest_fact_id(
            Q(destination_country="ES", observed_at__gte=as_of - timedelta(hours=24),
              observed_at__lte=as_of, price__gt=0, currency__iexact="EUR"),
            outer_ref="pk", exclude_es=False,
        )
    selected = list(
        Offer.objects.filter(pk__in=offer_ids).order_by()
        .annotate(**facts).values_list(*facts)
    )
    row_ids = {pk for result in selected for pk in result if pk is not None}
    history = {pk: [] for pk in offer_ids}
    es_evidence = {pk: [] for pk in offer_ids}
    for observation in OfferObservation.objects.filter(pk__in=row_ids).order_by("-observed_at", "-pk"):
        target = es_evidence if observation.destination_country == "ES" else history
        target[observation.offer_id].append(observation)
    for offer in offers:
        offer.observation_history = history[offer.pk]
        offer.recent_es_price_evidence = es_evidence[offer.pk]


def _has_valid_price(
    observation: OfferObservation, *, require_recent_price=None,
    allow_historical_owner_price=False,
) -> bool:
    currency = (observation.currency or "").strip()
    if observation.price is None or not currency:
        return False
    if allow_historical_owner_price:
        return bool(
            observation.price > 0
            and currency.upper() == "EUR"
            and observation.observed_at <= timezone.now()
        )
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
    observations: Iterable[OfferObservation], *, require_recent_price=None,
    allow_historical_owner_price=False,
) -> PublicOfferObservationData:
    # Spanish observations are private market evidence, never a replacement for
    # the existing Portuguese storefront's price/logistics or publication gate.
    history = [item for item in observations if item.destination_country != "ES"]
    return PublicOfferObservationData(
        price_observation=_first_matching(
            history,
            lambda observation: _has_valid_price(
                observation, require_recent_price=require_recent_price,
                allow_historical_owner_price=allow_historical_owner_price,
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
