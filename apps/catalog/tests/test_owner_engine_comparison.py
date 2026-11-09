"""Search-engine source comparison uses only verifiable existing metrics."""

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import ExternalMetricsSnapshot


class OwnerSearchEngineComparisonTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            username="engine-report-owner",
            password="test-only-password",
            is_staff=True,
        )
        self.url = reverse("owner-panel:dashboard")
        self.client.force_login(self.staff)

    def test_unreported_engines_have_no_fabricated_zero_clicks(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        rows = response.context["engine_comparison_rows"]
        self.assertEqual(
            [row["name"] for row in rows],
            ["Google", "Bing", "Yahoo", "DuckDuckGo", "Brave", "Seznam", "Yandex"],
        )
        self.assertTrue(all(row["clicks"] is None for row in rows))
        self.assertTrue(all(row["impressions"] is None for row in rows))
        self.assertContains(response, "Motores de pesquisa — desempenho")
        self.assertContains(response, "indisponível")
        self.assertContains(response, "não apenas a Portugal")
        self.assertContains(response, "não recolhe novos dados dos visitantes")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_only_google_official_snapshot_populates_its_engine_row(self):
        now = timezone.now()
        ExternalMetricsSnapshot.objects.create(
            source="GOOGLE_SEARCH_CONSOLE",
            period_start=now - timedelta(days=30),
            period_end=now,
            checked_at=now,
            payload={
                "property": "sc-domain:lowcost-europa.eu",
                "clicks": 27,
                "impressions": 450,
                "ctr_percent": "6.00",
                "average_position": "12.00",
                "top_queries": [],
            },
        )
        with patch(
            "apps.catalog.services.windsor_search_console_reporting._fetch_rows"
        ) as provider:
            response = self.client.get(self.url)
        provider.assert_not_called()
        rows = response.context["engine_comparison_rows"]
        self.assertEqual(rows[0]["clicks"], 27)
        self.assertEqual(rows[0]["impressions"], 450)
        self.assertEqual(rows[0]["status"], "Métricas sincronizadas")
        self.assertIsNotNone(rows[0]["checked_at"])
        self.assertTrue(all(row["clicks"] is None for row in rows[1:]))
        self.assertContains(response, "27")
        self.assertContains(response, "450")
        self.assertNotContains(response, "Bing — 0 cliques")

    def test_verified_google_zero_differs_from_missing_engine_data(self):
        now = timezone.now()
        ExternalMetricsSnapshot.objects.create(
            source="GOOGLE_SEARCH_CONSOLE",
            period_start=now - timedelta(days=30),
            period_end=now,
            checked_at=now,
            payload={
                "property": "sc-domain:lowcost-europa.eu",
                "clicks": 0,
                "impressions": 0,
            },
        )
        rows = self.client.get(self.url).context["engine_comparison_rows"]
        self.assertEqual(rows[0]["clicks"], 0)
        self.assertEqual(rows[0]["impressions"], 0)
        self.assertIsNone(rows[1]["clicks"])

    def test_engine_comparison_is_staff_only(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(get_user_model().objects.create_user(
            username="not-owner-engine", password="test-only-password"
        ))
        self.assertEqual(self.client.get(self.url).status_code, 403)
