from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Offer, OfferClick, OfferFamilyPlacement, ProductFamily


class OneProductLandingPilotTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(
            name="Cavitação", slug="cavitacao-rf-vacuum-corpo"
        )
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS_OWNER,
            external_product_id="1005013070854347",
            title="AOKO - equipamento selecionado",
            image_url="https://static.example.test/product.jpg",
            affiliate_url="https://s.click.aliexpress.com/e/_c3qslKyf",
            protocol_verified_at=timezone.now(),
        )
        OfferFamilyPlacement.objects.create(offer=self.offer, product_family=self.family)
        self.url = reverse("storefront:offer-landing", args=[self.offer.pk])

    def test_single_product_page_does_not_modify_affiliate_link(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AOKO - equipamento selecionado")
        self.assertContains(response, "VER PREÇO NO ALIEXPRESS")
        self.assertContains(response, reverse("storefront:offer-go", args=[self.offer.pk]))
        self.assertNotContains(response, "https://s.click.aliexpress.com/e/_EHuDEKi")
        self.assertEqual(response["X-Robots-Tag"], "noindex, follow")
        self.assertNotContains(response, '<link rel="canonical"', html=False)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.affiliate_url, "https://s.click.aliexpress.com/e/_c3qslKyf")
        self.assertFalse(OfferClick.objects.exists())

    def test_click_only_on_existing_go_endpoint(self):
        self.client.get(self.url)
        self.assertFalse(OfferClick.objects.exists())
        response = self.client.get(reverse("storefront:offer-go", args=[self.offer.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], self.offer.affiliate_url)
        self.assertEqual(OfferClick.objects.count(), 1)

    def test_hidden_or_inactive_offers_not_reachable(self):
        self.offer.owner_hidden = True
        self.offer.save(update_fields=["owner_hidden"])
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.offer.owner_hidden = False
        self.offer.is_active = False
        self.offer.save(update_fields=["owner_hidden", "is_active"])
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_retired_family_not_reachable(self):
        self.family.status = ProductFamily.Status.RETIRED
        self.family.save(update_fields=["status"])
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_unknown_offer_not_reachable(self):
        missing = reverse("storefront:offer-landing", args=[999999])
        self.assertEqual(self.client.get(missing).status_code, 404)
