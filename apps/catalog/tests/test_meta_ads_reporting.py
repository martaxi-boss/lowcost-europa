"""Regression tests for the owner's explicit Meta reporting disconnection."""

import os
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.catalog.models import ExternalMetricsSnapshot


class MetaDisconnectedTests(TestCase):
    def test_manual_meta_sync_is_disabled_despite_legacy_credentials(self):
        with patch.dict(
            os.environ,
            {
                "META_ACCESS_TOKEN": "historical-test-token",
                "META_AD_ACCOUNT_ID": "000000",
            },
        ):
            with self.assertRaisesRegex(CommandError, "META_REPORT=DISABLED_BY_OWNER"):
                call_command("sync_meta_ads", stdout=StringIO())
        self.assertFalse(ExternalMetricsSnapshot.objects.filter(source="META").exists())

    def test_combined_sync_does_not_use_meta_but_preserves_google(self):
        with (
            patch.dict(
                os.environ,
                {
                    "META_ACCESS_TOKEN": "historical-test-token",
                    "META_AD_ACCOUNT_ID": "000000",
                        "GOOGLE_SEARCH_CONSOLE_PROVIDER": "GOOGLE_OFFICIAL",
                    "GOOGLE_SEARCH_CONSOLE_PROPERTY": "sc-domain:lowcost-europa.eu",
                    "GOOGLE_OAUTH_CLIENT_ID": "test-id",
                    "GOOGLE_OAUTH_CLIENT_SECRET": "test-secret",
                    "GOOGLE_OAUTH_REFRESH_TOKEN": "test-refresh",
                },
            ),
            patch(
                "apps.catalog.management.commands.sync_external_metrics.call_command"
            ) as provider,
        ):
            call_command("sync_external_metrics", "--dry-run", stdout=StringIO())
        self.assertEqual(
            [item.args[0] for item in provider.call_args_list],
            ["sync_affiliate_orders", "sync_google_search_console"],
        )

    def test_google_sync_survives_aliexpress_failure_with_no_meta(self):
        calls = []

        def provider(name, *args):
            calls.append(name)
            if name == "sync_affiliate_orders":
                raise CommandError("test-only temporary error")

        with (
            patch.dict(
                os.environ,
                {
                    "META_ACCESS_TOKEN": "historical-test-token",
                    "META_AD_ACCOUNT_ID": "000000",
                        "GOOGLE_SEARCH_CONSOLE_PROVIDER": "GOOGLE_OFFICIAL",
                    "GOOGLE_SEARCH_CONSOLE_PROPERTY": "sc-domain:lowcost-europa.eu",
                    "GOOGLE_OAUTH_CLIENT_ID": "test-id",
                    "GOOGLE_OAUTH_CLIENT_SECRET": "test-secret",
                    "GOOGLE_OAUTH_REFRESH_TOKEN": "test-refresh",
                },
            ),
            patch(
                "apps.catalog.management.commands.sync_external_metrics.call_command",
                side_effect=provider,
            ),
        ):
            with self.assertRaisesRegex(CommandError, "EXTERNAL_METRICS_FAILED=ALIEXPRESS"):
                call_command("sync_external_metrics", stderr=StringIO())
        self.assertEqual(calls, ["sync_affiliate_orders", "sync_google_search_console"])

    def test_google_error_does_not_reconnect_meta(self):
        calls = []

        def provider(name, *args):
            calls.append(name)
            if name == "sync_google_search_console":
                raise CommandError("test-only Google unavailable")

        with (
            patch.dict(
                os.environ,
                {
                        "GOOGLE_SEARCH_CONSOLE_PROVIDER": "GOOGLE_OFFICIAL",
                    "GOOGLE_SEARCH_CONSOLE_PROPERTY": "sc-domain:lowcost-europa.eu",
                    "GOOGLE_OAUTH_CLIENT_ID": "test-id",
                    "GOOGLE_OAUTH_CLIENT_SECRET": "test-secret",
                    "GOOGLE_OAUTH_REFRESH_TOKEN": "test-refresh",
                },
            ),
            patch(
                "apps.catalog.management.commands.sync_external_metrics.call_command",
                side_effect=provider,
            ),
        ):
            with self.assertRaisesRegex(
                CommandError, "EXTERNAL_METRICS_FAILED=GOOGLE_SEARCH"
            ):
                call_command("sync_external_metrics", stderr=StringIO())
        self.assertEqual(calls, ["sync_affiliate_orders", "sync_google_search_console"])
