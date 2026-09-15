from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Offer, OfferObservation
from apps.integrations.aliexpress.client import AliExpressClient
from apps.integrations.aliexpress.exceptions import AliExpressResponseError
from apps.integrations.aliexpress.types import AliExpressProduct


@dataclass(frozen=True)
class ExistingOfferDetailObservationResult:
    offer_id: int
    product: AliExpressProduct
    observation: OfferObservation


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
