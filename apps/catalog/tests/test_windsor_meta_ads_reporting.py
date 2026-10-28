"""Windsor provider tests: exact account, read-only, absent access and no fake orders."""

import json
from contextlib import nullcontext
from datetime import datetime, timedelta
from datetime import timezone as datetime_timezone
from types import SimpleNamespace
from urllib import parse
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.catalog.services.meta_ads_reporting import MetaAdsNotConfigured, MetaAdsReportError
from apps.catalog.services.windsor_meta_ads_reporting import collect_windsor_meta_ads_report

NOW = datetime(2026, 10, 28, 16, tzinfo=datetime_timezone.utc)
ACCOUNT = "111222333"
KEY = "fake-test-api-key-never-a-real-secret"


def respond(*payloads, calls=None):
    queue = iter(payloads)

    def opener(req, timeout):
        if calls is not None:
            calls.append(req)
        response = SimpleNamespace(
            status=200,
            read=lambda _max_bytes: json.dumps(next(queue)).encode("utf-8"),
        )
        return nullcontext(response)

    return opener


ACCOUNT_ROW = {
    "account_id": ACCOUNT,
    "account_name": "LOW COST",
    "account_currency": "EUR",
    "account_status": "ACTIVE",
}


class WindsorMetaReportingTests(SimpleTestCase):
    def test_missing_key_is_not_a_verified_zero(self):
        with self.assertRaises(MetaAdsNotConfigured):
            collect_windsor_meta_ads_report(
                now=NOW, account_id=ACCOUNT, api_key=""
            )

    def test_valid_report_scoped_to_one_account_and_https_only(self):
        calls = []
        opener = respond(
            [ACCOUNT_ROW],
            [
                {
                    "account_id": ACCOUNT,
                    "spend": 12.34,
                    "impressions": 543,
                    "clicks": 20,
                    "reach": 432,
                    "actions_link_click": 9,
                }
            ],
            calls=calls,
        )
        report, begin, end = collect_windsor_meta_ads_report(
            now=NOW, opener=opener, account_id=ACCOUNT, api_key=KEY
        )
        self.assertEqual(report["provider"], "WINDSOR")
        self.assertEqual(report["spend"], "12.34")
        self.assertEqual(report["clicks"], 20)
        self.assertEqual(report["link_clicks"], 9)
        self.assertEqual(report["currency"], "EUR")
        self.assertEqual(begin, NOW - timedelta(days=30))
        self.assertEqual(end, NOW)
        self.assertEqual(len(calls), 2)
        for req in calls:
            parsed = parse.urlsplit(req.full_url)
            params = parse.parse_qs(parsed.query)
            self.assertEqual(parsed.netloc, "connectors.windsor.ai")
            self.assertEqual(parsed.scheme, "https")
            self.assertEqual(req.get_method(), "GET")
            self.assertEqual(params["select_accounts"], [ACCOUNT])
            self.assertEqual(params["api_key"], [KEY])
        self.assertEqual(
            parse.parse_qs(parse.urlsplit(calls[1].full_url).query)["date_preset"],
            ["last_30d"],
        )

    def test_empty_insights_requires_verified_account_to_report_zero(self):
        opener = respond([ACCOUNT_ROW], [])
        report, _, _ = collect_windsor_meta_ads_report(
            now=NOW, account_id=ACCOUNT, api_key=KEY, opener=opener
        )
        self.assertEqual(report["spend"], "0.00")
        self.assertEqual(report["clicks"], 0)
        self.assertIsNone(report["link_clicks"])

    def test_missing_account_cannot_be_misclassified_as_no_activity(self):
        opener = respond([], [])
        with self.assertRaisesRegex(MetaAdsReportError, "identity_mismatch"):
            collect_windsor_meta_ads_report(
                now=NOW, account_id=ACCOUNT, api_key=KEY, opener=opener
            )

    def test_cross_account_metrics_never_enter_snapshot(self):
        opener = respond(
            [ACCOUNT_ROW],
            [{"account_id": "444555666", "spend": "1.00"}],
        )
        with self.assertRaisesRegex(MetaAdsReportError, "account_mismatch"):
            collect_windsor_meta_ads_report(
                now=NOW, account_id=ACCOUNT, api_key=KEY, opener=opener
            )

    def test_incomplete_metric_rows_fail_closed(self):
        opener = respond([ACCOUNT_ROW], [{"account_id": ACCOUNT, "spend": 10}])
        with self.assertRaisesRegex(MetaAdsReportError, "incomplete"):
            collect_windsor_meta_ads_report(
                now=NOW, account_id=ACCOUNT, api_key=KEY, opener=opener
            )

    def test_provider_failure_is_not_reflected_back_with_token(self):
        opener = respond(
            {"error": "This error might contain a credential (test only)"},
        )
        with self.assertRaisesRegex(MetaAdsReportError, "provider_unavailable") as ctx:
            collect_windsor_meta_ads_report(
                now=NOW, account_id=ACCOUNT, api_key=KEY, opener=opener
            )
        self.assertNotIn(KEY, str(ctx.exception))

    def test_async_pending_response_is_not_success(self):
        opener = respond({"status": "pending"})
        with self.assertRaisesRegex(MetaAdsReportError, "provider_unavailable"):
            collect_windsor_meta_ads_report(
                now=NOW, account_id=ACCOUNT, api_key=KEY, opener=opener
            )
