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
    def test_no_provider_credentials_required_for_local_counter(self):
        with patch.dict(os.environ, {
            "WINDSOR_API_KEY": "legacy-test-only",
            "GOOGLE_OAUTH_REFRESH_TOKEN": "legacy-test-only",
        }):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contador gratuito — Google, Meta e AliExpress")
        self.assertContains(response, "Relatório de origens indisponível")
        self.assertEqual(response.context["google_local_requests_7d"], None)
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

    def test_private_search_referrer_counts_are_not_search_console_data(self):
        report = {
            "checked_at": timezone.now(),
            "total": 3,
            "rows": [{"name": "Google", "requests": 2},
                     {"name": "Bing", "requests": 1}],
        }
        with patch(
            "apps.catalog.owner_panel_views.read_private_report", return_value=report
        ):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contador gratuito — Google, Meta e AliExpress")
        self.assertContains(response, "Pedidos de páginas com origem Google identificada")
        self.assertNotContains(response, "Google Analytics 4")
        self.assertEqual(response.context["search_referrers"]["total"], 3)
        self.assertTrue(response.context["search_referrers_recent"])
        self.assertContains(response, "Recolha local recente")
        engine_rows = response.context["engine_comparison_rows"]
        self.assertEqual(engine_rows[0]["local_requests"], 2)
        self.assertEqual(engine_rows[1]["local_requests"], 1)
        self.assertEqual(len(engine_rows), 2)
        self.assertNotIn("clicks", engine_rows[1])
        self.assertContains(response, "Chegadas identificadas (VPS, 7 dias)")
        self.assertEqual(response.context["google_local_requests_7d"], 2)
        self.assertEqual(response["Cache-Control"], "private, no-store")

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

    def test_owner_sees_meta_local_counts_not_old_meta_account(self):
        report = {
            "checked_at": timezone.now(),
            "total": 0,
            "rows": [{"name": "Google", "requests": 0}],
            "meta": {
                "total": 4, "facebook": 2, "instagram": 1, "unspecified": 1,
                "paid_tagged": 1, "today": 3, "yesterday": 1,
                "daily": [{"date": "2026-11-10", "requests": 3}],
            },
        }
        self._click_ago(0.01)
        with patch(
            "apps.catalog.owner_panel_views.read_private_report", return_value=report
        ):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chegadas da Meta — contador próprio")
        self.assertContains(response, "Campanhas identificadas por UTM pago")
        self.assertEqual(response.context["search_referrers"]["meta"]["total"], 4)
        self.assertEqual(response.context["raw_clicks_today"], 1)
        self.assertNotContains(response, "Meta Ads")
        self.assertEqual(response["Cache-Control"], "private, no-store")

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
        self.assertNotContains(
            response, "2 candidatos pendentes pertencem a famílias descontinuadas"
        )
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
        self.assertNotContains(response, "Autorização da VPS necessária")
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
        self.assertContains(response, "Contador gratuito — Google, Meta e AliExpress")
        self.assertNotContains(response, "Meta Ads")
        self.assertNotContains(response, "Google Search Console")
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

    def test_old_meta_snapshot_never_renders_or_leaks_into_summary(self):
        now = timezone.now()
        ExternalMetricsSnapshot.objects.create(
            source="META",
            period_start=now - timedelta(days=30),
            period_end=now,
            checked_at=now,
            payload={
                "account_name": "UNAUTHORIZED_OLD_ADVERTISER",
                "spend": "25.22",
                "clicks": 382,
            },
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Meta Ads")
        self.assertNotContains(response, "UNAUTHORIZED_OLD_ADVERTISER")
        self.assertNotContains(response, "25.22")
        self.assertNotContains(response, "382")
        self.assertNotIn("meta_report_payload", response.context)
        self.assertContains(response, "Contador gratuito — Google, Meta e AliExpress")
        self.assertContains(response, "AliExpress")
        self.assertContains(response, "Google — chegadas identificadas")
        self.assertTrue(ExternalMetricsSnapshot.objects.filter(source="META").exists())

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
        self.assertNotContains(response, "Autorização da VPS necessária")
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

    def test_legacy_search_console_snapshot_never_overrides_local_counter(self):
        now = timezone.now()
        self._click_ago(1)
        ExternalMetricsSnapshot.objects.create(
            source="GOOGLE_SEARCH_CONSOLE",
            period_start=now - timedelta(days=30),
            period_end=now,
            checked_at=now,
            payload={
                "provider": "WINDSOR",
                "property": "sc-domain:lowcost-europa.eu",
                "clicks": 999,
                "impressions": 9999,
                "top_queries": [{"query": "hidden-old-query", "clicks": 5}],
            },
        )
        response = self.client.get(self.url)
        self.assertEqual(response.context["recent_raw_clicks_total"], 1)
        self.assertIsNone(response.context["google_local_requests_7d"])
        self.assertNotContains(response, "9999")
        self.assertNotContains(response, "hidden-old-query")
        self.assertNotContains(response, "Métricas Google sincronizadas")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_old_local_report_does_not_claim_realtime_zero_for_today(self):
        previous = timezone.now() - timedelta(hours=5)
        report = {
            "checked_at": previous,
            "total": 0,
            "rows": [{"name": "Google", "requests": 0}],
            "meta": {
                "total": 2,
                "facebook": 1,
                "instagram": 1,
                "unspecified": 0,
                "paid_tagged": 2,
                "today": 2,
                "yesterday": 0,
                "daily": [{"date": "2026-11-11", "requests": 2}],
            },
        }
        with patch(
            "apps.catalog.owner_panel_views.read_private_report",
            return_value=report,
        ):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["search_referrers_recent"])
        self.assertContains(
            response, "Recolha atrasada — números até à última leitura",
            count=2,
        )
        self.assertEqual(response.context["search_referrers"]["meta"]["today"], 2)
        self.assertNotContains(response, "Recolha local recente")

    def test_simple_local_panel_does_not_need_google_or_third_party_keys(self):
        with patch.dict(os.environ, {
            "WINDSOR_API_KEY": "",
            "GOOGLE_OAUTH_CLIENT_ID": "",
            "GOOGLE_OAUTH_REFRESH_TOKEN": "",
        }):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contador gratuito — Google, Meta e AliExpress")
        self.assertNotContains(response, "Google Search Console")
        self.assertNotContains(response, "Google Ads")
        self.assertNotContains(response, "Windsor.ai")
