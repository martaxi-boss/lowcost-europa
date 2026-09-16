from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Offer, OfferFamilyPlacement, ProductFamily


class PublicEligibilityTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(name="HIFU", slug="hifu")

    def make(self, ext, country="PL", when=None):
        o = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id=ext,
            title=ext,
            affiliate_url=f"https://affiliate.example/{ext}",
            ship_from_country=country,
            ship_from_verified_at=when,
        )
        OfferFamilyPlacement.objects.create(offer=o, product_family=self.family)
        return o

    def detail(self):
        return self.client.get(reverse("storefront:product-family-detail", kwargs={"slug": "hifu"}))

    def test_fresh_allowed_visible_and_go_works(self):
        o = self.make("fresh", when=timezone.now())
        self.assertContains(self.detail(), "fresh")
        self.assertEqual(
            self.client.get(reverse("storefront:offer-go", args=[o.pk])).status_code, 302
        )

    def test_stale_hidden_and_go_blocked(self):
        o = self.make("stale", when=timezone.now() - timedelta(days=8))
        self.assertNotContains(self.detail(), "stale")
        self.assertEqual(
            self.client.get(reverse("storefront:offer-go", args=[o.pk])).status_code, 404
        )

    def test_null_verification_hidden(self):
        o = self.make("null", when=None)
        self.assertNotContains(self.detail(), "null")
        self.assertEqual(
            self.client.get(reverse("storefront:offer-go", args=[o.pk])).status_code, 404
        )

    def test_future_verification_hidden(self):
        o = self.make("future", when=timezone.now() + timedelta(hours=1))
        self.assertNotContains(self.detail(), "future")
        self.assertEqual(
            self.client.get(reverse("storefront:offer-go", args=[o.pk])).status_code, 404
        )

    def test_legacy_unverified_offer_hidden_even_with_placement(self):
        o = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="legacy",
            title="Legacy Hidden",
            affiliate_url="https://affiliate.example/legacy",
        )
        OfferFamilyPlacement.objects.create(offer=o, product_family=self.family)
        self.assertNotContains(self.detail(), "Legacy Hidden")
