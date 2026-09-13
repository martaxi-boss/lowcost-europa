from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta

from apps.catalog.models import Offer, OfferObservation
from apps.catalog.services.logistics_evidence import (
    LogisticsEvidenceState,
    assess_logistics_evidence,
)
from apps.catalog.services.logistics_freshness import (
    LogisticsFreshnessState,
    assess_logistics_freshness,
    supports_current_5d_candidate,
)


@dataclass(frozen=True)
class LogisticsHistoryItem:
    observation_pk: int | None
    observed_at: datetime
    search_delivery_days: int | None
    detail_delivery_days: int | None
    evidence_state: LogisticsEvidenceState
    freshness_state: LogisticsFreshnessState
    supports_5d: bool
    supports_current_5d: bool

@dataclass(frozen=True)
class LogisticsHistoryAssessment:
    observation_count: int
    first_observed_at: datetime | None
    last_observed_at: datetime | None
    observation_span: timedelta | None
    evidence_state_counts: dict[LogisticsEvidenceState, int]
    freshness_state_counts: dict[LogisticsFreshnessState, int]
    supports_5d_count: int
    supports_current_5d_count: int
    has_conflict: bool
    has_future: bool
    latest: LogisticsHistoryItem | None


def _observation_sort_key(observation):
    pk = getattr(observation, "pk", None)
    return (observation.observed_at, -1 if pk is None else pk)


def assess_logistics_history(*, observations, as_of: datetime, max_age: timedelta):
    ordered = sorted(observations, key=_observation_sort_key)
    evidence_counts = Counter({state: 0 for state in LogisticsEvidenceState})
    freshness_counts = Counter({state: 0 for state in LogisticsFreshnessState})
    items: list[LogisticsHistoryItem] = []

    for observation in ordered:
        evidence = assess_logistics_evidence(
            search_delivery_days=observation.search_delivery_days,
            detail_delivery_days=observation.delivery_days,
        )
        freshness = assess_logistics_freshness(
            observed_at=observation.observed_at,
            as_of=as_of,
            max_age=max_age,
        )
        current_support = supports_current_5d_candidate(
            evidence=evidence,
            freshness=freshness,
        )
        evidence_counts[evidence.state] += 1
        freshness_counts[freshness.state] += 1
        items.append(
            LogisticsHistoryItem(
                observation_pk=getattr(observation, "pk", None),
                observed_at=observation.observed_at,
                search_delivery_days=observation.search_delivery_days,
                detail_delivery_days=observation.delivery_days,
                evidence_state=evidence.state,
                freshness_state=freshness.state,
                supports_5d=evidence.supports_within_5_days,
                supports_current_5d=current_support,
            )
        )

    count = len(items)
    first = items[0].observed_at if items else None
    last = items[-1].observed_at if items else None
    span = (last - first) if count > 1 else (timedelta(0) if count == 1 else None)
    return LogisticsHistoryAssessment(
        observation_count=count,
        first_observed_at=first,
        last_observed_at=last,
        observation_span=span,
        evidence_state_counts=dict(evidence_counts),
        freshness_state_counts=dict(freshness_counts),
        supports_5d_count=sum(item.supports_5d for item in items),
        supports_current_5d_count=sum(item.supports_current_5d for item in items),
        has_conflict=any(item.evidence_state is LogisticsEvidenceState.CONFLICT for item in items),
        has_future=any(item.freshness_state is LogisticsFreshnessState.FUTURE for item in items),
        latest=items[-1] if items else None,
    )


def assess_offer_logistics_history(*, offer: Offer, as_of: datetime, max_age: timedelta):
    observations = list(
        OfferObservation.objects.filter(offer=offer).order_by("observed_at", "pk")
    )
    return assess_logistics_history(observations=observations, as_of=as_of, max_age=max_age)
