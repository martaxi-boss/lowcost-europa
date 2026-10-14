from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Offer, OfferClick, OfferFamilyPlacement, ProductFamily


class OfferClickQualityTests(TestCase):
    def setUp(self):
        family = ProductFamily.objects.create(
            name="Qualidade cliques", slug="qualidade-cliques"
        )
        now = timezone.now()
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="click-quality-001",
            title="Produto de teste",
            affiliate_url="https://affiliate.example.test/valid",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=now,
            protocol_verified_at=now,
            is_active=True,
            owner_hidden=False,
        )
        OfferFamilyPlacement.objects.create(offer=self.offer, product_family=family)
        self.go = reverse("storefront:offer-go", args=[self.offer.pk])

    def test_real_get_keeps_redirect_and_records_one_raw_click(self):
        response = self.client.get(self.go)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], self.offer.affiliate_url)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")
        self.assertEqual(OfferClick.objects.filter(offer=self.offer).count(), 1)

    def test_head_redirect_does_not_record_a_click(self):
        response = self.client.head(self.go)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], self.offer.affiliate_url)
        self.assertFalse(OfferClick.objects.exists())

    def test_browser_prefetch_and_prerender_are_not_clicks(self):
        for headers in (
            {"HTTP_SEC_PURPOSE": "prefetch"},
            {"HTTP_SEC_PURPOSE": "prefetch;prerender"},
            {"HTTP_PURPOSE": "prefetch"},
            {"HTTP_X_MOZ": "prefetch"},
        ):
            with self.subTest(headers=headers):
                response = self.client.get(self.go, **headers)
                self.assertEqual(response.status_code, 302)
        self.assertFalse(OfferClick.objects.exists())

    def test_post_is_rejected_without_tracking(self):
        response = self.client.post(self.go)
        self.assertEqual(response.status_code, 405)
        self.assertFalse(OfferClick.objects.exists())
