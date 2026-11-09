"""Regression tests for explicit Owner-only commercial evidence and provenance."""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Offer, OfferFamilyPlacement, OfferObservation, ProductFamily
from apps.catalog.services.commercial_evidence import owner_commercial_evidence_rows


@override_settings(PUBLIC_RECENT_PRICE_REQUIRED=True)
class OwnerCommercialEvidenceTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.family = ProductFamily.objects.create(
            name="Equipamentos com prova", slug="equipamentos-com-prova",
            status=ProductFamily.Status.VERIFIED,
        )
        self.owner = get_user_model().objects.create_user(
            username="owner-evidence", password="test-password-only", is_staff=True
        )
        self.fresh = self.make_offer(
            "verificado", ship_from_country="PL",
            ship_from_verified_at=self.now - timedelta(days=9),
        )
        self.stale = self.make_offer("historico")
        OfferObservation.objects.create(
            offer=self.fresh, destination_country="PT", observed_at=self.now - timedelta(hours=2),
            price=Decimal("125.00"), currency="EUR",
            delivery_days=4, availability=OfferObservation.Availability.UNKNOWN,
        )
        OfferObservation.objects.create(
            offer=self.fresh, destination_country="PT", observed_at=self.now - timedelta(hours=1),
            availability=OfferObservation.Availability.UNKNOWN,
        )
        OfferObservation.objects.create(
            offer=self.stale, destination_country="PT", observed_at=self.now - timedelta(hours=48),
            price=Decimal("250.00"), currency="EUR",
            availability=OfferObservation.Availability.UNKNOWN,
        )
        OfferObservation.objects.create(
            offer=self.stale, destination_country="PT", observed_at=self.now - timedelta(hours=2),
            availability=OfferObservation.Availability.UNKNOWN,
        )

    def make_offer(self, name, **overrides):
        fields = {
            "source": Offer.Source.ALIEXPRESS,
            "external_product_id": f"commercial-evidence-{name}",
            "title": f"Equipamento {name}",
            "product_url": f"https://www.aliexpress.com/item/{name}.html",
            "affiliate_url": "https://s.click.aliexpress.com/e/_SafeTest",
            "affiliate_promotion_status": Offer.AffiliatePromotionStatus.ELIGIBLE,
            "affiliate_promotion_verified_at": self.now,
            "protocol_verified_at": self.now,
            "owner_hidden": False,
            "is_active": True,
        }
        fields.update(overrides)
        offer = Offer.objects.create(**fields)
        OfferFamilyPlacement.objects.create(offer=offer, product_family=self.family)
        return offer

    def test_read_only_table_distinguishes_price_origin_stock_and_delivery(self):
        with patch(
            "apps.integrations.aliexpress.client.AliExpressClient.get_product_detail"
        ) as provider:
            rows = owner_commercial_evidence_rows(as_of=self.now)
            provider.assert_not_called()
        self.assertEqual(len(rows), 2)
        fresh, stale = rows
        self.assertEqual(fresh.publication, "Na montra")
        self.assertEqual(fresh.price, Decimal("125.00"))
        self.assertEqual(fresh.price_state, "Observação recente (até 24 h)")
        self.assertIn("PL — registado em revisão editorial", fresh.origin)
        self.assertIn("Stock por variante não confirmado", fresh.availability)
        self.assertEqual(fresh.delivery, "Detalhe: 4 dias")
        self.assertIn("Estimativa observada", fresh.delivery_state)

        self.assertIn("Retida", stale.publication)
        self.assertEqual(stale.price, Decimal("250.00"))
        self.assertIn("Histórico", stale.price_state)
        self.assertEqual(stale.origin, "País/armazém por confirmar")
        self.assertEqual(stale.delivery, "Prazo não confirmado")

    def test_dashboard_shows_each_offer_only_to_staff(self):
        dashboard = reverse("owner-panel:dashboard")
        anonymous = self.client.get(dashboard)
        self.assertEqual(anonymous.status_code, 302)
        self.client.force_login(self.owner)
        response = self.client.get(dashboard)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Validação comercial — oferta a oferta")
        self.assertNotContains(response, "Consultar 2 ofertas selecionadas")
        self.assertNotContains(response, "Equipamento historico")
        self.assertNotContains(response, "Stock por variante não confirmado")
        self.assertNotContains(response, "País/armazém por confirmar")
        self.assertEqual(response.context["eligible_public_offers"], 1)
        self.assertEqual(response.context["price_held_from_public"], 1)
        self.assertEqual(response.context["origin_without_individual_proof"], 0)
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")
        self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_historical_price_remains_visible_in_private_audit_not_public(self):
        self.client.force_login(self.owner)
        private_family = reverse(
            "owner-panel:family", kwargs={"family_slug": self.family.slug}
        )
        private_page = self.client.get(private_family + "?vista=auditoria")
        self.assertEqual(private_page.status_code, 200)
        self.assertContains(private_page, "Equipamento historico")
        self.assertContains(private_page, "250")
        self.assertContains(private_page, "Preço histórico")
        self.assertContains(private_page, "País/armazém por confirmar")

        self.client.logout()
        public = self.client.get(
            reverse("storefront:product-family-detail", args=[self.family.slug])
        )
        self.assertNotContains(public, "Equipamento historico")
        self.assertNotContains(public, "Verificação interna")
        self.assertContains(public, "Equipamento verificado")

        self.client.force_login(self.owner)
        staff = self.client.get(
            reverse("storefront:product-family-detail", args=[self.family.slug])
        )
        self.assertContains(staff, "Verificação interna: origem, stock e entrega")
        self.assertContains(staff, "registada na revisão editorial")

    def test_delivery_for_other_country_is_not_evidence_for_portugal(self):
        OfferObservation.objects.create(
            offer=self.stale, destination_country="ES",
            observed_at=self.now - timedelta(minutes=30),
            delivery_days=2,
        )
        rows = owner_commercial_evidence_rows(as_of=self.now)
        self.assertEqual(rows[1].delivery, "Prazo não confirmado")

    def test_future_origin_review_not_counted_as_proof(self):
        self.fresh.ship_from_verified_at = self.now + timedelta(days=2)
        self.fresh.save(update_fields=["ship_from_verified_at"])
        rows = owner_commercial_evidence_rows(as_of=self.now)
        self.assertEqual(rows[0].origin, "País/armazém por confirmar")
        self.client.force_login(self.owner)
        response = self.client.get(reverse("owner-panel:dashboard"))
        self.assertEqual(response.context["origin_without_individual_proof"], 1)
        self.assertNotContains(response, "País/armazém por confirmar")

    def test_es_table_never_fills_missing_price_from_portugal(self):
        rows = owner_commercial_evidence_rows(as_of=self.now, country="ES")
        self.assertIsNone(rows[0].price)
        self.assertIsNone(rows[0].delivery_at)
        OfferObservation.objects.create(
            offer=self.fresh, destination_country="ES", price=Decimal("90.00"),
            currency="EUR", observed_at=self.now - timedelta(minutes=1),
        )
        pt = owner_commercial_evidence_rows(as_of=self.now)
        es = owner_commercial_evidence_rows(as_of=self.now, country="ES")
        self.assertEqual(pt[0].price, Decimal("125.00"))
        self.assertEqual(es[0].price, Decimal("90.00"))
        self.assertEqual(es[0].delivery, "Prazo não confirmado")
