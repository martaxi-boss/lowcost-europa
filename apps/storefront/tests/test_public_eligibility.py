from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Offer, OfferFamilyPlacement, OfferObservation, ProductFamily
from apps.catalog.services.public_eligibility import public_eligibility_q


class PublicEligibilityTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(name="HIFU", slug="hifu")

    def make(self, ext, country="PL", when=None):
        o = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id=ext,
            title=ext,
            affiliate_url=f"https://affiliate.example/{ext}",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=timezone.now(),
            ship_from_country=country,
            ship_from_verified_at=when,
            protocol_verified_at=when,
        )
        OfferFamilyPlacement.objects.create(offer=o, product_family=self.family)
        return o

    def detail(self):
        return self.client.get(reverse("storefront:product-family-detail", kwargs={"slug": "hifu"}))

    def assert_public(self, offer):
        self.assertContains(self.detail(), offer.title)
        self.assertEqual(
            self.client.get(reverse("storefront:offer-go", args=[offer.pk])).status_code,
            302,
        )

    def assert_not_public(self, offer):
        self.assertNotContains(self.detail(), offer.title)
        self.assertEqual(
            self.client.get(reverse("storefront:offer-go", args=[offer.pk])).status_code,
            404,
        )

    def test_verified_today_is_public(self):
        self.assert_public(self.make("verified-today", when=timezone.now()))

    def test_verified_8_days_ago_remains_public(self):
        self.assert_public(self.make("verified-8-days", when=timezone.now() - timedelta(days=8)))

    def test_verified_30_days_ago_remains_public(self):
        self.assert_public(
            self.make("verified-30-days", when=timezone.now() - timedelta(days=30))
        )

    def test_verified_many_months_ago_remains_public(self):
        self.assert_public(
            self.make("verified-months", when=timezone.now() - timedelta(days=180))
        )

    def test_null_verification_hidden(self):
        self.assert_not_public(self.make("null", when=None))

    def test_future_verification_hidden(self):
        self.assert_not_public(self.make("future", when=timezone.now() + timedelta(hours=1)))

    def test_old_available_offer_stays_active_and_public(self):
        observed_at = timezone.now() - timedelta(days=90)
        offer = self.make("old-available", when=observed_at)
        OfferObservation.objects.create(
            offer=offer,
            observed_at=observed_at,
            availability=OfferObservation.Availability.AVAILABLE,
            destination_country="PT",
        )

        offer.refresh_from_db()
        self.assertTrue(offer.is_active)
        self.assertTrue(
            Offer.objects.filter(pk=offer.pk).filter(public_eligibility_q()).exists()
        )
        self.assert_public(offer)

    def test_verified_attestation_without_individual_ship_from_is_eligible(self):
        offer = self.make("attested-no-country", country=None, when=timezone.now())
        offer.ship_from_verified_at = None
        offer.save(update_fields=["ship_from_verified_at"])
        self.assert_public(offer)

    def test_missing_affiliate_url_is_hidden(self):
        offer = self.make("missing-affiliate", when=timezone.now())
        offer.affiliate_url = ""
        offer.save(update_fields=["affiliate_url"])
        self.assert_not_public(offer)

    def test_affiliate_ineligible_is_distinct_from_unavailable(self):
        offer = self.make("promo-ineligible", when=timezone.now() - timedelta(days=30))
        offer.affiliate_promotion_status = Offer.AffiliatePromotionStatus.INELIGIBLE
        offer.save(update_fields=["affiliate_promotion_status"])

        offer.refresh_from_db()
        self.assertTrue(offer.is_active)
        self.assert_not_public(offer)

    def test_legacy_unverified_offer_hidden_even_with_placement(self):
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="legacy",
            title="Legacy Hidden",
            affiliate_url="https://affiliate.example/legacy",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=timezone.now(),
        )
        OfferFamilyPlacement.objects.create(offer=offer, product_family=self.family)
        self.assert_not_public(offer)
