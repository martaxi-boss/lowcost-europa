from dataclasses import dataclass, field

from django.utils import timezone

from apps.catalog.models import Offer, OfferCandidate, ProductFamily
from apps.catalog.services.candidate_relevance import is_family_candidate_relevant
from apps.integrations.aliexpress.client import AliExpressClient
from apps.integrations.aliexpress.exceptions import AliExpressError, AliExpressRateLimitError


@dataclass
class CandidateDiscoveryResult:
    search_results: int = 0
    shortlisted: int = 0
    detailed: int = 0
    created: int = 0
    updated: int = 0
    skipped_existing_offer: int = 0
    skipped_existing_candidate: int = 0
    failures: list[str] = field(default_factory=list)


def discover_family_candidates(family, keyword, *, limit=10, max_details=10, client=None):
    if not isinstance(family, ProductFamily):
        raise TypeError("family must be ProductFamily")
    if not 1 <= limit <= 15:
        raise ValueError("limit must be between 1 and 15")
    if not 0 <= max_details <= 10:
        raise ValueError("max_details must be between 0 and 10")
    client = client or AliExpressClient()
    result = CandidateDiscoveryResult()
    search = client.search_products_diagnostic(
        keyword, country="PT", currency="EUR", page_no=1, page_size=limit, target_language="EN"
    )
    products = search.products[:limit]
    result.search_results = len(products) + search.invalid_items
    seen = set()
    shortlist = []
    for product in products:
        pid = product.product_id
        if not pid or pid in seen:
            continue
        if not is_family_candidate_relevant(family.slug, product.title):
            continue
        seen.add(pid)
        if Offer.objects.filter(source=Offer.Source.ALIEXPRESS, external_product_id=pid).exists():
            result.skipped_existing_offer += 1
            continue
        if OfferCandidate.objects.filter(
            product_family=family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id=pid,
        ).exists():
            result.skipped_existing_candidate += 1
            continue
        shortlist.append(product)
    shortlist = shortlist[:max_details]
    result.shortlisted = len(shortlist)
    for search_product in shortlist:
        try:
            detail = client.get_product_detail(search_product.product_id, "PT", "EUR")
        except AliExpressRateLimitError:
            raise
        except AliExpressError as exc:
            result.failures.append(f"{search_product.product_id}:{exc.__class__.__name__}")
            continue
        if detail.product_id != search_product.product_id:
            raise ValueError("AliExpress detail product ID mismatch")
        result.detailed += 1
        now = timezone.now()
        defaults = {
            "title": detail.title or search_product.title or "",
            "image_url": detail.image_url or search_product.image_url or "",
            "product_url": detail.product_url or search_product.product_url or "",
            "price": detail.price,
            "original_price": detail.original_price,
            "currency": detail.currency,
            "evaluation_rate_percent": detail.evaluation_rate_percent,
            "sales_count": detail.sales_count,
            "commission_rate": detail.commission_rate,
            "search_ship_to_days_raw": search_product.ship_to_days_raw,
            "search_delivery_days": search_product.delivery_days,
            "detail_ship_to_days_raw": detail.ship_to_days_raw,
            "detail_delivery_days": detail.delivery_days,
            "last_observed_at": now,
        }
        candidate, created = OfferCandidate.objects.get_or_create(
            product_family=family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id=detail.product_id,
            defaults={**defaults, "discovered_at": now},
        )
        if created:
            result.created += 1
        else:
            for key, value in defaults.items():
                setattr(candidate, key, value)
            candidate.save(update_fields=[*defaults.keys(), "updated_at"])
            result.updated += 1
    return result


def seed_candidates_from_existing_offers(family):
    created = 0
    for placement in family.offer_placements.select_related("offer").prefetch_related(
        "offer__observations"
    ):
        offer = placement.offer
        latest = offer.observations.order_by("-observed_at", "-pk").first()
        defaults = {
            "title": offer.title,
            "image_url": offer.image_url,
            "product_url": offer.product_url,
            "price": latest.price if latest else None,
            "original_price": latest.original_price if latest else None,
            "currency": latest.currency if latest else None,
            "evaluation_rate_percent": latest.evaluation_rate_percent if latest else None,
            "sales_count": latest.sales_count if latest else None,
            "commission_rate": latest.commission_rate if latest else None,
            "search_ship_to_days_raw": latest.search_ship_to_days_raw if latest else None,
            "search_delivery_days": latest.search_delivery_days if latest else None,
            "detail_ship_to_days_raw": latest.ship_to_days_raw if latest else None,
            "detail_delivery_days": latest.delivery_days if latest else None,
            "last_observed_at": latest.observed_at if latest else offer.last_seen_at,
            "approved_offer": offer,
        }
        _, was_created = OfferCandidate.objects.get_or_create(
            product_family=family,
            source=offer.source,
            external_product_id=offer.external_product_id,
            defaults=defaults,
        )
        created += int(was_created)
    return created
