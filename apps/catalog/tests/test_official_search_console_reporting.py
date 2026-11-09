"""Official GSC API tests: verified metrics, privacy, failure and free fallback."""

import json
import os
from datetime import datetime, timezone as dt_timezone
from io import StringIO
from unittest.mock import patch
from urllib.error import HTTPError

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.catalog.models import ExternalMetricsSnapshot
from apps.catalog.services.official_search_console_reporting import (
    collect_official_search_console_report,
)
from apps.catalog.services.windsor_search_console_reporting import (
    EXPECTED_PROPERTY,
    SearchConsoleAwaitingData,
    SearchConsoleNotConfigured,
    SearchConsoleReportError,
)

CLIENT = {
    "property_id": EXPECTED_PROPERTY,
    "client_id": "client-test",
    "client_secret": "private-secret-test",
    "refresh_token": "private-refresh-test",
}


class _Response:
    status = 200

    def __init__(self, value):
        self.body = json.dumps(value).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        return False

    def read(self, size):
        return self.body[:size]


def _opener(request, timeout):
    if request.full_url.endswith("/token"):
        return _Response({"access_token": "temporary-test", "token_type": "Bearer"})
    data = json.loads(request.data)
    if data["dimensions"] == []:
        return _Response({"rows": [{
            "clicks": 8.0, "impressions": 100.0, "ctr": 0.08, "position": 11.234
        }]})
    return _Response({"rows": [
        {"keys": ["equipamento profissional"], "clicks": 4.0, "impressions": 24.0},
        {"keys": ["lowcost europa"], "clicks": 2.0, "impressions": 12.0},
    ]})


class OfficialSearchConsoleTests(SimpleTestCase):
    def test_no_oauth_credentials_or_wrong_property_rejected(self):
        with self.assertRaises(SearchConsoleNotConfigured):
            collect_official_search_console_report(
                **{**CLIENT, "property_id": "sc-domain:other.example"}, opener=_opener
            )
        with patch.dict(os.environ, {
            "GOOGLE_SEARCH_CONSOLE_PROPERTY": EXPECTED_PROPERTY,
            "GOOGLE_OAUTH_CLIENT_ID": "", "GOOGLE_OAUTH_CLIENT_SECRET": "",
            "GOOGLE_OAUTH_REFRESH_TOKEN": "",
        }):
            with self.assertRaises(SearchConsoleNotConfigured):
                collect_official_search_console_report(opener=_opener)

    def test_aggregate_is_factual_and_only_fixed_readonly_property(self):
        requests = []

        def record(req, timeout):
            requests.append(req)
            return _opener(req, timeout)

        now = datetime(2026, 11, 9, 12, 0, tzinfo=dt_timezone.utc)
        report, first, last = collect_official_search_console_report(
            **CLIENT, now=now, opener=record
        )
        self.assertEqual(report["provider"], "GOOGLE_OFFICIAL")
        self.assertEqual(report["property"], EXPECTED_PROPERTY)
        self.assertEqual(report["clicks"], 8)
        self.assertEqual(report["impressions"], 100)
        self.assertEqual(report["ctr_percent"], "8.00")
        self.assertEqual(report["average_position"], "11.23")
        self.assertEqual(report["top_queries"][0]["query"], "equipamento profissional")
        self.assertEqual(first.date().isoformat(), "2026-10-08")
        self.assertEqual(last.date().isoformat(), "2026-11-06")
        self.assertEqual(len(requests), 3)
        self.assertTrue(all(req.get_method() == "POST" for req in requests))
        self.assertEqual(requests[0].full_url, "https://oauth2.googleapis.com/token")
        self.assertTrue(all(
            "sc-domain%3Alowcost-europa.eu" in req.full_url
            for req in requests[1:]
        ))
        self.assertEqual(
            json.loads(requests[1].data)["dimensions"], []
        )
        self.assertEqual(
            json.loads(requests[2].data)["dimensions"], ["query"]
        )
        self.assertIn("Bearer temporary-test", requests[1].headers.values())
        self.assertNotIn("private-secret-test", requests[1].full_url)
        self.assertNotIn("private-refresh-test", requests[1].full_url)

    def test_empty_provider_is_awaiting_not_zero(self):
        def empty(req, timeout):
            if req.full_url.endswith("/token"):
                return _Response({"access_token": "token"})
            return _Response({"rows": []})

        with self.assertRaises(SearchConsoleAwaitingData):
            collect_official_search_console_report(**CLIENT, opener=empty)

    def test_invalid_totals_and_query_rejected(self):
        def invalid(req, timeout):
            if req.full_url.endswith("/token"):
                return _Response({"access_token": "token"})
            body = json.loads(req.data)
            if body["dimensions"] == []:
                return _Response({"rows": [
                    {"clicks": 7, "impressions": 3, "position": 4}
                ]})
            return _Response({"rows": []})

        with self.assertRaisesRegex(SearchConsoleReportError, "exceed"):
            collect_official_search_console_report(**CLIENT, opener=invalid)

    def test_google_authorization_error_never_exposes_refresh_secret(self):
        def reject(req, timeout):
            raise HTTPError(req.full_url, 401, "token rejected", {}, None)

        with self.assertRaises(SearchConsoleReportError) as caught:
            collect_official_search_console_report(**CLIENT, opener=reject)
        self.assertNotIn(CLIENT["client_secret"], str(caught.exception))
        self.assertNotIn(CLIENT["refresh_token"], str(caught.exception))

    def test_successful_oauth_with_invalid_token_cannot_call_api(self):
        with self.assertRaisesRegex(SearchConsoleReportError, "invalid_token"):
            collect_official_search_console_report(
                **CLIENT,
                opener=lambda req, timeout: _Response({
                    "access_token": "", "token_type": "Bearer"
                })
            )


class OfficialSearchConsoleCommandTests(TestCase):
    def test_official_provider_dry_run_no_database_write(self):
        with patch.dict(os.environ, {"GOOGLE_SEARCH_CONSOLE_PROVIDER": "GOOGLE_OFFICIAL"}):
            with patch(
                "apps.catalog.management.commands.sync_google_search_console."
                "collect_official_search_console_report",
                return_value=(
                    {"source": "GOOGLE_SEARCH_CONSOLE", "provider": "GOOGLE_OFFICIAL",
                     "property": EXPECTED_PROPERTY, "clicks": 8},
                    datetime(2026, 10, 8, tzinfo=dt_timezone.utc),
                    datetime(2026, 11, 6, tzinfo=dt_timezone.utc),
                ),
            ) as official:
                call_command("sync_google_search_console", "--dry-run", stdout=StringIO())
        self.assertEqual(official.call_count, 1)
        self.assertFalse(ExternalMetricsSnapshot.objects.exists())

    def test_owner_panel_identifies_configured_free_provider(self):
        owner = get_user_model().objects.create_user(
            username="official-gsc-owner", password="test-only", is_staff=True
        )
        self.client.force_login(owner)
        env = {
            "GOOGLE_SEARCH_CONSOLE_PROVIDER": "GOOGLE_OFFICIAL",
            "GOOGLE_SEARCH_CONSOLE_PROPERTY": EXPECTED_PROPERTY,
            "GOOGLE_OAUTH_CLIENT_ID": "id", "GOOGLE_OAUTH_CLIENT_SECRET": "secret",
            "GOOGLE_OAUTH_REFRESH_TOKEN": "refresh", "WINDSOR_API_KEY": "",
        }
        with patch.dict(os.environ, env):
            response = self.client.get(reverse("owner-panel:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["google_search_configured"])
        self.assertFalse(response.context["google_search_report_payload"])
        self.assertContains(response, "Leitura configurada — a aguardar dados")
