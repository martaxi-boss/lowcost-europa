from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Offer, OfferFamilyPlacement, ProductFamily


class StorefrontAliExpressIsolationTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(name="HIFU", slug="hifu")
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="42",
            product_family=self.family,
            title="Persisted product",
            affiliate_url="https://affiliate.example.test/42",
            is_active=True,
            is_primary=True,
        )
        OfferFamilyPlacement.objects.create(
            offer=self.offer, product_family=self.family, selection_position=1
        )

    @patch("apps.integrations.aliexpress.client.AliExpressClient.__init__")
    def test_public_requests_do_not_instantiate_aliexpress_client(self, client_init):
        client_init.side_effect = AssertionError("AliExpressClient instantiated in request path")
        urls = [
            reverse("storefront:home"),
            reverse("storefront:product-family-detail", kwargs={"slug": self.family.slug}),
            reverse("storefront:contacto"),
            reverse("storefront:como-funciona"),
            reverse("storefront:afiliados"),
            reverse("storefront:privacidade"),
            reverse("storefront:termos"),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        go_response = self.client.get(
            reverse("storefront:offer-go", kwargs={"offer_id": self.offer.pk})
        )
        self.assertEqual(go_response.status_code, 302)
        self.assertEqual(go_response["Location"], self.offer.affiliate_url)
        client_init.assert_not_called()
