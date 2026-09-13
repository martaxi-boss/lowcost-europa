from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Offer, OfferObservation
from apps.integrations.aliexpress.client import AliExpressClient
from apps.integrations.aliexpress.types import AliExpressProduct


@dataclass(frozen=True)
class PersistenceResult:
    product: AliExpressProduct
    offer: Offer
    observation: OfferObservation
    offer_created: bool
    dry_run: bool


def import_aliexpress_product(
    product_id: str,
    country: str = "PT",
    currency: str = "EUR",
    *,
    client: AliExpressClient | None = None,
    dry_run: bool = False,
) -> PersistenceResult:
    client = client or AliExpressClient()

    # All network work happens before opening the database transaction.
    product = client.get_product_detail(product_id, country, currency)
    affiliate_url = product.affiliate_url
    if product.product_url:
        affiliate_url = client.generate_affiliate_link(product.product_url)

    observed_at = timezone.now()

    with transaction.atomic():
        offer, created = Offer.objects.get_or_create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id=product.product_id,
            defaults={
                "first_seen_at": observed_at,
                "last_seen_at": observed_at,
                "title": product.title or "",
                "product_url": product.product_url or "",
                "image_url": product.image_url or "",
                "affiliate_url": affiliate_url or "",
                "is_active": True,
            },
        )

        if not created:
            offer.last_seen_at = observed_at
            offer.is_active = True
            if product.title:
                offer.title = product.title
            if product.product_url:
                offer.product_url = product.product_url
            if product.image_url:
                offer.image_url = product.image_url
            if affiliate_url:
                offer.affiliate_url = affiliate_url
            offer.save(
                update_fields=[
                    "last_seen_at",
                    "is_active",
                    "title",
                    "product_url",
                    "image_url",
                    "affiliate_url",
                    "updated_at",
                ]
            )

        observation = OfferObservation.objects.create(
            offer=offer,
            observed_at=observed_at,
            destination_country=product.destination_country,
            price=product.price,
            original_price=product.original_price,
            currency=product.currency,
            evaluation_rate_percent=product.evaluation_rate_percent,
            sales_count=product.sales_count,
            commission_rate=product.commission_rate,
            ship_to_days_raw=product.ship_to_days_raw,
            delivery_days=product.delivery_days,
            availability=OfferObservation.Availability.UNKNOWN,
        )

        result = PersistenceResult(
            product=product,
            offer=offer,
            observation=observation,
            offer_created=created,
            dry_run=dry_run,
        )
        if dry_run:
            transaction.set_rollback(True)
        return result
