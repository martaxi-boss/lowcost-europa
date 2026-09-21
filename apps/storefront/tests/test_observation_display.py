from datetime import timedelta
from decimal import Decimal

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Offer, OfferFamilyPlacement, OfferObservation, ProductFamily


class ObservationFallbackDisplayTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(
            name="Observation Family",
            slug="observation-family",
        )

    def make_offer(self, external_id="obs-offer", **overrides):
        now = timezone.now()
        values = {
            "source": Offer.Source.ALIEXPRESS,
            "external_product_id": external_id,
            "title": f"Offer {external_id}",
            "affiliate_url": f"https://affiliate.example/{external_id}",
            "affiliate_promotion_status": Offer.AffiliatePromotionStatus.ELIGIBLE,
            "affiliate_promotion_verified_at": now,
            "protocol_verified_at": now,
            "is_active": True,
            "owner_hidden": False,
        }
        values.update(overrides)
        offer = Offer.objects.create(**values)
        OfferFamilyPlacement.objects.create(offer=offer, product_family=self.family)
        return offer

    def detail(self):
        return self.client.get(
            reverse(
                "storefront:product-family-detail",
                kwargs={"slug": self.family.slug},
            )
        )

    def test_latest_unknown_falls_back_field_by_field(self):
        offer = self.make_offer()
        now = timezone.now()
        OfferObservation.objects.create(
            offer=offer,
            price=Decimal("570.00"),
            currency="EUR",
            evaluation_rate_percent=Decimal("100.00"),
            sales_count=6,
            observed_at=now - timedelta(hours=1),
        )
        OfferObservation.objects.create(
            offer=offer,
            availability=OfferObservation.Availability.UNKNOWN,
            observed_at=now,
        )

        response = self.detail()

        self.assertContains(response, "570,00 EUR")
        self.assertContains(response, "100,00%")
        self.assertContains(response, ">6<", html=False)

    def test_latest_partial_uses_each_fields_latest_valid_source(self):
        offer = self.make_offer()
        now = timezone.now()
        OfferObservation.objects.create(
            offer=offer,
            price=Decimal("500.00"),
            currency="EUR",
            evaluation_rate_percent=Decimal("95.00"),
            sales_count=10,
            observed_at=now - timedelta(hours=1),
        )
        OfferObservation.objects.create(
            offer=offer,
            price=Decimal("450.00"),
            currency="EUR",
            sales_count=12,
            observed_at=now,
        )

        response = self.detail()

        self.assertContains(response, "450,00 EUR")
        self.assertContains(response, "95,00%")
        self.assertContains(response, ">12<", html=False)
        self.assertNotContains(response, "500,00 EUR")

    def test_without_historical_price_renders_not_available(self):
        offer = self.make_offer()
        OfferObservation.objects.create(
            offer=offer,
            evaluation_rate_percent=Decimal("98.00"),
        )

        response = self.detail()

        self.assertContains(response, "Preço observado")
        self.assertContains(response, "Não disponível")

    def test_price_without_currency_falls_back_to_previous_valid_pair(self):
        offer = self.make_offer()
        now = timezone.now()
        OfferObservation.objects.create(
            offer=offer,
            price=Decimal("500.00"),
            currency="EUR",
            observed_at=now - timedelta(hours=1),
        )
        OfferObservation.objects.create(
            offer=offer,
            price=Decimal("450.00"),
            currency=None,
            observed_at=now,
        )

        response = self.detail()

        self.assertContains(response, "500,00 EUR")
        self.assertNotContains(response, "450,00")

    def test_logistics_falls_back_to_previous_renderable_observation(self):
        offer = self.make_offer()
        now = timezone.now()
        OfferObservation.objects.create(
            offer=offer,
            delivery_days=4,
            observed_at=now - timedelta(hours=1),
        )
        OfferObservation.objects.create(
            offer=offer,
            availability=OfferObservation.Availability.UNKNOWN,
            observed_at=now,
        )

        response = self.detail()

        self.assertContains(response, "Estimativa indicada no detalhe: 4 dias")

    def test_without_renderable_logistics_uses_unconfirmed_copy(self):
        offer = self.make_offer()
        OfferObservation.objects.create(
            offer=offer,
            search_ship_to_days_raw="raw text only",
            ship_to_days_raw="another raw value",
        )

        response = self.detail()

        self.assertContains(response, "Prazo não confirmado")
        self.assertNotContains(response, "raw text only")

    def test_inactive_offer_remains_excluded(self):
        offer = self.make_offer(is_active=False)
        OfferObservation.objects.create(offer=offer, price=Decimal("400.00"), currency="EUR")

        response = self.detail()

        self.assertNotContains(response, offer.title)

    def test_owner_hidden_offer_remains_excluded(self):
        offer = self.make_offer(owner_hidden=True)
        OfferObservation.objects.create(offer=offer, price=Decimal("400.00"), currency="EUR")

        response = self.detail()

        self.assertNotContains(response, offer.title)

    def test_affiliate_ineligible_offer_remains_excluded(self):
        offer = self.make_offer(
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.INELIGIBLE
        )
        OfferObservation.objects.create(offer=offer, price=Decimal("400.00"), currency="EUR")

        response = self.detail()

        self.assertNotContains(response, offer.title)

    def test_homepage_family_card_uses_same_price_fallback(self):
        offer = self.make_offer()
        now = timezone.now()
        OfferObservation.objects.create(
            offer=offer,
            price=Decimal("321.00"),
            currency="EUR",
            observed_at=now - timedelta(hours=1),
        )
        OfferObservation.objects.create(offer=offer, observed_at=now)

        response = self.client.get(reverse("storefront:home"))

        self.assertContains(response, "321,00 EUR")

    def test_price_timestamp_is_from_price_source_observation(self):
        offer = self.make_offer()
        old = timezone.now() - timedelta(days=2)
        latest = timezone.now()
        OfferObservation.objects.create(
            offer=offer,
            price=Decimal("250.00"),
            currency="EUR",
            observed_at=old,
        )
        OfferObservation.objects.create(
            offer=offer,
            evaluation_rate_percent=Decimal("99.00"),
            observed_at=latest,
        )

        response = self.detail()

        expected = timezone.localtime(old).strftime("%d/%m/%Y %H:%M")
        latest_text = timezone.localtime(latest).strftime("%d/%m/%Y %H:%M")
        self.assertContains(response, expected)
        if expected != latest_text:
            self.assertNotContains(response, latest_text)

    def test_observation_prefetch_is_bounded_for_multiple_offers(self):
        now = timezone.now()
        for index in range(3):
            offer = self.make_offer(external_id=f"query-{index}")
            OfferObservation.objects.create(
                offer=offer,
                price=Decimal("100.00") + index,
                currency="EUR",
                observed_at=now - timedelta(hours=1),
            )
            OfferObservation.objects.create(offer=offer, observed_at=now)

        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(reverse("storefront:home"))

        self.assertEqual(response.status_code, 200)
        observation_queries = [
            query["sql"]
            for query in captured.captured_queries
            if "catalog_offerobservation" in query["sql"].lower()
        ]
        self.assertEqual(len(observation_queries), 1)
