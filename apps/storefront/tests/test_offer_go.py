from unittest.mock import patch

from django.db import OperationalError
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Offer, OfferClick, OfferFamilyPlacement, ProductFamily


class OfferGoTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(name="7D HIFU", slug="7d-hifu")
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="go-offer",
            product_family=self.family,
            title="Eligible offer",
            affiliate_url="https://affiliate.example/item/123",
        )
        OfferFamilyPlacement.objects.create(offer=self.offer, product_family=self.family)
        self.url = reverse("storefront:offer-go", args=[self.offer.pk])

    def test_eligible_offer_redirects_and_records_raw_click(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], self.offer.affiliate_url)
        self.assertEqual(OfferClick.objects.filter(offer=self.offer).count(), 1)

    def test_each_valid_request_creates_separate_click(self):
        self.client.get(self.url)
        self.client.get(self.url)
        self.assertEqual(OfferClick.objects.filter(offer=self.offer).count(), 2)

    def test_missing_offer_returns_404_without_click(self):
        response = self.client.get(reverse("storefront:offer-go", args=[999999]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(OfferClick.objects.count(), 0)

    def test_inactive_offer_returns_404(self):
        self.offer.is_active = False
        self.offer.save(update_fields=["is_active"])
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(OfferClick.objects.count(), 0)

    def test_offer_without_placement_returns_404(self):
        OfferFamilyPlacement.objects.filter(offer=self.offer).delete()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(OfferClick.objects.count(), 0)

    def test_retired_family_returns_404(self):
        self.family.status = ProductFamily.Status.RETIRED
        self.family.save(update_fields=["status"])
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(OfferClick.objects.count(), 0)

    def test_empty_affiliate_url_returns_404(self):
        self.offer.affiliate_url = ""
        self.offer.save(update_fields=["affiliate_url"])
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(OfferClick.objects.count(), 0)

    @patch("apps.storefront.views.OfferClick.objects.create")
    def test_tracking_database_failure_is_fail_open(self, create_click):
        create_click.side_effect = OperationalError("tracking unavailable")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], self.offer.affiliate_url)

    @patch("apps.storefront.views.OfferClick.objects.create")
    def test_programming_errors_are_not_hidden(self, create_click):
        create_click.side_effect = RuntimeError("bug")
        with self.assertRaises(RuntimeError):
            self.client.get(self.url)

    def test_user_supplied_destination_is_ignored(self):
        response = self.client.get(
            f"{self.url}?url=https://evil.example/&next=https://evil.example/"
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], self.offer.affiliate_url)


class StorefrontCtaTests(TestCase):
    def test_homepage_category_cta_keeps_partner_destination_private(self):
        family = ProductFamily.objects.create(name="Primary", slug="primary-cta")
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="primary-cta-offer",
            product_family=family,
            affiliate_url="https://affiliate.example/primary",
            is_primary=True,
        )
        OfferFamilyPlacement.objects.create(
            offer=offer, product_family=family, selection_position=1
        )
        response = self.client.get(reverse("storefront:home"))
        family_url = reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        self.assertContains(response, f'href="{family_url}"')
        self.assertContains(response, "Ver seleção")
        self.assertNotContains(response, offer.affiliate_url)
        self.assertNotContains(response, reverse("storefront:offer-go", args=[offer.pk]))

    def test_detail_has_separate_internal_cta_for_each_eligible_offer(self):
        family = ProductFamily.objects.create(name="Two Offers", slug="two-offers")
        offers = []
        for suffix in ("one", "two"):
            offers.append(
                Offer.objects.create(
                    source=Offer.Source.ALIEXPRESS,
                    external_product_id=f"detail-{suffix}",
                    product_family=family,
                    affiliate_url=f"https://affiliate.example/{suffix}",
                )
            )
        for index, offer in enumerate(offers):
            OfferFamilyPlacement.objects.create(
                offer=offer, product_family=family, display_order=index
            )
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        for offer in offers:
            self.assertContains(
                response,
                f'href="{reverse("storefront:offer-go", args=[offer.pk])}"',
            )
            self.assertNotContains(response, offer.affiliate_url)
