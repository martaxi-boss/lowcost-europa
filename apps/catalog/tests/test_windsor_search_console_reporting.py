"""Google Search Console metric integrity and private-only snapshot tests."""

import json
from datetime import timedelta
from unittest.mock import patch
from urllib.error import HTTPError

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from apps.catalog.models import ExternalMetricsSnapshot
from apps.catalog.services.windsor_search_console_reporting import (
    EXPECTED_PROPERTY,
    SearchConsoleNotConfigured,
    SearchConsoleReportError,
    collect_search_console_report,
)


class _FakeResponse:
    status = 200

    def __init__(self, data):
        self.payload = json.dumps(data).encode()

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        return False

    def read(self, length=-1):
        return self.payload[:length] if length >= 0 else self.payload


class SearchConsoleReportTests(SimpleTestCase):
    def test_verified_google_clicks_impressions_ctr_and_queries(self):
        requested = []

        def opener(req, timeout):
            requested.append(req.full_url)
            if "query" in req.full_url:
                return _FakeResponse([
                    {"account_id": EXPECTED_PROPERTY, "query": "lowcost europa", "clicks": 3, "impressions": 11},
                    {"account_id": EXPECTED_PROPERTY, "query": "ofertas europa", "clicks": 1, "impressions": 3},
                ])
            return _FakeResponse([
                {"account_id": EXPECTED_PROPERTY, "clicks": 7, "impressions": 100, "position": 11.5}
            ])

        report, start, end = collect_search_console_report(
            api_key="test-only-secret", property_id=EXPECTED_PROPERTY, opener=opener
        )
        self.assertEqual(report["source"], "GOOGLE_SEARCH_CONSOLE")
        self.assertEqual(report["clicks"], 7)
        self.assertEqual(report["impressions"], 100)
        self.assertEqual(report["ctr_percent"], "7.00")
        self.assertEqual(report["average_position"], "11.50")
        self.assertEqual(report["top_queries"][0]["query"], "lowcost europa")
        self.assertEqual(len(requested), 2)
        self.assertTrue(all("select_accounts=sc-domain%3Alowcost-europa.eu" in url for url in requested))
        self.assertTrue(all("api_key=test-only-secret" in url for url in requested))
        self.assertEqual((end - start).days, 30)

    def test_missing_api_permission_never_yields_fictional_zero(self):
        with self.assertRaises(SearchConsoleNotConfigured):
            collect_search_console_report(api_key="test-only", property_id="sc-domain:other.example")
        with patch.dict("os.environ", {"WINDSOR_API_KEY": "", "GOOGLE_SEARCH_CONSOLE_PROPERTY": ""}):
            with self.assertRaises(SearchConsoleNotConfigured):
                collect_search_console_report()

    def test_provider_empty_summary_is_unavailable_not_zero(self):
        with self.assertRaises(SearchConsoleReportError):
            collect_search_console_report(
                api_key="test-only", property_id=EXPECTED_PROPERTY,
                opener=lambda req, timeout: _FakeResponse([]),
            )

    def test_wrong_site_data_is_rejected(self):
        with self.assertRaisesRegex(SearchConsoleReportError, "property_mismatch"):
            collect_search_console_report(
                api_key="test-only", property_id=EXPECTED_PROPERTY,
                opener=lambda req, timeout: _FakeResponse([{
                    "account_id": "sc-domain:unrelated.example",
                    "clicks": 500,
                    "impressions": 800,
                    "position": 2.2,
                }]),
            )

    def test_invalid_incomplete_provider_data_rejected(self):
        with self.assertRaisesRegex(SearchConsoleReportError, "invalid_clicks"):
            collect_search_console_report(
                api_key="test-only", property_id=EXPECTED_PROPERTY,
                opener=lambda req, timeout: _FakeResponse([{
                    "account_id": EXPECTED_PROPERTY,
                    "clicks": None,
                    "impressions": 12,
                    "position": 9,
                }]),
            )

    def test_provider_auth_exception_does_not_expose_secret(self):
        def deny(req, timeout):
            raise HTTPError(req.full_url, 403, "denied", {}, None)

        with self.assertRaises(SearchConsoleReportError) as result:
            collect_search_console_report(
                api_key="very-private-token",
                property_id=EXPECTED_PROPERTY,
                opener=deny,
            )
        self.assertNotIn("very-private-token", str(result.exception))


class SearchConsoleSnapshotCommandTests(TestCase):
    def test_real_response_is_saved_as_private_snapshot(self):
        now = timezone.now()
        sample = {
            "property": EXPECTED_PROPERTY,
            "source": "GOOGLE_SEARCH_CONSOLE",
            "provider": "WINDSOR",
            "days": 30,
            "clicks": 4,
            "impressions": 70,
            "ctr_percent": "5.71",
            "average_position": "13.20",
            "top_queries": [],
        }
        with patch(
            "apps.catalog.management.commands.sync_google_search_console.collect_search_console_report",
            return_value=(sample, now - timedelta(days=30), now)
        ):
            call_command("sync_google_search_console")
        stored = ExternalMetricsSnapshot.objects.get(source="GOOGLE_SEARCH_CONSOLE")
        self.assertEqual(stored.payload["clicks"], 4)
        self.assertEqual(stored.payload["property"], EXPECTED_PROPERTY)

    def test_dry_run_does_not_modify_snapshot(self):
        now = timezone.now()
        with patch(
            "apps.catalog.management.commands.sync_google_search_console.collect_search_console_report",
            return_value=(
                {"property": EXPECTED_PROPERTY, "clicks": 2, "impressions": 10},
                now - timedelta(days=30), now
            )
        ):
            call_command("sync_google_search_console", "--dry-run")
        self.assertFalse(
            ExternalMetricsSnapshot.objects.filter(source="GOOGLE_SEARCH_CONSOLE").exists()
        )
