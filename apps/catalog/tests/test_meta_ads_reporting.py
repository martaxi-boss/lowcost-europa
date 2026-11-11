"""No paid marketing connector is needed to count site traffic or affiliate orders."""

import os
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.catalog.models import ExternalMetricsSnapshot


class LocalMarketingCountersTests(TestCase):
    def test_old_meta_account_reporting_is_disabled(self):
        with patch.dict(os.environ, {
            "META_ACCESS_TOKEN": "historical-test-token",
            "META_AD_ACCOUNT_ID": "000000",
        }):
            with self.assertRaisesRegex(CommandError, "META_REPORT=DISABLED_BY_OWNER"):
                call_command("sync_meta_ads", stdout=StringIO())
        self.assertFalse(ExternalMetricsSnapshot.objects.filter(source="META").exists())

    def test_periodic_sync_calls_aliexpress_only_without_google_accounts(self):
        stdout = StringIO()
        with (
            patch.dict(os.environ, {
                "META_ACCESS_TOKEN": "unused",
                "GOOGLE_SEARCH_CONSOLE_PROPERTY": "sc-domain:lowcost-europa.eu",
                "GOOGLE_OAUTH_CLIENT_ID": "unused",
                "GOOGLE_OAUTH_REFRESH_TOKEN": "unused",
            }),
            patch(
                "apps.catalog.management.commands.sync_external_metrics.call_command"
            ) as api,
        ):
            call_command("sync_external_metrics", "--dry-run", stdout=stdout)
        self.assertEqual(
            [call.args[0] for call in api.call_args_list],
            ["sync_affiliate_orders"],
        )
        self.assertIn("VISITOR_ORIGINS=PRIVATE_NGINX_COUNTER_ONLY", stdout.getvalue())

    def test_aliexpress_failure_is_reported_without_disabling_local_counter(self):
        calls = []
        def provider(name, *args):
            calls.append(name)
            raise CommandError("test-only affiliate outage")
        with patch(
            "apps.catalog.management.commands.sync_external_metrics.call_command",
            side_effect=provider,
        ):
            with self.assertRaisesRegex(CommandError, "EXTERNAL_METRICS_FAILED=ALIEXPRESS"):
                call_command("sync_external_metrics", stderr=StringIO())
        self.assertEqual(calls, ["sync_affiliate_orders"])
