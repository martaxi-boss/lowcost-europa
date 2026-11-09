"""Regression checks for the private read-only commercial dashboard."""

import os
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import (
    ExternalMetricsSnapshot,
    Offer,
    OfferCandidate,
    OfferClick,
    OfferFamilyPlacement,
    OfferObservation,
    ProductFamily,
)


class OwnerAnalyticsDashboardTests(TestCase):
    def test_configured_property_without_report_is_waiting_for_data_not_fake_metrics(self):
        self.client.force_login(self.owner)
        with patch.dict(os.environ, {
            "WINDSOR_API_KEY": "test-only",
            "GOOGLE_SEARCH_CONSOLE_PROPERTY": "sc-domain:lowcost-europa.eu",
        }):
            response = self.client.get(reverse("owner-panel:dashboard"))
        self.assertContains(response, "Leitura configurada — a aguardar dados")
        self.assertNotContains(response, "Falta autorizar a leitura automática")
        self.assertFalse(response.context["google_search_report_payload"])
        self.assertFalse(ExternalMetricsSnapshot.objects.exists())

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

    def test_missing_individual_origin_is_visible_only_as_owner_warning(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context["eligible_public_offers"], 1)
        self.assertEqual(response.context["origin_without_individual_proof"], 1)
        self.assertNotContains(response, "Origem individual por confirmar")
        self.assertNotContains(response, "Isso não significa origem proibida")
        self.offer.ship_from_country = "PL"
        self.offer.ship_from_verified_at = timezone.now()
        self.offer.save(update_fields=["ship_from_country", "ship_from_verified_at"])
        response = self.client.get(self.url)
        self.assertEqual(response.context["origin_without_individual_proof"], 0)

    def test_pending_queue_alert_never_changes_candidate_status(self):
        candidates = [
            OfferCandidate(
                source=Offer.Source.ALIEXPRESS,
                external_product_id=f"pending-audit-{index}",
                product_family=self.family,
                status=OfferCandidate.Status.PENDING,
            )
            for index in range(20)
        ]
        OfferCandidate.objects.bulk_create(candidates)
        response = self.client.get(self.url)
        self.assertEqual(response.context["paused_discovery_families"], 1)
        family = response.context["families"][0]
        self.assertTrue(family.discovery_paused)
        self.assertEqual(family.reviews_to_resume_discovery, 1)
        self.assertNotContains(response, "abrir fila de revisão")
        self.assertEqual(
            OfferCandidate.objects.filter(status=OfferCandidate.Status.PENDING).count(), 20
        )

    def test_factual_stock_price_and_logistics_warnings_never_invent_evidence(self):
        now = timezone.now()
        OfferObservation.objects.create(
            offer=self.offer,
            observed_at=now - timedelta(days=2),
            availability=OfferObservation.Availability.AVAILABLE,
            price=Decimal("99.99"),
            currency="EUR",
        )
        OfferObservation.objects.create(
            offer=self.offer,
            observed_at=now - timedelta(minutes=2),
            availability=OfferObservation.Availability.UNKNOWN,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["latest_availability_unconfirmed"], 1)
        self.assertEqual(response.context["current_price_unconfirmed"], 1)
        self.assertEqual(response.context["delivery_days_unproven"], 1)
        self.assertNotContains(response, "UNKNOWN não significa esgotado")
        self.assertNotContains(response, "o histórico pode existir")
        self.assertNotContains(response, "não deve prometer entrega em até 5 dias")

        OfferObservation.objects.create(
            offer=self.offer,
            observed_at=now - timedelta(minutes=1),
            availability=OfferObservation.Availability.AVAILABLE,
            price=Decimal("102.50"),
            currency="EUR",
            delivery_days=4,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.context["latest_availability_unconfirmed"], 0)
        self.assertEqual(response.context["current_price_unconfirmed"], 0)
        self.assertEqual(response.context["delivery_days_unproven"], 0)

    def test_price_with_whitespace_currency_is_not_fresh_evidence(self):
        OfferObservation.objects.create(
            offer=self.offer,
            observed_at=timezone.now(),
            price=Decimal("20.00"),
            currency="   ",
            availability=OfferObservation.Availability.UNKNOWN,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.context["current_price_unconfirmed"], 1)

    def test_retired_family_candidates_are_visible_in_owner_summary_without_mutation(self):
        retired = ProductFamily.objects.create(
            name="Microcorrente antiga",
            slug="microcorrente-antiga",
            status=ProductFamily.Status.RETIRED,
        )
        candidates = [
            OfferCandidate(
                source=Offer.Source.ALIEXPRESS,
                external_product_id=f"retired-pending-{index}",
                product_family=retired,
            )
            for index in range(2)
        ]
        OfferCandidate.objects.bulk_create(candidates)

        response = self.client.get(self.url)
        self.assertEqual(response.context["retired_pending_total"], 2)
        self.assertEqual(response.context["paused_discovery_families"], 0)
        self.assertEqual(len(response.context["families"]), 1)
        self.assertNotContains(response, "Microcorrente antiga")
        self.assertNotContains(response, "2 candidatos pendentes pertencem a famílias descontinuadas")
        self.assertEqual(
            OfferCandidate.objects.filter(
                product_family=retired, status=OfferCandidate.Status.PENDING
            ).count(),
            2,
        )

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
        self.assertNotContains(response, "não passam os requisitos de publicação")

    def test_tracking_id_is_shown_to_owner_without_external_tracking_scripts(self):
        with patch.dict(os.environ, {"ALIEXPRESS_TRACKING_ID": "lowcost_europa"}):
            response = self.client.get(self.url)

        self.assertNotContains(response, "<code>lowcost_europa</code>", html=False)
        self.assertContains(response, "Autorização da VPS necessária")
        self.assertNotContains(response, "googletagmanager.com")
        self.assertNotContains(response, "fbq(")
        self.assertNotContains(response, "gtag(")
        self.assertNotContains(response, "ALIEXPRESS_APP_SECRET")

    def test_summary_has_only_metrics_and_existing_store_management_is_unchanged(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Resumo de métricas")
        self.assertContains(response, "Cliques para parceiros")
        self.assertContains(response, "Evolução — 14 dias")
        self.assertContains(response, "Motores de pesquisa — desempenho")
        self.assertContains(response, "Meta Ads")
        self.assertContains(response, "Google Search Console")
        self.assertContains(response, "VER LOJA")
        for forbidden in (
            "Validação comercial — oferta a oferta",
            "Consultar 77 ofertas",
            "Produtos mais clicados",
            "Links de afiliado e montra",
            "Gestão por categoria",
            "A rever",
            "Retirados",
            "Selecionadas mas não publicadas",
        ):
            self.assertNotContains(response, forbidden)

        store = self.client.get(
            reverse("storefront:product-family-detail", args=[self.family.slug])
            + "?gestao=rever"
        )
        self.assertEqual(store.status_code, 200)
        self.assertContains(store, "Gestão ativa")
        self.assertContains(store, "A rever")
        self.assertContains(store, "Aprovados")
        self.assertContains(store, "Retirados")
        self.assertContains(store, "Revalidação")

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
        self.assertNotContains(response, "Produtos mais clicados")
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

    def test_google_search_snapshot_is_separate_from_local_outbound_clicks(self):
        now = timezone.now()
        self._click_ago(1)
        ExternalMetricsSnapshot.objects.create(
            source="GOOGLE_SEARCH_CONSOLE",
            period_start=now - timedelta(days=30),
            period_end=now,
            checked_at=now,
            payload={
                "property": "sc-domain:lowcost-europa.eu",
                "clicks": 23,
                "impressions": 480,
                "ctr_percent": "4.79",
                "average_position": "12.80",
                "top_queries": [{"query": "lowcost europa", "clicks": 7, "impressions": 80}],
            },
        )
        response = self.client.get(self.url)
        self.assertTrue(response.context["google_search_report_fresh"])
        self.assertEqual(response.context["google_search_report_payload"]["clicks"], 23)
        self.assertEqual(response.context["recent_raw_clicks_total"], 1)
        self.assertContains(response, "Métricas Google sincronizadas")
        self.assertContains(response, "Cliques da pesquisa Google")
        self.assertContains(response, "480")
        self.assertContains(response, "lowcost europa")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")
        self.assertNotContains(response, "gtag(")

    def test_missing_or_stale_google_data_is_not_invented(self):
        pending = self.client.get(self.url)
        self.assertContains(pending, "Ligação de métricas pendente")
        self.assertNotContains(pending, "Métricas Google sincronizadas")
        now = timezone.now()
        ExternalMetricsSnapshot.objects.create(
            source="GOOGLE_SEARCH_CONSOLE",
            period_start=now - timedelta(days=33),
            period_end=now - timedelta(days=3),
            checked_at=now - timedelta(hours=49),
            payload={
                "property": "sc-domain:lowcost-europa.eu",
                "clicks": 3,
                "impressions": 45,
                "ctr_percent": "6.67",
                "average_position": "16.25",
                "top_queries": [],
            },
        )
        stale = self.client.get(self.url)
        self.assertFalse(stale.context["google_search_report_fresh"])
        self.assertContains(stale, "Dados Google desatualizados")

    def test_google_metrics_stay_owner_only_without_external_requests(self):
        now = timezone.now()
        ExternalMetricsSnapshot.objects.create(
            source="GOOGLE_SEARCH_CONSOLE",
            period_start=now - timedelta(days=30),
            period_end=now,
            checked_at=now,
            payload={
                "property": "sc-domain:lowcost-europa.eu",
                "clicks": 4,
                "impressions": 40,
                "ctr_percent": "10.00",
                "average_position": "8.50",
                "top_queries": [],
            },
        )
        with patch(
            "apps.catalog.services.windsor_search_console_reporting._fetch_rows"
        ) as external:
            response = self.client.get(self.url)
        external.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)
