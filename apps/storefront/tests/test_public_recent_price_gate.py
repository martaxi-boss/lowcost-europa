"""A public offer/affiliate redirect must have genuine recent EUR price evidence."""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Offer, OfferFamilyPlacement, OfferObservation, ProductFamily
from apps.catalog.services.public_eligibility import public_eligibility_q


@override_settings(PUBLIC_RECENT_PRICE_REQUIRED=True)
class PublicRecentPriceGateTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.family = ProductFamily.objects.create(
            name="Oferta com prova de preço",
            slug="oferta-com-prova-de-preco",
        )
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="positive-price-gate-1",
            title="Aparelho de estética",
            product_url="https://www.aliexpress.com/item/111111.html",
            affiliate_url="https://s.click.aliexpress.com/e/_SafeTest",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=self.now,
            protocol_verified_at=self.now,
            is_active=True,
            owner_hidden=False,
        )
        self.placement = OfferFamilyPlacement.objects.create(
            offer=self.offer, product_family=self.family
        )
        self.go_url = reverse("storefront:offer-go", args=[self.offer.pk])
        self.detail_url = reverse(
            "storefront:product-family-detail",
            kwargs={"slug": self.family.slug},
        )

    def observe(self, *, price, hours_ago=1, currency="EUR", availability="UNKNOWN"):
        return OfferObservation.objects.create(
            offer=self.offer,
            observed_at=self.now - timedelta(hours=hours_ago),
            price=Decimal(str(price)) if price is not None else None,
            currency=currency,
            availability=availability,
            destination_country="PT",
        )

    def test_no_price_evidence_is_not_public_and_no_redirect(self):
        self.assertFalse(Offer.objects.filter(public_eligibility_q()).exists())
        self.assertEqual(self.client.get(self.go_url).status_code, 404)
        self.assertNotContains(self.client.get(self.detail_url), "Aparelho de estética")
        self.offer.refresh_from_db()
        self.assertTrue(self.offer.is_active)
        self.assertFalse(self.offer.owner_hidden)
        self.assertTrue(OfferFamilyPlacement.objects.filter(pk=self.placement.pk).exists())

    def test_expired_price_prevents_public_link_but_preserves_history(self):
        self.observe(price="125.00", hours_ago=25)
        self.observe(price=None, hours_ago=1)
        self.assertFalse(Offer.objects.filter(public_eligibility_q()).exists())
        self.assertEqual(self.client.get(self.go_url).status_code, 404)
        self.assertEqual(OfferObservation.objects.filter(offer=self.offer).count(), 2)

    def test_recent_positive_eur_price_is_published_despite_unknown_stock(self):
        self.observe(price="125.00", hours_ago=2)
        self.observe(price=None, hours_ago=1)
        self.assertTrue(Offer.objects.filter(public_eligibility_q()).exists())
        self.assertEqual(self.client.get(self.go_url).status_code, 302)
        self.assertContains(self.client.get(self.detail_url), "125,00 EUR")
        self.assertTrue(
            OfferFamilyPlacement.objects.filter(
                public_eligibility_q(prefix="offer__")
            ).filter(pk=self.placement.pk).exists()
        )

    def test_non_eur_or_zero_or_future_price_does_not_enable_publication(self):
        for price, currency, age in [
            ("100.00", "USD", 1),
            ("0.00", "EUR", 1),
            ("100.00", "EUR", -1),
        ]:
            with self.subTest(price=price, currency=currency, age=age):
                OfferObservation.objects.filter(offer=self.offer).delete()
                self.observe(price=price, currency=currency, hours_ago=age)
                self.assertFalse(Offer.objects.filter(public_eligibility_q()).exists())
                self.assertEqual(self.client.get(self.go_url).status_code, 404)

    def test_recovery_republishes_after_new_real_observation(self):
        self.observe(price="99.00", hours_ago=80)
        self.assertEqual(self.client.get(self.go_url).status_code, 404)
        self.observe(price="101.50", hours_ago=1)
        self.assertEqual(self.client.get(self.go_url).status_code, 302)
        self.assertContains(self.client.get(self.detail_url), "101,50 EUR")

    def test_owner_sees_held_price_without_editorial_deletion(self):
        self.observe(price="99.00", hours_ago=80)
        owner = get_user_model().objects.create_user(
            username="owner-price-test", password="x", is_staff=True
        )
        self.client.force_login(owner)
        result = self.client.get(reverse("owner-panel:dashboard"))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.context["eligible_public_offers"], 0)
        self.assertEqual(result.context["visible_blocked_offers"], 0)
        self.assertEqual(result.context["price_held_from_public"], 1)
        self.assertNotContains(result, "fora da montra")
        self.assertNotContains(result, "históricos e a aprovação editorial")
        managed = self.client.get(
            reverse("owner-panel:family", args=[self.family.slug]) + "?vista=auditoria"
        )
        self.assertContains(managed, "Retida: preço EUR sem observação recente")
        self.assertEqual(result["X-Robots-Tag"], "noindex, nofollow")
