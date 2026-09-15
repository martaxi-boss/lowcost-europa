from django.test import TestCase

from apps.catalog.models import Offer, OfferObservation, ProductFamily
from apps.catalog.services.aliexpress_persistence import import_aliexpress_product
from apps.integrations.aliexpress.exceptions import AliExpressTransportError


class FailingClient:
    def get_product_detail(self, *_args, **_kwargs):
        raise AliExpressTransportError("AliExpress transport error")


class LastKnownGoodTests(TestCase):
    def test_refresh_failure_preserves_offer_and_observation(self):
        family = ProductFamily.objects.create(name="HIFU", slug="hifu")
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="42",
            product_family=family,
            title="Known title",
            image_url="https://example.test/known.jpg",
            affiliate_url="https://example.test/known-affiliate",
            is_active=True,
            is_primary=True,
        )
        OfferObservation.objects.create(
            offer=offer,
            destination_country="PT",
            price="100.00",
            currency="EUR",
            sales_count=12,
            commission_rate="7.0",
            search_delivery_days=5,
        )
        before_offer = {
            "title": offer.title,
            "image_url": offer.image_url,
            "affiliate_url": offer.affiliate_url,
            "is_active": offer.is_active,
            "is_primary": offer.is_primary,
        }
        before_count = OfferObservation.objects.filter(offer=offer).count()

        with self.assertRaises(AliExpressTransportError):
            import_aliexpress_product("42", client=FailingClient())

        offer.refresh_from_db()
        self.assertEqual(
            {
                "title": offer.title,
                "image_url": offer.image_url,
                "affiliate_url": offer.affiliate_url,
                "is_active": offer.is_active,
                "is_primary": offer.is_primary,
            },
            before_offer,
        )
        self.assertEqual(OfferObservation.objects.filter(offer=offer).count(), before_count)
