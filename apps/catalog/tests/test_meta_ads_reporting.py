"""Meta reporting is read-only, account scoped, and truthful on missing access."""

import json
import os
from contextlib import nullcontext
from datetime import datetime, timedelta
from datetime import timezone as datetime_timezone
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.catalog.models import ExternalMetricsSnapshot
from apps.catalog.services.meta_ads_reporting import (
    MetaAdsNotConfigured,
    MetaAdsReportError,
    collect_meta_ads_report,
)

NOW = datetime(2026, 10, 28, 16, 0, tzinfo=datetime_timezone.utc)
ACCOUNT = "3406762302806854"
TOKEN = "private-test-token-not-real"


def opener_responses(*payloads, calls=None):
    queue = iter(payloads)

    def opener(req, timeout):
        if calls is not None:
            calls.append(req)
        payload = next(queue)
        data = json.dumps(payload).encode("utf-8")
        return nullcontext(SimpleNamespace(status=200, read=lambda: data))

    return opener


class MetaAdsReportTests(TestCase):
    def test_unauthorized_missing_token_fails_closed(self):
        with patch.dict(os.environ, {"META_AD_ACCOUNT_ID": "", "META_ACCESS_TOKEN": ""}):
            with self.assertRaises(MetaAdsNotConfigured):
                collect_meta_ads_report(now=NOW)

    def test_one_account_and_one_insights_request_without_token_in_url(self):
        calls = []
        opener = opener_responses(
            {"id": "act_" + ACCOUNT, "name": "LOW COST", "currency": "EUR"},
            {"data": [{
                "spend": "23.44",
                "impressions": "1500",
                "clicks": "22",
                "reach": "900",
                "inline_link_clicks": "10",
            }]},
            calls=calls,
        )
        report, begin, end = collect_meta_ads_report(
            now=NOW, opener=opener, account_id=ACCOUNT, token=TOKEN
        )
        self.assertEqual(report["spend"], "23.44")
        self.assertEqual(report["currency"], "EUR")
        self.assertEqual(report["clicks"], 22)
        self.assertEqual(report["link_clicks"], 10)
        self.assertEqual(report["impressions"], 1500)
        self.assertEqual(begin, NOW - timedelta(days=30))
        self.assertEqual(end, NOW)
        self.assertEqual(len(calls), 2)
        for call in calls:
            self.assertNotIn(TOKEN, call.full_url)
            self.assertEqual(call.get_header("Authorization"), "Bearer " + TOKEN)
            self.assertEqual(call.get_method(), "GET")
        self.assertIn("/act_" + ACCOUNT + "/insights?", calls[1].full_url)

    def test_account_mismatch_and_provider_error_never_emit_metrics(self):
        opener = opener_responses({"id": "act_999", "currency": "EUR"})
        with self.assertRaisesRegex(MetaAdsReportError, "account_identity_mismatch"):
            collect_meta_ads_report(
                now=NOW, opener=opener, account_id=ACCOUNT, token=TOKEN
            )
        opener = opener_responses({"error": {"message": "test token is not valid"}})
        with self.assertRaisesRegex(MetaAdsReportError, "meta_error_response"):
            collect_meta_ads_report(
                now=NOW, opener=opener, account_id=ACCOUNT, token=TOKEN
            )

    def test_valid_empty_insights_is_verified_zero_not_unknown(self):
        opener = opener_responses(
            {"id": "act_" + ACCOUNT, "name": "LOW COST", "currency": "EUR"},
            {"data": []},
        )
        report, _, _ = collect_meta_ads_report(
            now=NOW, opener=opener, account_id=ACCOUNT, token=TOKEN
        )
        self.assertEqual(report["spend"], "0.00")
        self.assertEqual(report["clicks"], 0)
        self.assertIsNone(report["link_clicks"])


class MetaCommandTests(TestCase):
    def test_meta_snapshot_written_idempotently_only_when_verified(self):
        result = {"spend": "15.00", "clicks": 3}
        with patch(
            "apps.catalog.management.commands.sync_meta_ads.collect_meta_ads_report",
            return_value=(result, NOW - timedelta(days=30), NOW),
        ):
            call_command("sync_meta_ads", stdout=StringIO())
            call_command("sync_meta_ads", stdout=StringIO())
        saved = ExternalMetricsSnapshot.objects.get(source="META")
        self.assertEqual(saved.payload["spend"], "15.00")
        self.assertEqual(ExternalMetricsSnapshot.objects.count(), 1)

    def test_failed_meta_sync_does_not_overwrite_previous_data(self):
        ExternalMetricsSnapshot.objects.create(
            source="META",
            period_start=NOW - timedelta(days=30),
            period_end=NOW,
            checked_at=NOW,
            payload={"spend": "19.00"},
        )
        with patch(
            "apps.catalog.management.commands.sync_meta_ads.collect_meta_ads_report",
            side_effect=MetaAdsReportError("token expired"),
        ):
            with self.assertRaises(CommandError):
                call_command("sync_meta_ads", stdout=StringIO())
        self.assertEqual(
            ExternalMetricsSnapshot.objects.get(source="META").payload["spend"], "19.00"
        )

    def test_combined_sync_skips_meta_without_vps_credential(self):
        with (
            patch.dict(os.environ, {"META_ACCESS_TOKEN": "", "META_AD_ACCOUNT_ID": ""}),
            patch(
                "apps.catalog.management.commands.sync_external_metrics.call_command"
            ) as child_command,
        ):
            call_command("sync_external_metrics", "--dry-run", stdout=StringIO())
        self.assertEqual(child_command.call_count, 1)
        self.assertEqual(child_command.call_args.args[0], "sync_affiliate_orders")

    def test_partial_meta_configuration_is_rejected(self):
        with (
            patch.dict(
                os.environ, {"META_ACCESS_TOKEN": "test-only", "META_AD_ACCOUNT_ID": ""}
            ),
            patch("apps.catalog.management.commands.sync_external_metrics.call_command"),
        ):
            with self.assertRaises(CommandError):
                call_command("sync_external_metrics", stdout=StringIO())
