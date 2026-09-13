from dataclasses import dataclass, field
from datetime import datetime, timedelta

from django.db import DatabaseError
from django.utils import timezone

from apps.catalog.services.aliexpress_persistence import import_aliexpress_product
from apps.catalog.services.logistics_evidence import assess_logistics_evidence
from apps.catalog.services.logistics_freshness import assess_logistics_freshness
from apps.integrations.aliexpress.client import AliExpressClient
from apps.integrations.aliexpress.exceptions import AliExpressError

COUNTRY = "PT"
CURRENCY = "EUR"
TARGET_LANGUAGE = "EN"
DELIVERY_DAYS = 5
SEARCH_LIMIT = 10
MAX_COHORT_SIZE = 3
FRESHNESS_MAX_AGE = timedelta(hours=24)


@dataclass(frozen=True)
class CohortObservationCandidate:
    product_id: str
    title: str | None
    outcome: str
    search_delivery_days: int | None = None
    detail_delivery_days: int | None = None
    evidence_state: str | None = None
    freshness_state: str | None = None
    supports_5d: bool | None = None
    supports_current_5d: bool | None = None
    price: object | None = None
    currency: str | None = None
    commission_rate: object | None = None
    observed_at: datetime | None = None
    offer_created: bool | None = None


@dataclass
class CohortObservationResult:
    keyword: str
    requested_ids: list[str]
    product_ids: list[str]
    duplicate_ids: int
    commit: bool
    successful: int = 0
    failed: int = 0
    offers_created: int = 0
    offers_reused: int = 0
    observations_created: int = 0
    candidates: list[CohortObservationCandidate] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    diagnostic_as_of: datetime | None = None


def normalize_product_ids(product_ids: list[str]) -> tuple[list[str], int]:
    if not product_ids:
        raise ValueError("at least one product_id is required")
    if len(product_ids) > MAX_COHORT_SIZE:
        raise ValueError(f"no more than {MAX_COHORT_SIZE} product IDs are allowed")
    cleaned: list[str] = []
    seen: set[str] = set()
    duplicates = 0
    for raw in product_ids:
        product_id = raw.strip()
        if not product_id:
            raise ValueError("product_id must not be blank")
        if product_id in seen:
            duplicates += 1
            continue
        seen.add(product_id)
        cleaned.append(product_id)
    return cleaned, duplicates


def observe_aliexpress_products(
    product_ids: list[str],
    *,
    keyword: str = "HIFU machine",
    commit: bool = False,
    client: AliExpressClient | None = None,
) -> CohortObservationResult:
    normalized_ids, duplicates = normalize_product_ids(product_ids)
    keyword = keyword.strip()
    if not keyword:
        raise ValueError("keyword must not be blank")

    client = client or AliExpressClient()
    search = client.search_products_diagnostic(
        keyword,
        country=COUNTRY,
        currency=CURRENCY,
        page_no=1,
        page_size=SEARCH_LIMIT,
        target_language=TARGET_LANGUAGE,
        delivery_days=DELIVERY_DAYS,
    )
    search_by_id = {product.product_id: product for product in search.products}
    result = CohortObservationResult(
        keyword=keyword,
        requested_ids=list(product_ids),
        product_ids=normalized_ids,
        duplicate_ids=duplicates,
        commit=commit,
    )

    staged: list[tuple[CohortObservationCandidate, object]] = []
    for product_id in normalized_ids:
        search_product = search_by_id.get(product_id)
        if search_product is None:
            result.failed += 1
            result.errors.append(f"product {product_id}: search context not found")
            result.candidates.append(
                CohortObservationCandidate(
                    product_id=product_id,
                    title=None,
                    outcome="search_context_missing",
                )
            )
            continue
        try:
            persisted = import_aliexpress_product(
                product_id,
                COUNTRY,
                CURRENCY,
                client=client,
                dry_run=not commit,
                search_product=search_product,
            )
        except AliExpressError as exc:
            result.failed += 1
            result.errors.append(f"product {product_id}: {exc.__class__.__name__}")
            result.candidates.append(
                CohortObservationCandidate(
                    product_id=product_id,
                    title=search_product.title,
                    outcome="external_error",
                    search_delivery_days=search_product.delivery_days,
                )
            )
            continue
        except DatabaseError as exc:
            result.failed += 1
            result.errors.append(f"product {product_id}: {exc.__class__.__name__}")
            result.candidates.append(
                CohortObservationCandidate(
                    product_id=product_id,
                    title=search_product.title,
                    outcome="persistence_error",
                    search_delivery_days=search_product.delivery_days,
                )
            )
            continue
        evidence = assess_logistics_evidence(
            search_delivery_days=search_product.delivery_days,
            detail_delivery_days=persisted.product.delivery_days,
        )
        result.successful += 1
        result.observations_created += 1
        if persisted.offer_created:
            result.offers_created += 1
        else:
            result.offers_reused += 1
        candidate = CohortObservationCandidate(
            product_id=product_id,
            title=persisted.product.title or search_product.title,
            outcome="success",
            search_delivery_days=search_product.delivery_days,
            detail_delivery_days=persisted.product.delivery_days,
            evidence_state=evidence.state.value,
            supports_5d=evidence.supports_within_5_days,
            price=persisted.product.price,
            currency=persisted.product.currency,
            commission_rate=persisted.product.commission_rate,
            observed_at=persisted.observation.observed_at,
            offer_created=persisted.offer_created,
        )
        staged.append((candidate, evidence))

    as_of = timezone.now()
    result.diagnostic_as_of = as_of
    for candidate, evidence in staged:
        freshness = assess_logistics_freshness(
            observed_at=candidate.observed_at,
            as_of=as_of,
            max_age=FRESHNESS_MAX_AGE,
        )
        enriched = CohortObservationCandidate(
            **{
                **candidate.__dict__,
                "freshness_state": freshness.state.value,
                "supports_current_5d": bool(
                    evidence.supports_within_5_days and freshness.is_fresh
                ),
            }
        )
        result.candidates.append(enriched)
    return result
