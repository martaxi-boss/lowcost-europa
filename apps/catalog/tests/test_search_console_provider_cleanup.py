"""No legacy provider runtime; official-only reporting, safe OAuth pending state."""

import os
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import ExternalMetricsSnapshot
from apps.catalog.services.search_console_metrics import EXPECTED_PROPERTY


class OfficialProviderCleanupTests(TestCase):
    def _environment(self, *, authorized=False):
        return {
            "GOOGLE_SEARCH_CONSOLE_PROVIDER": "GOOGLE_OFFICIAL",
            "GOOGLE_SEARCH_CONSOLE_PROPERTY": EXPECTED_PROPERTY,
            "GOOGLE_OAUTH_CLIENT_ID": "test-id" if authorized else "",
            "GOOGLE_OAUTH_CLIENT_SECRET": "test-secret" if authorized else "",
            "GOOGLE_OAUTH_REFRESH_TOKEN": "test-refresh" if authorized else "",
        }

    def test_missing_google_oauth_never_calls_official_api_or_overwrites_legacy(self):
        now = timezone.now()
        original = {
            "provider": "WINDSOR",
            "property": EXPECTED_PROPERTY,
            "clicks": 3,
            "impressions": 8,
        }
        ExternalMetricsSnapshot.objects.create(
            source="GOOGLE_SEARCH_CONSOLE",
            period_start=now - timedelta(days=30),
            period_end=now,
            checked_at=now,
            payload=original,
        )
        stdout = StringIO()
        with (
            patch.dict(os.environ, self._environment()),
            patch(
                "apps.catalog.management.commands.sync_google_search_console."
                "collect_official_search_console_report"
            ) as collect,
        ):
            call_command("sync_google_search_console", stdout=stdout)
        collect.assert_not_called()
        self.assertIn("AWAITING_OFFICIAL_OAUTH", stdout.getvalue())
        saved = ExternalMetricsSnapshot.objects.get(source="GOOGLE_SEARCH_CONSOLE")
        self.assertEqual(saved.payload, original)

    def test_combined_sync_still_runs_aliexpress_without_google_authorization(self):
        stdout = StringIO()
        with (
            patch.dict(os.environ, self._environment()),
            patch(
                "apps.catalog.management.commands.sync_external_metrics.call_command"
            ) as internal,
        ):
            call_command("sync_external_metrics", "--dry-run", stdout=stdout)
        self.assertEqual(
            [item.args[0] for item in internal.call_args_list],
            ["sync_affiliate_orders"],
        )
        self.assertIn("GOOGLE_SEARCH_REPORT=AWAITING_OFFICIAL_OAUTH", stdout.getvalue())

    def test_no_hidden_fallback_to_discontinued_provider(self):
        env = self._environment()
        env["GOOGLE_SEARCH_CONSOLE_PROVIDER"] = "WINDSOR"
        with (
            patch.dict(os.environ, env),
            patch(
                "apps.catalog.management.commands.sync_google_search_console."
                "collect_official_search_console_report"
            ) as collect,
        ):
            with self.assertRaisesRegex(CommandError, "UNSUPPORTED_PROVIDER"):
                call_command("sync_google_search_console", stdout=StringIO())
        collect.assert_not_called()

    def test_verified_official_report_replaces_legacy_snapshot_after_authorization(self):
        now = timezone.now()
        ExternalMetricsSnapshot.objects.create(
            source="GOOGLE_SEARCH_CONSOLE",
            period_start=now - timedelta(days=30),
            period_end=now,
            checked_at=now - timedelta(days=3),
            payload={"property": EXPECTED_PROPERTY, "provider": "WINDSOR", "clicks": 2},
        )
        result = {
            "source": "GOOGLE_SEARCH_CONSOLE",
            "provider": "GOOGLE_OFFICIAL",
            "property": EXPECTED_PROPERTY,
            "clicks": 7,
            "impressions": 72,
            "ctr_percent": "9.72",
            "average_position": "11.00",
            "top_queries": [],
        }
        with (
            patch.dict(os.environ, self._environment(authorized=True)),
            patch(
                "apps.catalog.management.commands.sync_google_search_console."
                "collect_official_search_console_report",
                return_value=(result, now - timedelta(days=30), now),
            ),
        ):
            call_command("sync_google_search_console", stdout=StringIO())
        stored = ExternalMetricsSnapshot.objects.get(source="GOOGLE_SEARCH_CONSOLE")
        self.assertEqual(stored.payload, result)
        self.assertEqual(stored.payload["provider"], "GOOGLE_OFFICIAL")
