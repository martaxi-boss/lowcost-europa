from dataclasses import dataclass, field

from django.db import DatabaseError

from apps.catalog.services.aliexpress_persistence import import_aliexpress_product
from apps.integrations.aliexpress.client import AliExpressClient
from apps.integrations.aliexpress.exceptions import AliExpressError

DEFAULT_LIMIT = 10
MAX_LIMIT = 25
COUNTRY = "PT"
CURRENCY = "EUR"


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


@dataclass
class DiscoveryResult:
    keyword: str
    requested_limit: int
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
    errors: list[str] = field(default_factory=list)


def validate_limit(limit: int) -> int:
    if limit < 1 or limit > MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")
    return limit


def _record_metrics(metrics: DiscoveryMetrics, product) -> None:
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


def discover_aliexpress(
    keyword: str,
    limit: int = DEFAULT_LIMIT,
    *,
    client: AliExpressClient | None = None,
    dry_run: bool = False,
) -> DiscoveryResult:
    validate_limit(limit)
    keyword = keyword.strip()
    if not keyword:
        raise ValueError("keyword must not be blank")

    client = client or AliExpressClient()
    search = client.search_products_diagnostic(
        keyword, country=COUNTRY, currency=CURRENCY, page_no=1, page_size=limit
    )
    limited = search.products[:limit]
    result = DiscoveryResult(
        keyword=keyword,
        requested_limit=limit,
        search_results_received=len(limited) + search.invalid_items,
        invalid_ids=search.invalid_items,
    )

    unique_ids: list[str] = []
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
        unique_ids.append(product_id)
    result.unique_candidates = len(unique_ids)

    for product_id in unique_ids:
        result.attempted += 1
        try:
            persisted = import_aliexpress_product(
                product_id,
                COUNTRY,
                CURRENCY,
                client=client,
                dry_run=dry_run,
            )
        except AliExpressError as exc:
            result.failed += 1
            result.external_errors += 1
            result.errors.append(f"product {product_id}: {exc.__class__.__name__}")
            continue
        except DatabaseError as exc:
            result.failed += 1
            result.persistence_errors += 1
            result.errors.append(f"product {product_id}: {exc.__class__.__name__}")
            continue

        result.successful += 1
        result.observations_created += 1
        if persisted.offer_created:
            result.offers_created += 1
        else:
            result.offers_reused += 1
        _record_metrics(result.metrics, persisted.product)

    return result
