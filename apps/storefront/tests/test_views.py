from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Offer, OfferObservation, ProductFamily


class StorefrontViewTests(TestCase):
    def test_homepage_returns_200_with_empty_state(self):
        response = self.client.get(reverse("storefront:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A seleção pública está a ser preparada")

    def test_missing_product_family_returns_404(self):
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": "missing"})
        )
        self.assertEqual(response.status_code, 404)

    def test_detail_renders_family_and_active_offer(self):
        family = ProductFamily.objects.create(
            name="HIFU Professional",
            slug="hifu-professional",
            status=ProductFamily.Status.TESTING,
        )
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="123",
            product_family=family,
            title="7D HIFU Professional Machine",
        )
        OfferObservation.objects.create(
            offer=offer,
            price=Decimal("199.90"),
            currency="EUR",
            sales_count=12,
            search_delivery_days=5,
            delivery_days=None,
        )
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "HIFU Professional")
        self.assertContains(response, "7D HIFU Professional Machine")
        self.assertContains(response, "199,90 EUR")
        self.assertContains(response, "Estimativa indicada pela pesquisa: 5 dias")

    def test_null_fields_do_not_render_false_zero_values(self):
        family = ProductFamily.objects.create(name="Test Family", slug="test-family")
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="nulls",
            product_family=family,
            title="Offer with unknown values",
        )
        OfferObservation.objects.create(
            offer=offer,
            price=None,
            evaluation_rate_percent=None,
            sales_count=None,
            search_delivery_days=None,
            delivery_days=None,
        )
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        self.assertContains(response, "Não disponível")
        self.assertNotContains(response, "0 EUR")
        self.assertNotContains(response, "0 estrelas")
        self.assertNotContains(response, "0 dias")

    def test_strong_internal_statuses_are_not_promoted_publicly(self):
        for status in (
            ProductFamily.Status.VERIFIED,
            ProductFamily.Status.PROVEN,
            ProductFamily.Status.WINNER,
        ):
            family = ProductFamily.objects.create(
                name=f"Family {status}",
                slug=f"family-{status.lower()}",
                status=status,
            )
            response = self.client.get(
                reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
            )
            self.assertContains(response, "Em avaliação")
            self.assertNotContains(response, f">{status}<")

    def test_templates_do_not_make_guaranteed_delivery_claims(self):
        family = ProductFamily.objects.create(name="Logistics", slug="logistics")
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="delivery",
            product_family=family,
        )
        OfferObservation.objects.create(offer=offer, search_delivery_days=5)
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        content = response.content.decode().lower()
        self.assertNotIn("entrega garantida", content)
        self.assertNotIn("guaranteed", content)
        self.assertIn("estimativa indicada pela pesquisa", content)

    def test_family_without_offers_has_safe_empty_state(self):
        family = ProductFamily.objects.create(name="Empty Family", slug="empty-family")
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        self.assertContains(response, "Sem ofertas ativas neste momento")

    def test_latest_observation_is_used_for_display(self):
        family = ProductFamily.objects.create(name="Latest", slug="latest")
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="latest-offer",
            product_family=family,
        )
        now = timezone.now()
        OfferObservation.objects.create(
            offer=offer,
            price=Decimal("100.00"),
            currency="EUR",
            observed_at=now - timedelta(days=1),
        )
        OfferObservation.objects.create(
            offer=offer, price=Decimal("150.00"), currency="EUR", observed_at=now
        )
        response = self.client.get(reverse("storefront:home"))
        self.assertContains(response, "150,00 EUR")
        self.assertNotContains(response, "100,00 EUR")

    def test_retired_family_hidden_from_home_but_detail_remains_accessible(self):
        family = ProductFamily.objects.create(
            name="Retired Family", slug="retired-family", status=ProductFamily.Status.RETIRED
        )
        home = self.client.get(reverse("storefront:home"))
        detail = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        self.assertNotContains(home, "Retired Family")
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Retired Family")

    def test_inactive_offer_is_not_rendered_publicly(self):
        family = ProductFamily.objects.create(name="Inactive Test", slug="inactive-test")
        Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="inactive-offer",
            product_family=family,
            title="Hidden inactive offer",
            is_active=False,
        )
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        self.assertNotContains(response, "Hidden inactive offer")
        self.assertContains(response, "Sem ofertas ativas neste momento")

    def test_conflicting_logistics_are_presented_neutrally(self):
        family = ProductFamily.objects.create(name="Conflict", slug="conflict")
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="conflict-offer",
            product_family=family,
        )
        OfferObservation.objects.create(
            offer=offer, search_delivery_days=3, delivery_days=5
        )
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        content = response.content.decode()
        self.assertIn("As fontes apresentam estimativas diferentes", content)
        self.assertNotIn("Entrega garantida", content)
        self.assertNotIn("Estimativa indicada pela pesquisa: 3 dias", content)
        self.assertNotIn("Estimativa indicada no detalhe: 5 dias", content)
