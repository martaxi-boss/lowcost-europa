"""Regression checks for the private read-only commercial dashboard."""

import os
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import (
    ExternalMetricsSnapshot,
    Offer,
    OfferClick,
    OfferFamilyPlacement,
    ProductFamily,
)


class OwnerAnalyticsDashboardTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="owner-analytics",
            password="owner-test-only",
            is_staff=True,
        )
        self.family = ProductFamily.objects.create(
            name="Teste de estatísticas", slug="teste-estatisticas"
        )
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="analytics-offer",
            title="Máquina de testes",
            product_url="https://www.aliexpress.com/item/123456789.html",
            affiliate_url="https://s.click.aliexpress.com/e/_TestOnly",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=timezone.now(),
            protocol_verified_at=timezone.now(),
            owner_hidden=False,
            is_active=True,
        )
        OfferFamilyPlacement.objects.create(offer=self.offer, product_family=self.family)
        self.url = reverse("owner-panel:dashboard")
        self.client.force_login(self.owner)

    def _click_ago(self, days):
        click = OfferClick.objects.create(offer=self.offer)
        OfferClick.objects.filter(pk=click.pk).update(
            clicked_at=timezone.now() - timedelta(days=days)
        )
        return click

    def test_metrics_are_real_outbound_clicks_not_sales_or_unique_visitors(self):
        self._click_ago(0.1)
        self._click_ago(3)
        self._click_ago(9)
        self._click_ago(20)
        self._click_ago(40)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["raw_clicks_24h"], 1)
        self.assertEqual(response.context["recent_raw_clicks_total"], 2)
        self.assertEqual(response.context["previous_raw_clicks_total"], 1)
        self.assertEqual(response.context["raw_clicks_30d"], 4)
        self.assertEqual(response.context["eligible_public_offers"], 1)
        self.assertEqual(response.context["visible_blocked_offers"], 0)
        self.assertEqual(response.context["top_clicked_offers"][0]["total"], 2)
        self.assertEqual(response.context["families"][0].recent_raw_clicks, 2)
        self.assertContains(response, "não representam visitantes únicos, compras ou comissões")
        self.assertContains(response, "indisponíveis até existirem integrações verificadas")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_daily_chart_includes_zero_days_and_local_date(self):
        self._click_ago(1)
        response = self.client.get(self.url)

        chart = response.context["daily_raw_clicks"]
        self.assertEqual(len(chart), 14)
        self.assertEqual(sum(item["total"] for item in chart), 1)
        yesterday = (timezone.localdate() - timedelta(days=1)).strftime("%d/%m/%Y")
        self.assertEqual(
            next(item["total"] for item in chart if item["date_label"] == yesterday), 1
        )
        self.assertGreaterEqual(sum(item["total"] == 0 for item in chart), 12)
        self.assertTrue(all(0 <= item["height"] <= 100 for item in chart))

    def test_missing_affiliate_link_is_not_counted_as_eligible(self):
        self.offer.affiliate_url = ""
        self.offer.save(update_fields=["affiliate_url", "updated_at"])

        response = self.client.get(self.url)

        self.assertEqual(response.context["eligible_public_offers"], 0)
        self.assertEqual(response.context["visible_blocked_offers"], 1)
        self.assertContains(response, "não passam o filtro público")

    def test_tracking_id_is_shown_to_owner_without_external_tracking_scripts(self):
        with patch.dict(os.environ, {"ALIEXPRESS_TRACKING_ID": "lowcost_europa"}):
            response = self.client.get(self.url)

        self.assertContains(response, "<code>lowcost_europa</code>", html=False)
        self.assertContains(response, "Por integrar no site")
        self.assertNotContains(response, "googletagmanager.com")
        self.assertNotContains(response, "fbq(")
        self.assertNotContains(response, "gtag(")
        self.assertNotContains(response, "ALIEXPRESS_APP_SECRET")

    def test_unauthorised_users_cannot_open_metrics(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        visitor = get_user_model().objects.create_user(
            username="visitor-analytics", password="test-only"
        )
        self.client.force_login(visitor)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_empty_period_has_no_fictitious_orders(self):
        response = self.client.get(self.url)

        self.assertEqual(response.context["raw_clicks_30d"], 0)
        self.assertEqual(response.context["top_clicked_offers"], [])
        self.assertContains(response, "Sem cliques de saída registados")
        self.assertContains(response, "A aguardar primeira sincronização")

    def test_verified_order_report_appears_on_private_dashboard(self):
        now = timezone.now()
        ExternalMetricsSnapshot.objects.create(
            source="ALIEXPRESS",
            period_start=now - timedelta(days=30),
            period_end=now,
            checked_at=now,
            payload={
                "days": 30,
                "paid_count": 2,
                "received_count": 1,
                "excluded_count": 0,
                "missing_commission_count": 0,
                "by_tracking": [
                    {
                        "tracking_id": "lowcost_europa",
                        "paid_count": 2,
                        "received_count": 1,
                        "estimated_paid": [{"currency": "USD", "amount": "4.50"}],
                        "estimated_finished": [],
                    }
                ],
            },
        )
        with patch("apps.integrations.aliexpress.client.AliExpressClient._call") as request_api:
            response = self.client.get(self.url)
        request_api.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["affiliate_report_fresh"])
        self.assertContains(response, "Consulta automática ativa")
        self.assertContains(response, "4.50 USD")
        self.assertContains(response, "lowcost_europa")
        self.assertContains(response, "Autorização da VPS necessária")
        self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_stale_report_is_explicit_not_live(self):
        now = timezone.now()
        old = now - timedelta(hours=13)
        ExternalMetricsSnapshot.objects.create(
            source="ALIEXPRESS",
            period_start=old - timedelta(days=30),
            period_end=old,
            checked_at=old,
            payload={
                "days": 30,
                "paid_count": 0,
                "received_count": 0,
                "excluded_count": 0,
                "missing_commission_count": 0,
                "by_tracking": [],
            },
        )
        response = self.client.get(self.url)
        self.assertFalse(response.context["affiliate_report_fresh"])
        self.assertContains(response, "Dados desatualizados")
        self.assertNotContains(response, "Consulta automática ativa")
