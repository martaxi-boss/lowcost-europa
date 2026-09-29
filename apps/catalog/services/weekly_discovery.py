from dataclasses import dataclass, field

from django.utils import timezone

from apps.catalog.models import OfferCandidate, ProductFamily
from apps.catalog.services.deep_discovery import DeepDiscoveryResult, discover_family_deep
from apps.catalog.services.family_profiles import get_family_profile
from apps.integrations.aliexpress.client import AliExpressClient
from apps.integrations.aliexpress.exceptions import (
    AliExpressAuthenticationError,
    AliExpressConfigurationError,
    AliExpressError,
    AliExpressRateLimitError,
    AliExpressRuntimeStateError,
)

WEEKLY_FAMILY_SLUGS = (
    "cavitacao-rf-vacuum-corpo",
    "hydrodermoabrasao-aqua-facial-multifuncoes",
    "pressoterapia-vacuum-drenagem",
    "hifu",
    "diodo-laser-remocao-tatuagens-pigmentacao",
)
PENDING_CAP_PER_FAMILY = 20
MAX_SEARCH_OPERATIONS_PER_FAMILY = 4
MAX_DETAIL_ATTEMPTS_PER_FAMILY = 6
MAX_PAGES_PER_KEYWORD = 2
SEARCH_PAGE_SIZE = 10
MAX_DETAILS_PER_PAGE = 3


@dataclass
class WeeklyFamilyResult:
    family_slug: str
    pending_before: int
    search_operations: int = 0
    detail_attempts: int = 0
    new_candidates: int = 0
    duplicates_ignored: int = 0
    historical_rejections_ignored: int = 0
    transient_errors: int = 0
    pending_after: int = 0
    queue_cap_hit: bool = False
    failures: list[str] = field(default_factory=list)


@dataclass
class WeeklyDiscoveryReport:
    families: list[WeeklyFamilyResult]
    started_at: object
    finished_at: object


def _pending_count(family):
    return OfferCandidate.objects.filter(
        product_family=family,
        status=OfferCandidate.Status.PENDING,
    ).count()


def _aggregate_deep(family, pending_before, result, *, extra_transient=0):
    pages = [page.result for page in result.pages]
    pending_after = _pending_count(family)
    return WeeklyFamilyResult(
        family_slug=family.slug,
        pending_before=pending_before,
        search_operations=result.search_operations,
        detail_attempts=result.detail_attempts,
        new_candidates=result.created,
        duplicates_ignored=sum(
            item.skipped_duplicate_in_batch
            + item.skipped_existing_offer
            + item.skipped_existing_candidate
            + item.skipped_known_other_family
            for item in pages
        ),
        historical_rejections_ignored=sum(
            item.skipped_previously_rejected for item in pages
        ),
        transient_errors=sum(item.detail_failures for item in pages) + extra_transient,
        pending_after=pending_after,
        queue_cap_hit=pending_after >= PENDING_CAP_PER_FAMILY,
        failures=[failure for item in pages for failure in item.failures],
    )


def _attach_partial_report(exc, results, started_at):
    setattr(
        exc,
        "weekly_discovery_report",
        WeeklyDiscoveryReport(
            families=results,
            started_at=started_at,
            finished_at=timezone.now(),
        ),
    )


def run_weekly_discovery(*, client=None):
    """Run one bounded, sequential five-family discovery campaign."""
    client = client or AliExpressClient()
    started_at = timezone.now()
    families = []
    for order, slug in enumerate(WEEKLY_FAMILY_SLUGS):
        family = ProductFamily.objects.get(slug=slug)
        if family.status == ProductFamily.Status.RETIRED:
            raise ValueError(f"Operational weekly family is retired: {slug}")
        families.append((_pending_count(family), order, family))

    # Fairness: low/empty queues consume the weekly budget first.
    families.sort(key=lambda row: (row[0], row[1]))
    results = []

    for pending_before, _order, family in families:
        if pending_before >= PENDING_CAP_PER_FAMILY:
            results.append(
                WeeklyFamilyResult(
                    family_slug=family.slug,
                    pending_before=pending_before,
                    pending_after=pending_before,
                    queue_cap_hit=True,
                )
            )
            continue

        profile = get_family_profile(family.slug)
        keywords = tuple(profile.search_keywords if profile else ())
        if not keywords:
            results.append(
                WeeklyFamilyResult(
                    family_slug=family.slug,
                    pending_before=pending_before,
                    pending_after=pending_before,
                    transient_errors=1,
                    failures=["NO_SEARCH_KEYWORDS"],
                )
            )
            continue

        remaining_slots = PENDING_CAP_PER_FAMILY - pending_before
        max_detail_attempts = min(MAX_DETAIL_ATTEMPTS_PER_FAMILY, remaining_slots)
        max_details = min(MAX_DETAILS_PER_PAGE, remaining_slots)
        try:
            deep = discover_family_deep(
                family,
                keywords,
                max_pages=MAX_PAGES_PER_KEYWORD,
                limit=SEARCH_PAGE_SIZE,
                max_details=max_details,
                max_search_operations=MAX_SEARCH_OPERATIONS_PER_FAMILY,
                max_detail_attempts=max_detail_attempts,
                client=client,
            )
        except (
            AliExpressAuthenticationError,
            AliExpressConfigurationError,
            AliExpressRateLimitError,
            AliExpressRuntimeStateError,
        ) as exc:
            partial = getattr(exc, "deep_discovery_result", DeepDiscoveryResult())
            results.append(_aggregate_deep(family, pending_before, partial))
            _attach_partial_report(exc, results, started_at)
            raise
        except AliExpressError as exc:
            partial = getattr(exc, "deep_discovery_result", DeepDiscoveryResult())
            family_result = _aggregate_deep(
                family,
                pending_before,
                partial,
                extra_transient=1,
            )
            family_result.failures.append(exc.__class__.__name__)
            results.append(family_result)
            continue

        results.append(_aggregate_deep(family, pending_before, deep))

    by_slug = {item.family_slug: item for item in results}
    ordered = [by_slug[slug] for slug in WEEKLY_FAMILY_SLUGS]
    return WeeklyDiscoveryReport(
        families=ordered,
        started_at=started_at,
        finished_at=timezone.now(),
    )
