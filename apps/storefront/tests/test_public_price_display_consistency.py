"""The storefront must display the same trustworthy price the public gate accepts."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Offer, OfferFamilyPlacement, OfferObservation, ProductFamily


@override_settings(PUBLIC_RECENT_PRICE_REQUIRED=True)
class PublicPriceDisplayConsistencyTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.family = ProductFamily.objects.create(
            name="Equipamentos de teste", slug="equipamentos-de-teste"
        )
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="display-price-evidence-1",
            title="Equipamento verificado",
            affiliate_url="https://s.click.aliexpress.com/e/_SafeDisplayTest",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=self.now,
            protocol_verified_at=self.now,
            is_active=True,
            owner_hidden=False,
        )
        OfferFamilyPlacement.objects.create(offer=self.offer, product_family=self.family)

    def observe(self, *, price, currency, hours_ago, **facts):
        return OfferObservation.objects.create(
            offer=self.offer,
            price=Decimal(price) if price is not None else None,
            currency=currency,
            destination_country="PT",
            observed_at=self.now - timedelta(hours=hours_ago),
            **facts,
        )

    def test_only_recent_positive_eur_evidence_is_shown_in_public_views(self):
        self.observe(price="125.00", currency="EUR", hours_ago=3)
        # These later rows may be loaded for ratings, sales or commissions.
        # None is allowed to replace the verifiable EUR price in the UI.
        self.observe(
            price="999.00", currency="USD", hours_ago=2, sales_count=17
        )
        self.observe(
            price="0.00", currency="EUR", hours_ago=1,
            evaluation_rate_percent=Decimal("93.00"),
        )
        self.observe(
            price="888.00", currency="EUR", hours_ago=-1,
            commission_rate=Decimal("5.00"),
        )
        self.observe(price=None, currency=None, hours_ago=0.5)

        urls = (
            reverse("storefront:home"),
            reverse("storefront:product-family-detail", args=[self.family.slug]),
            reverse("storefront:search") + "?q=Equipamento",
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "125,00 EUR")
                self.assertNotContains(response, "999,00 USD")
                self.assertNotContains(response, "0,00 EUR")
                self.assertNotContains(response, "888,00 EUR")
                if "equipamentos-de-teste" in url:
                    self.assertIn(
                        'data-price="125.00" data-currency="EUR"',
                        response.content.decode(),
                    )

    def test_price_display_uses_latest_eligible_eur_observation(self):
        self.observe(price="100.00", currency="EUR", hours_ago=6)
        self.observe(price="150.00", currency="EUR", hours_ago=2)
        self.observe(
            price="190.00", currency="USD", hours_ago=1, sales_count=19
        )
        response = self.client.get(
            reverse("storefront:product-family-detail", args=[self.family.slug])
        )
        self.assertContains(response, "150,00 EUR")
        self.assertNotContains(response, "100,00 EUR")
        self.assertNotContains(response, "190,00 USD")
