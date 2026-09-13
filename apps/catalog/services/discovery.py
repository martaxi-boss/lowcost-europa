from dataclasses import dataclass, field
from decimal import Decimal

from django.db import DatabaseError

from apps.catalog.services.aliexpress_persistence import import_aliexpress_product
from apps.integrations.aliexpress.client import SUPPORTED_DELIVERY_DAYS, AliExpressClient
from apps.integrations.aliexpress.exceptions import AliExpressError
from apps.integrations.aliexpress.types import AliExpressProduct

DEFAULT_LIMIT = 10
MAX_LIMIT = 25
COUNTRY = "PT"
CURRENCY = "EUR"
SUPPORTED_TARGET_LANGUAGES = frozenset({"EN", "PT"})


@dataclass
class DiscoveryMetrics:
    price_present: int = 0
    price_missing: int = 0
    currency_present: int = 0
    currency_missing: int = 0
    evaluation_rate_present: int = 0
    evaluation_rate_missing: int = 0
    sales_count_present: int = 0
    sales_count_missing: int = 0
    commission_rate_present: int = 0
    commission_rate_missing: int = 0
    shipping_raw_present: int = 0
    shipping_raw_missing: int = 0
    delivery_days_present: int = 0
    delivery_days_missing: int = 0
    delivery_within_5_days: int = 0
    delivery_over_5_days: int = 0
    search_shipping_raw_present: int = 0
    search_shipping_raw_missing: int = 0
    search_delivery_days_present: int = 0
    search_delivery_days_missing: int = 0
    search_delivery_within_5_days: int = 0
    search_delivery_over_5_days: int = 0
    delivery_search_detail_mismatch: int = 0


@dataclass(frozen=True)
class DiscoveryCandidate:
    product_id: str
    title: str | None
    price: Decimal | None
    currency: str | None
    evaluation_rate_percent: Decimal | None
    sales_count: int | None
    commission_rate: Decimal | None
    search_ship_to_days_raw: str | None
    search_delivery_days: int | None
    detail_ship_to_days_raw: str | None
    detail_delivery_days: int | None
    observation_search_delivery_days: int | None
    observation_detail_delivery_days: int | None
    outcome: str


@dataclass
class DiscoveryResult:
    keyword: str
    requested_limit: int
    target_language: str | None = None
    delivery_days_filter: int | None = None
    search_results_received: int = 0
    unique_candidates: int = 0
    duplicates_in_batch: int = 0
    invalid_ids: int = 0
    attempted: int = 0
    successful: int = 0
    failed: int = 0
    offers_created: int = 0
    offers_reused: int = 0
    observations_created: int = 0
    external_errors: int = 0
    persistence_errors: int = 0
    metrics: DiscoveryMetrics = field(default_factory=DiscoveryMetrics)
    candidates: list[DiscoveryCandidate] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def validate_limit(limit: int) -> int:
    if limit < 1 or limit > MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")
    return limit


def validate_target_language(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.upper()
    if normalized not in SUPPORTED_TARGET_LANGUAGES:
        allowed = ", ".join(sorted(SUPPORTED_TARGET_LANGUAGES))
        raise ValueError(f"target_language must be one of: {allowed}")
    return normalized


def validate_delivery_days(value: int | None) -> int | None:
    if value is None:
        return None
    if value not in SUPPORTED_DELIVERY_DAYS:
        allowed = ", ".join(str(item) for item in sorted(SUPPORTED_DELIVERY_DAYS))
        raise ValueError(f"delivery_days must be one of: {allowed}")
    return value


def _record_detail_metrics(metrics: DiscoveryMetrics, product: AliExpressProduct) -> None:
    fields = [
        ("price", "price_present", "price_missing"),
        ("currency", "currency_present", "currency_missing"),
        ("evaluation_rate_percent", "evaluation_rate_present", "evaluation_rate_missing"),
        ("sales_count", "sales_count_present", "sales_count_missing"),
        ("commission_rate", "commission_rate_present", "commission_rate_missing"),
        ("ship_to_days_raw", "shipping_raw_present", "shipping_raw_missing"),
        ("delivery_days", "delivery_days_present", "delivery_days_missing"),
    ]
    for attr, present, missing in fields:
        target = present if getattr(product, attr) is not None else missing
        setattr(metrics, target, getattr(metrics, target) + 1)
    if product.delivery_days is not None:
        target = "delivery_within_5_days" if product.delivery_days <= 5 else "delivery_over_5_days"
        setattr(metrics, target, getattr(metrics, target) + 1)


def _record_search_metrics(metrics: DiscoveryMetrics, product: AliExpressProduct) -> None:
    if product.ship_to_days_raw is None:
        metrics.search_shipping_raw_missing += 1
    else:
        metrics.search_shipping_raw_present += 1
    if product.delivery_days is None:
        metrics.search_delivery_days_missing += 1
    else:
        metrics.search_delivery_days_present += 1
        if product.delivery_days <= 5:
            metrics.search_delivery_within_5_days += 1
        else:
            metrics.search_delivery_over_5_days += 1


def _candidate_record(
    search_product: AliExpressProduct,
    detail_product: AliExpressProduct | None,
    outcome: str,
    *,
    observation=None,
) -> DiscoveryCandidate:
    return DiscoveryCandidate(
        product_id=search_product.product_id,
        title=search_product.title,
        price=search_product.price,
        currency=search_product.currency,
        evaluation_rate_percent=search_product.evaluation_rate_percent,
        sales_count=search_product.sales_count,
        commission_rate=search_product.commission_rate,
        search_ship_to_days_raw=search_product.ship_to_days_raw,
        search_delivery_days=search_product.delivery_days,
        detail_ship_to_days_raw=(detail_product.ship_to_days_raw if detail_product else None),
        detail_delivery_days=(detail_product.delivery_days if detail_product else None),
        observation_search_delivery_days=(
            observation.search_delivery_days if observation is not None else None
        ),
        observation_detail_delivery_days=(
            observation.delivery_days if observation is not None else None
        ),
        outcome=outcome,
    )


def discover_aliexpress(
    keyword: str,
    limit: int = DEFAULT_LIMIT,
    *,
    target_language: str | None = None,
    delivery_days: int | None = None,
    client: AliExpressClient | None = None,
    dry_run: bool = False,
) -> DiscoveryResult:
    validate_limit(limit)
    target_language = validate_target_language(target_language)
    delivery_days = validate_delivery_days(delivery_days)
    keyword = keyword.strip()
    if not keyword:
        raise ValueError("keyword must not be blank")

    client = client or AliExpressClient()
    search = client.search_products_diagnostic(
        keyword,
        country=COUNTRY,
        currency=CURRENCY,
        page_no=1,
        page_size=limit,
        target_language=target_language,
        delivery_days=delivery_days,
    )
    limited = search.products[:limit]
    result = DiscoveryResult(
        keyword=keyword,
        requested_limit=limit,
        target_language=target_language,
        delivery_days_filter=delivery_days,
        search_results_received=len(limited) + search.invalid_items,
        invalid_ids=search.invalid_items,
    )

    candidates: list[AliExpressProduct] = []
    seen: set[str] = set()
    for product in limited:
        product_id = (product.product_id or "").strip()
        if not product_id:
            result.invalid_ids += 1
            continue
        if product_id in seen:
            result.duplicates_in_batch += 1
            continue
        seen.add(product_id)
        candidates.append(product)
        _record_search_metrics(result.metrics, product)
    result.unique_candidates = len(candidates)

    for search_product in candidates:
        product_id = search_product.product_id
        result.attempted += 1
        try:
            persisted = import_aliexpress_product(
                product_id,
                COUNTRY,
                CURRENCY,
                client=client,
                dry_run=dry_run,
                search_product=search_product,
            )
        except AliExpressError as exc:
            result.failed += 1
            result.external_errors += 1
            result.errors.append(f"product {product_id}: {exc.__class__.__name__}")
            result.candidates.append(_candidate_record(search_product, None, "external_error"))
            continue
        except DatabaseError as exc:
            result.failed += 1
            result.persistence_errors += 1
            result.errors.append(f"product {product_id}: {exc.__class__.__name__}")
            result.candidates.append(_candidate_record(search_product, None, "persistence_error"))
            continue

        detail_product = persisted.product
        result.successful += 1
        result.observations_created += 1
        if persisted.offer_created:
            result.offers_created += 1
        else:
            result.offers_reused += 1
        _record_detail_metrics(result.metrics, detail_product)
        if search_product.delivery_days != detail_product.delivery_days:
            result.metrics.delivery_search_detail_mismatch += 1
        result.candidates.append(
            _candidate_record(
                search_product, detail_product, "success", observation=persisted.observation
            )
        )

    return result
