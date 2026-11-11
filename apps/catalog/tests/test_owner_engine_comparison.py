"""Local first-party search source counts, never a Google API snapshot."""

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

    def test_no_local_report_is_unavailable_not_fabricated_zero(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        rows = response.context["engine_comparison_rows"]
        self.assertEqual(
            [row["name"] for row in rows],
            ["Google", "Bing", "Yahoo", "DuckDuckGo", "Brave", "Seznam", "Yandex"],
        )
        self.assertTrue(all(row["local_requests"] is None for row in rows))
        self.assertContains(response, "Relatório de origens indisponível")
        self.assertContains(response, "Chegadas identificadas (VPS, 7 dias)")
        self.assertContains(response, "O navegador pode ocultar a origem")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_google_and_other_origins_use_only_local_private_report(self):
        report = {
            "checked_at": timezone.now(),
            "total": 30,
            "rows": [
                {"name": "Google", "requests": 12},
                {"name": "Bing", "requests": 18},
                *[
                    {"name": name, "requests": 0}
                    for name in ("Yahoo", "DuckDuckGo", "Brave", "Seznam", "Yandex")
                ],
            ],
            "meta": {
                "total": 8, "facebook": 6, "instagram": 2, "unspecified": 0,
                "paid_tagged": 8, "today": 3, "yesterday": 5,
                "daily": [{"date": "2026-11-10", "requests": 8}],
            },
        }
        now = timezone.now()
        ExternalMetricsSnapshot.objects.create(
            source="GOOGLE_SEARCH_CONSOLE",
            period_start=now - timedelta(days=30),
            period_end=now,
            checked_at=now,
            payload={
                "provider": "WINDSOR", "property": "sc-domain:lowcost-europa.eu",
                "clicks": 777, "impressions": 900, "top_queries": [],
            },
        )
        with patch(
            "apps.catalog.owner_panel_views.read_private_report",
            return_value=report,
        ):
            response = self.client.get(self.url)
        self.assertEqual(response.context["google_local_requests_7d"], 12)
        self.assertEqual(response.context["engine_comparison_rows"][1]["local_requests"], 18)
        self.assertContains(response, "12")
        self.assertContains(response, "Google — chegadas identificadas")
        self.assertNotContains(response, "777")
        self.assertNotContains(response, "impressões no Google")
        self.assertNotContains(response, "Google Search Console")

    def test_local_observed_zero_differs_from_missing_data(self):
        report = {
            "checked_at": timezone.now(),
            "total": 0,
            "rows": [
                {"name": name, "requests": 0}
                for name in ("Google", "Bing", "Yahoo", "DuckDuckGo", "Brave", "Seznam", "Yandex")
            ],
            "meta": None,
        }
        with patch(
            "apps.catalog.owner_panel_views.read_private_report",
            return_value=report,
        ):
            response = self.client.get(self.url)
        self.assertEqual(response.context["google_local_requests_7d"], 0)
        self.assertContains(response, "zero pedidos identificados")

    def test_engine_comparison_is_staff_only(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(get_user_model().objects.create_user(
            username="not-owner-engine", password="test-only-password"
        ))
        self.assertEqual(self.client.get(self.url).status_code, 403)
