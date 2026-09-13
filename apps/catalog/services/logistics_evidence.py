from dataclasses import dataclass
from enum import StrEnum


class LogisticsEvidenceState(StrEnum):
    UNKNOWN = "UNKNOWN"
    SEARCH_ONLY = "SEARCH_ONLY"
    DETAIL_ONLY = "DETAIL_ONLY"
    CONSISTENT = "CONSISTENT"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True)
class LogisticsEvidenceAssessment:
    state: LogisticsEvidenceState
    search_delivery_days: int | None
    detail_delivery_days: int | None
    supports_within_5_days: bool
    reason: str


def assess_logistics_evidence(
    *,
    search_delivery_days: int | None,
    detail_delivery_days: int | None,
) -> LogisticsEvidenceAssessment:
    if search_delivery_days is None and detail_delivery_days is None:
        return LogisticsEvidenceAssessment(
            state=LogisticsEvidenceState.UNKNOWN,
            search_delivery_days=None,
            detail_delivery_days=None,
            supports_within_5_days=False,
            reason="no interpretable logistics evidence",
        )

    if detail_delivery_days is None:
        return LogisticsEvidenceAssessment(
            state=LogisticsEvidenceState.SEARCH_ONLY,
            search_delivery_days=search_delivery_days,
            detail_delivery_days=None,
            supports_within_5_days=search_delivery_days <= 5,
            reason="search endpoint evidence only",
        )

    if search_delivery_days is None:
        return LogisticsEvidenceAssessment(
            state=LogisticsEvidenceState.DETAIL_ONLY,
            search_delivery_days=None,
            detail_delivery_days=detail_delivery_days,
            supports_within_5_days=detail_delivery_days <= 5,
            reason="detail endpoint evidence only",
        )

    if search_delivery_days == detail_delivery_days:
        return LogisticsEvidenceAssessment(
            state=LogisticsEvidenceState.CONSISTENT,
            search_delivery_days=search_delivery_days,
            detail_delivery_days=detail_delivery_days,
            supports_within_5_days=search_delivery_days <= 5,
            reason="search and detail endpoints agree",
        )

    return LogisticsEvidenceAssessment(
        state=LogisticsEvidenceState.CONFLICT,
        search_delivery_days=search_delivery_days,
        detail_delivery_days=detail_delivery_days,
        supports_within_5_days=False,
        reason="search and detail endpoints disagree",
    )
