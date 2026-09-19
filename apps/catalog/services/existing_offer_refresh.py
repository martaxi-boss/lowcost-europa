from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Offer, OfferObservation
from apps.catalog.services.offer_maintenance import (
    is_factually_available,
    is_factually_unavailable,
)
from apps.integrations.aliexpress.client import AliExpressClient
from apps.integrations.aliexpress.exceptions import AliExpressResponseError
from apps.integrations.aliexpress.types import AliExpressProduct


@dataclass(frozen=True)
class ExistingOfferDetailObservationResult:
    offer_id: int
    product: AliExpressProduct
    observation: OfferObservation


@dataclass(frozen=True)
class ExistingOfferLogisticsObservationResult:
    offer_id: int
    status: str
    search_product: AliExpressProduct | None = None
    detail_product: AliExpressProduct | None = None
    observation: OfferObservation | None = None

    EXACT_PRODUCT_NOT_FOUND = "EXACT_PRODUCT_NOT_FOUND"
    OBSERVED = "OBSERVED"


def observe_existing_offer_detail(
    offer_id: int,
    *,
    country: str = "PT",
    currency: str = "EUR",
    client: AliExpressClient | None = None,
) -> ExistingOfferDetailObservationResult:
    offer = Offer.objects.get(pk=offer_id)
    expected_product_id = offer.external_product_id
    client = client or AliExpressClient()

    # Network/retry work happens before opening the database transaction.
    product = client.get_product_detail(expected_product_id, country, currency)
    if product.product_id != expected_product_id:
        raise AliExpressResponseError(
            "detail product_id does not match existing Offer external_product_id"
        )

    observed_at = timezone.now()
    with transaction.atomic():
        current_offer = Offer.objects.get(pk=offer_id)
        if current_offer.external_product_id != expected_product_id:
            raise AliExpressResponseError("existing Offer identity changed during detail refresh")
        observation = OfferObservation.objects.create(
            offer=current_offer,
            observed_at=observed_at,
            destination_country=product.destination_country,
            price=product.price,
            original_price=product.original_price,
            currency=product.currency,
            evaluation_rate_percent=product.evaluation_rate_percent,
            sales_count=product.sales_count,
            commission_rate=product.commission_rate,
            search_ship_to_days_raw=None,
            search_delivery_days=None,
            ship_to_days_raw=product.ship_to_days_raw,
            delivery_days=product.delivery_days,
            availability=OfferObservation.Availability.UNKNOWN,
        )

    return ExistingOfferDetailObservationResult(
        offer_id=current_offer.pk,
        product=product,
        observation=observation,
    )


def observe_existing_offer_logistics(
    offer: Offer,
    *,
    search_query: str,
    country: str = "PT",
    currency: str = "EUR",
    delivery_days: int = 5,
    client: AliExpressClient | None = None,
) -> ExistingOfferLogisticsObservationResult:
    """Observe an existing Offer with separate search/detail logistics provenance."""

    if not offer.pk:
        raise ValueError("offer must be a persisted Offer")
    if not search_query.strip():
        raise ValueError("search_query must not be blank")

    expected_product_id = offer.external_product_id
    client = client or AliExpressClient()

    # All external work happens before the database transaction.
    search_result = client.search_products_diagnostic(
        search_query,
        country=country,
        currency=currency,
        delivery_days=delivery_days,
    )
    search_product = next(
        (
            product
            for product in search_result.products
            if product.product_id == expected_product_id
        ),
        None,
    )
    if search_product is None:
        return ExistingOfferLogisticsObservationResult(
            offer_id=offer.pk,
            status=ExistingOfferLogisticsObservationResult.EXACT_PRODUCT_NOT_FOUND,
        )

    detail_product = client.get_product_detail(
        expected_product_id,
        country,
        currency,
    )
    if detail_product.product_id != expected_product_id:
        raise AliExpressResponseError(
            "detail product_id does not match existing Offer external_product_id"
        )

    if is_factually_unavailable(detail_product):
        availability = OfferObservation.Availability.UNAVAILABLE
    elif is_factually_available(detail_product):
        availability = OfferObservation.Availability.AVAILABLE
    else:
        availability = OfferObservation.Availability.UNKNOWN

    observed_at = timezone.now()
    with transaction.atomic():
        current_offer = Offer.objects.select_for_update().get(pk=offer.pk)
        if current_offer.external_product_id != expected_product_id:
            raise AliExpressResponseError(
                "existing Offer identity changed during logistics observation"
            )

        observation = OfferObservation.objects.create(
            offer=current_offer,
            observed_at=observed_at,
            destination_country=detail_product.destination_country,
            price=detail_product.price,
            original_price=detail_product.original_price,
            currency=detail_product.currency,
            evaluation_rate_percent=detail_product.evaluation_rate_percent,
            sales_count=detail_product.sales_count,
            commission_rate=detail_product.commission_rate,
            search_ship_to_days_raw=search_product.ship_to_days_raw,
            search_delivery_days=search_product.delivery_days,
            ship_to_days_raw=detail_product.ship_to_days_raw,
            delivery_days=detail_product.delivery_days,
            availability=availability,
        )

    return ExistingOfferLogisticsObservationResult(
        offer_id=current_offer.pk,
        status=ExistingOfferLogisticsObservationResult.OBSERVED,
        search_product=search_product,
        detail_product=detail_product,
        observation=observation,
    )
