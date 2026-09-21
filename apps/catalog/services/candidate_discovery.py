from dataclasses import dataclass, field

from django.utils import timezone

from apps.catalog.models import Offer, OfferCandidate, ProductFamily
from apps.catalog.services.candidate_learning import family_learning_snapshot
from apps.catalog.services.candidate_priority import (
    priority_for_family,
)
from apps.catalog.services.candidate_relevance import family_candidate_relevance
from apps.catalog.services.family_profiles import get_family_profile
from apps.catalog.services.shipping_qualification import is_factually_not_shippable_to_pt
from apps.integrations.aliexpress.client import AliExpressClient
from apps.integrations.aliexpress.exceptions import AliExpressError, AliExpressRateLimitError


@dataclass
class CandidateDiscoveryResult:
    search_results: int = 0
    shortlisted: int = 0
    detailed: int = 0
    detail_attempts: int = 0
    detail_failures: int = 0
    created: int = 0
    updated: int = 0
    skipped_irrelevant_family: int = 0
    skipped_accessory_part: int = 0
    skipped_existing_offer: int = 0
    skipped_existing_candidate: int = 0
    skipped_previously_rejected: int = 0
    skipped_known_other_family: int = 0
    skipped_not_shippable_to_pt: int = 0
    failures: list[str] = field(default_factory=list)
    raw_product_ids: set[str] = field(default_factory=set)
    current_page_no: int | None = None
    current_record_count: int | None = None
    total_page_no: int | None = None
    total_record_count: int | None = None


def _learning_inputs(family):
    profile = get_family_profile(family.slug)
    learning = family_learning_snapshot(family)
    return profile, learning.learned_variants, learning.semantic_negative_titles


def _family_move_positive_titles(family):
    return family_learning_snapshot(family).classification_positive_titles


def _count_irrelevant(result, reason):
    if reason == "ACCESSORY_OR_PART":
        result.skipped_accessory_part += 1
    else:
        result.skipped_irrelevant_family += 1


def discover_family_candidates(
    family, keyword, *, page_no=1, limit=10, max_details=10, client=None
):
    if not isinstance(family, ProductFamily):
        raise TypeError("family must be ProductFamily")
    if family.status == ProductFamily.Status.RETIRED:
        raise ValueError("Retired family cannot receive discovery")
    if page_no < 1:
        raise ValueError("page_no must be at least 1")
    if not 1 <= limit <= 25:
        raise ValueError("limit must be between 1 and 25")
    if not 0 <= max_details <= 10:
        raise ValueError("max_details must be between 0 and 10")
    client = client or AliExpressClient()
    result = CandidateDiscoveryResult()
    search = client.search_products_diagnostic(
        keyword,
        country="PT",
        currency="EUR",
        page_no=page_no,
        page_size=limit,
        target_language="EN",
    )
    products = search.products[:limit]
    result.search_results = len(products) + search.invalid_items
    result.raw_product_ids = {product.product_id for product in products if product.product_id}
    result.current_page_no = search.current_page_no
    result.current_record_count = search.current_record_count
    result.total_page_no = search.total_page_no
    result.total_record_count = search.total_record_count
    seen = set()
    shortlist = []
    for product in products:
        pid = product.product_id
        if not pid or pid in seen:
            continue
        seen.add(pid)
        relevant, reason = family_candidate_relevance(family.slug, product.title)
        if not relevant:
            _count_irrelevant(result, reason)
            continue
        if is_factually_not_shippable_to_pt(product):
            result.skipped_not_shippable_to_pt += 1
            continue
        if Offer.objects.filter(source=Offer.Source.ALIEXPRESS, external_product_id=pid).exists():
            result.skipped_existing_offer += 1
            continue
        existing = (
            OfferCandidate.objects.filter(
                source=Offer.Source.ALIEXPRESS,
                external_product_id=pid,
            )
            .only("status", "product_family_id")
            .first()
        )
        if existing:
            if existing.status == OfferCandidate.Status.REJECTED:
                result.skipped_previously_rejected += 1
            elif existing.product_family_id != family.pk:
                result.skipped_known_other_family += 1
            else:
                result.skipped_existing_candidate += 1
            continue
        shortlist.append(product)

    profile = get_family_profile(family.slug)
    learning = family_learning_snapshot(family)
    if profile:
        shortlist.sort(
            key=lambda product: priority_for_family(
                product,
                family.slug,
                learned_variants=learning.learned_variants,
                semantic_negative_titles=learning.semantic_negative_titles,
                accessory_negative_titles=learning.accessory_negative_titles,
                classification_negative_titles=learning.classification_negative_titles,
                quality_negative_titles=learning.quality_negative_titles,
                classification_positive_titles=learning.classification_positive_titles,
            )[0],
            reverse=True,
        )
    shortlist = shortlist[:max_details]
    result.shortlisted = len(shortlist)

    for search_product in shortlist:
        result.detail_attempts += 1
        try:
            detail = client.get_product_detail(search_product.product_id, "PT", "EUR")
        except AliExpressRateLimitError:
            raise
        except AliExpressError as exc:
            result.detail_failures += 1
            result.failures.append(f"{search_product.product_id}:{exc.__class__.__name__}")
            continue
        if detail.product_id != search_product.product_id:
            raise ValueError("AliExpress detail product ID mismatch")
        result.detailed += 1
        if is_factually_not_shippable_to_pt(detail):
            result.skipped_not_shippable_to_pt += 1
            continue
        relevant, reason = family_candidate_relevance(
            family.slug, detail.title or search_product.title
        )
        if not relevant:
            _count_irrelevant(result, reason)
            continue

        now = timezone.now()
        defaults = {
            "product_family": family,
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
            source=Offer.Source.ALIEXPRESS,
            external_product_id=detail.product_id,
            defaults={**defaults, "discovered_at": now},
        )
        if created:
            result.created += 1
        else:
            if candidate.status == OfferCandidate.Status.REJECTED:
                result.skipped_previously_rejected += 1
            elif candidate.product_family_id != family.pk:
                result.skipped_known_other_family += 1
            else:
                result.skipped_existing_candidate += 1
    return result


def seed_candidates_from_existing_offers(family):
    created = 0
    for placement in family.offer_placements.select_related("offer").prefetch_related(
        "offer__observations"
    ):
        offer = placement.offer
        latest = offer.observations.order_by("-observed_at", "-pk").first()
        defaults = {
            "product_family": family,
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
        candidate, was_created = OfferCandidate.objects.get_or_create(
            source=offer.source,
            external_product_id=offer.external_product_id,
            defaults=defaults,
        )
        if not was_created and candidate.product_family_id != family.pk:
            continue
        created += int(was_created)
    return created
