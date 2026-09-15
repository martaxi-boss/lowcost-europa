from decimal import Decimal

from django.test import TransactionTestCase

from apps.catalog.models import Offer, OfferObservation, ProductFamily
from apps.catalog.services.existing_offer_refresh import observe_existing_offer_detail
from apps.integrations.aliexpress.exceptions import AliExpressAPIError, AliExpressResponseError
from apps.integrations.aliexpress.types import AliExpressProduct


class FakeDetailClient:
    def __init__(self, product=None, error=None):
        self.product = product
        self.error = error
        self.detail_calls = []
        self.link_calls = []

    def get_product_detail(self, product_id, country, currency):
        self.detail_calls.append((product_id, country, currency))
        if self.error:
            raise self.error
        return self.product

    def generate_affiliate_link(self, source_url):
        self.link_calls.append(source_url)
        raise AssertionError("affiliate link generation must not be called")


def detail_product(product_id="100", **overrides):
    values = {
        "product_id": product_id,
        "title": "Fresh title must not overwrite Offer",
        "image_url": "https://images.example/fresh.jpg",
        "product_url": "https://source.example/fresh",
        "price": Decimal("101.10"),
        "currency": "EUR",
        "original_price": Decimal("120.00"),
        "evaluation_rate_percent": Decimal("97.0"),
        "sales_count": 4,
        "commission_rate": Decimal("7.0"),
        "ship_to_days_raw": None,
        "delivery_days": None,
        "destination_country": "PT",
        "affiliate_url": "https://affiliate.example/fresh",
    }
    values.update(overrides)
    return AliExpressProduct(**values)


class ExistingOfferDetailRefreshTests(TransactionTestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(name="Diode", slug="diode")
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="100",
            product_family=self.family,
            title="Stored title",
            product_url="https://stored.example/product",
            image_url="https://stored.example/image.jpg",
            affiliate_url="https://stored.example/affiliate",
            is_active=True,
            is_primary=True,
        )
        OfferObservation.objects.create(
            offer=self.offer,
            price=Decimal("99.00"),
            currency="EUR",
            availability=OfferObservation.Availability.UNKNOWN,
        )

    def test_detail_only_refresh_creates_one_observation_and_preserves_offer(self):
        client = FakeDetailClient(product=detail_product())
        result = observe_existing_offer_detail(self.offer.pk, client=client)
        self.assertEqual(result.product.product_id, "100")
        self.assertEqual(client.detail_calls, [("100", "PT", "EUR")])
        self.assertEqual(client.link_calls, [])
        self.assertEqual(OfferObservation.objects.filter(offer=self.offer).count(), 2)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.title, "Stored title")
        self.assertEqual(self.offer.product_url, "https://stored.example/product")
        self.assertEqual(self.offer.image_url, "https://stored.example/image.jpg")
        self.assertEqual(self.offer.affiliate_url, "https://stored.example/affiliate")
        self.assertTrue(self.offer.is_active)
        self.assertTrue(self.offer.is_primary)
        self.assertEqual(self.offer.product_family, self.family)

    def test_detail_failure_preserves_last_known_good_and_creates_zero_observation(self):
        client = FakeDetailClient(error=AliExpressAPIError("external failure"))
        before = OfferObservation.objects.filter(offer=self.offer).count()
        with self.assertRaises(AliExpressAPIError):
            observe_existing_offer_detail(self.offer.pk, client=client)
        self.assertEqual(OfferObservation.objects.filter(offer=self.offer).count(), before)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.affiliate_url, "https://stored.example/affiliate")

    def test_product_id_mismatch_creates_zero_observation(self):
        client = FakeDetailClient(product=detail_product("DIFFERENT"))
        before = OfferObservation.objects.filter(offer=self.offer).count()
        with self.assertRaises(AliExpressResponseError):
            observe_existing_offer_detail(self.offer.pk, client=client)
        self.assertEqual(OfferObservation.objects.filter(offer=self.offer).count(), before)
