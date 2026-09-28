from datetime import timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import (
    Offer,
    OfferClick,
    OfferFamilyPlacement,
    OfferObservation,
    ProductFamily,
)
from apps.catalog.services.public_eligibility import (
    ALLOWED_SHIP_FROM_COUNTRIES,
    is_ship_from_verified,
    public_eligibility_q,
)


class PublicEligibilityTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(name="HIFU", slug="hifu")

    def make(self, ext, country="PL", protocol_when=None, ship_from_when=None):
        protocol_when = protocol_when or timezone.now()
        ship_from_when = ship_from_when if ship_from_when is not None else protocol_when
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id=ext,
            title=ext,
            affiliate_url=f"https://affiliate.example/{ext}",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=timezone.now(),
            ship_from_country=country,
            ship_from_verified_at=ship_from_when,
            protocol_verified_at=protocol_when,
        )
        OfferFamilyPlacement.objects.create(offer=offer, product_family=self.family)
        return offer

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

    def test_all_allowed_ship_from_countries_may_be_public(self):
        self.assertEqual(ALLOWED_SHIP_FROM_COUNTRIES, frozenset({"PL", "CZ", "FR", "ES", "DE"}))
        for country in sorted(ALLOWED_SHIP_FROM_COUNTRIES):
            with self.subTest(country=country):
                self.assert_public(self.make(f"allowed-{country}", country=country))

    def test_missing_ship_from_country_is_not_public_and_go_creates_no_click(self):
        offer = self.make("missing-country", country=None)
        clicks_before = OfferClick.objects.filter(offer=offer).count()

        self.assert_not_public(offer)

        self.assertEqual(OfferClick.objects.filter(offer=offer).count(), clicks_before)
        offer.refresh_from_db()
        self.assertTrue(offer.is_active)

    def test_missing_ship_from_verification_is_not_public(self):
        offer = self.make("missing-ship-verified")
        offer.ship_from_verified_at = None
        offer.save(update_fields=["ship_from_verified_at"])
        self.assert_not_public(offer)

    def test_future_ship_from_verification_is_not_public(self):
        offer = self.make(
            "future-ship",
            ship_from_when=timezone.now() + timedelta(hours=1),
        )
        self.assert_not_public(offer)

    def test_old_ship_from_verification_has_no_age_expiry(self):
        for days in (30, 180):
            with self.subTest(days=days):
                when = timezone.now() - timedelta(days=days)
                offer = self.make(
                    f"old-ship-{days}",
                    protocol_when=when,
                    ship_from_when=when,
                )
                self.assertTrue(is_ship_from_verified(offer))
                self.assert_public(offer)

    def test_disallowed_ship_from_country_is_rejected(self):
        now = timezone.now()
        offer = Offer(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="disallowed-origin",
            ship_from_country="CN",
            ship_from_verified_at=now,
            protocol_verified_at=now,
        )
        self.assertFalse(is_ship_from_verified(offer))
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                offer.save()

    def test_protocol_verified_without_individual_ship_from_is_not_public(self):
        offer = self.make("attested-no-country", country=None)
        offer.ship_from_verified_at = None
        offer.save(update_fields=["ship_from_verified_at"])
        self.assert_not_public(offer)

    def test_protocol_age_has_no_expiry_when_shipping_is_valid(self):
        for days in (8, 30, 180):
            with self.subTest(days=days):
                when = timezone.now() - timedelta(days=days)
                self.assert_public(
                    self.make(
                        f"protocol-{days}",
                        protocol_when=when,
                        ship_from_when=when,
                    )
                )

    def test_null_protocol_verification_hidden(self):
        offer = self.make("null-protocol")
        offer.protocol_verified_at = None
        offer.save(update_fields=["protocol_verified_at"])
        self.assert_not_public(offer)

    def test_future_protocol_verification_hidden(self):
        self.assert_not_public(
            self.make(
                "future-protocol",
                protocol_when=timezone.now() + timedelta(hours=1),
                ship_from_when=timezone.now(),
            )
        )

    def test_old_available_offer_stays_active_and_public(self):
        observed_at = timezone.now() - timedelta(days=90)
        offer = self.make(
            "old-available",
            protocol_when=observed_at,
            ship_from_when=observed_at,
        )
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

    def test_missing_affiliate_url_is_hidden(self):
        offer = self.make("missing-affiliate")
        offer.affiliate_url = ""
        offer.save(update_fields=["affiliate_url"])
        self.assert_not_public(offer)

    def test_affiliate_ineligible_is_distinct_from_unavailable(self):
        offer = self.make("promo-ineligible")
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
