from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum


class LogisticsFreshnessState(StrEnum):
    FRESH = "FRESH"
    STALE = "STALE"
    FUTURE = "FUTURE"


@dataclass(frozen=True)
class LogisticsFreshnessAssessment:
    state: LogisticsFreshnessState
    observed_at: datetime
    as_of: datetime
    age: timedelta
    max_age: timedelta
    is_fresh: bool
    reason: str


def _require_aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def assess_logistics_freshness(
    *,
    observed_at: datetime,
    as_of: datetime,
    max_age: timedelta,
) -> LogisticsFreshnessAssessment:
    _require_aware(observed_at, "observed_at")
    _require_aware(as_of, "as_of")
    if max_age <= timedelta(0):
        raise ValueError("max_age must be greater than zero")

    age = as_of - observed_at
    if age < timedelta(0):
        return LogisticsFreshnessAssessment(
            state=LogisticsFreshnessState.FUTURE,
            observed_at=observed_at,
            as_of=as_of,
            age=age,
            max_age=max_age,
            is_fresh=False,
            reason="observation timestamp is in the future",
        )

    if age <= max_age:
        return LogisticsFreshnessAssessment(
            state=LogisticsFreshnessState.FRESH,
            observed_at=observed_at,
            as_of=as_of,
            age=age,
            max_age=max_age,
            is_fresh=True,
            reason="observation is within the freshness window",
        )

    return LogisticsFreshnessAssessment(
        state=LogisticsFreshnessState.STALE,
        observed_at=observed_at,
        as_of=as_of,
        age=age,
        max_age=max_age,
        is_fresh=False,
        reason="observation is older than the freshness window",
    )


def supports_current_5d_candidate(*, evidence, freshness: LogisticsFreshnessAssessment) -> bool:
    return bool(evidence.supports_within_5_days and freshness.is_fresh)
