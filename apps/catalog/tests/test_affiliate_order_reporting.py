"""Provider order summaries are exact, privacy-minimal and fail closed."""

from datetime import datetime, timedelta
from datetime import timezone as datetime_timezone
from io import StringIO
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.catalog.models import ExternalMetricsSnapshot
from apps.catalog.services.affiliate_order_reporting import (
    AffiliateOrderReportError,
    collect_affiliate_order_report,
)

UTC = datetime_timezone.utc
NOW = datetime(2026, 10, 28, 16, 0, tzinfo=UTC)


def provider_result(rows, *, pages=1, code=200, message="success"):
    result = {"total_page_no": pages, "orders": {"order": rows}}
    return {
        "aliexpress_affiliate_order_list_response": {
            "resp_result": {
                "resp_code": code,
                "resp_msg": message,
                **({"result": result} if code == 200 else {}),
            }
        }
    }


def order(parent, child, tracking, status, value, currency="USD", effect=""):
    return {
        "order_id": parent,
        "sub_order_id": child,
        "tracking_id": tracking,
        "order_status": status,
        "effect_detail_status": effect,
        "estimated_paid_commission": value,
        "estimated_finished_commission": value,
        "settled_currency": currency,
        "product_title": "PRIVATE: must never be stored in the summary",
    }


class AffiliateOrderReportingTests(TestCase):
    def test_405_with_provider_empty_message_is_valid_empty_window(self):
        empty = provider_result([], code=405, message="The result is empty")
        client = Mock()
        client._call.side_effect = [empty, empty]

        summary, start, end = collect_affiliate_order_report(client=client, now=NOW)

        self.assertEqual(client._call.call_count, 2)
        self.assertEqual(summary["paid_count"], 0)
        self.assertEqual(summary["received_count"], 0)
        self.assertEqual(start, NOW - timedelta(days=30))
        self.assertEqual(end, NOW)
        self.assertEqual(
            [item["tracking_id"] for item in summary["by_tracking"]],
            ["lowcost_europa", "default", "meus_links", "outros"],
        )
        self.assertFalse(any("PRIVATE" in str(item) for item in summary["by_tracking"]))
        query = client._call.call_args_list[0]
        self.assertEqual(query.args[0], "aliexpress.affiliate.order.list")
        self.assertEqual(query.args[1]["status"], "Payment Completed")
        self.assertEqual(query.args[1]["page_no"], 1)

    def test_purchases_refunds_and_currency_are_never_mixed(self):
        pay = provider_result([
            order("parent-1", "child-1", "lowcost_europa", "Payment Completed", 1234),
            order("parent-2", "child-2", "default", "Payment Completed", "1.50", "EUR"),
            order("parent-3", "child-3", "meus_links", "Payment Completed", 250,
                  effect="FullRefund"),
            order("parent-4", "child-4", "old_tracking", "Payment Completed", 200),
        ])
        confirmed = provider_result([
            order("parent-1", "child-1", "lowcost_europa", "Buyer Confirmed Receipt", 777),
            order("parent-5", "child-5", "meus_links", "Buyer Confirmed Receipt", 123),
        ])
        client = Mock()
        client._call.side_effect = [pay, confirmed]
        report, _, _ = collect_affiliate_order_report(client=client, now=NOW)

        self.assertEqual(report["paid_count"], 2)
        self.assertEqual(report["received_count"], 2)
        self.assertEqual(report["excluded_count"], 1)
        self.assertNotIn("PRIVATE", str(report))
        tracking = {row["tracking_id"]: row for row in report["by_tracking"]}
        self.assertEqual(tracking["default"]["paid_count"], 1)
        self.assertEqual(
            tracking["default"]["estimated_paid"],
            [{"currency": "EUR", "amount": "1.50"}],
        )
        self.assertEqual(tracking["lowcost_europa"]["paid_count"], 0)
        self.assertEqual(tracking["lowcost_europa"]["received_count"], 1)
        self.assertEqual(
            tracking["lowcost_europa"]["estimated_finished"],
            [{"currency": "USD", "amount": "7.77"}],
        )
        self.assertEqual(tracking["outros"]["paid_count"], 1)
        self.assertEqual(tracking["meus_links"]["received_count"], 1)

    def test_unknown_405_must_not_be_reported_as_zero_sales(self):
        client = Mock()
        client._call.return_value = provider_result([], code=405, message="Access forbidden")
        with self.assertRaisesRegex(AffiliateOrderReportError, "ambiguous_empty_result"):
            collect_affiliate_order_report(client=client, now=NOW)

    def test_error_on_malformed_orders_prevents_partial_snapshot(self):
        client = Mock()
        client._call.return_value = provider_result(
            [{"tracking_id": "lowcost_europa"}]
        )
        with self.assertRaisesRegex(AffiliateOrderReportError, "missing_order_identity"):
            collect_affiliate_order_report(client=client, now=NOW)

    def test_pagination_does_not_silently_truncate(self):
        first_page = [
            order(f"parent-{n}", f"child-{n}", "lowcost_europa", "Payment Completed", 100)
            for n in range(50)
        ]
        second_page = [order("parent-50", "child-50", "default", "Payment Completed", 100)]
        client = Mock()
        client._call.side_effect = [
            provider_result(first_page, pages=2),
            provider_result(second_page, pages=2),
            provider_result([], code=405, message="The result is empty"),
        ]
        report, _, _ = collect_affiliate_order_report(client=client, now=NOW)
        self.assertEqual(report["paid_count"], 51)
        self.assertEqual(client._call.call_count, 3)
        self.assertEqual(client._call.call_args_list[1].args[1]["page_no"], 2)

    def test_missing_monetary_value_is_not_an_estimated_zero(self):
        client = Mock()
        row = order("parent", "child", "lowcost_europa", "Payment Completed", 100)
        row.pop("estimated_paid_commission")
        client._call.side_effect = [
            provider_result([row]),
            provider_result([], code=405, message="The result is empty"),
        ]
        report, _, _ = collect_affiliate_order_report(client=client, now=NOW)
        self.assertEqual(report["paid_count"], 1)
        self.assertEqual(report["missing_commission_count"], 1)
        self.assertEqual(report["by_tracking"][0]["estimated_paid"], [])


class AffiliateOrderCommandTests(TestCase):
    def test_dry_run_never_writes_snapshot(self):
        report = {"paid_count": 0, "received_count": 0, "excluded_count": 0}
        with patch(
            "apps.catalog.management.commands.sync_affiliate_orders.collect_affiliate_order_report",
            return_value=(report, NOW - timedelta(days=30), NOW),
        ):
            output = StringIO()
            call_command("sync_affiliate_orders", "--dry-run", stdout=output)
        self.assertIn("DRY_RUN_PASS", output.getvalue())
        self.assertEqual(ExternalMetricsSnapshot.objects.count(), 0)

    def test_verified_report_upserts_snapshot_idempotently(self):
        report = {"paid_count": 1, "received_count": 0, "excluded_count": 0}
        with patch(
            "apps.catalog.management.commands.sync_affiliate_orders.collect_affiliate_order_report",
            return_value=(report, NOW - timedelta(days=30), NOW),
        ):
            call_command("sync_affiliate_orders", stdout=StringIO())
            call_command("sync_affiliate_orders", stdout=StringIO())
        self.assertEqual(ExternalMetricsSnapshot.objects.count(), 1)
        self.assertEqual(
            ExternalMetricsSnapshot.objects.get(source="ALIEXPRESS").payload["paid_count"], 1
        )

    def test_failed_refresh_keeps_last_successful_snapshot(self):
        saved = ExternalMetricsSnapshot.objects.create(
            source="ALIEXPRESS",
            period_start=NOW - timedelta(days=30),
            period_end=NOW,
            checked_at=NOW,
            payload={"paid_count": 2},
        )
        with patch(
            "apps.catalog.management.commands.sync_affiliate_orders.collect_affiliate_order_report",
            side_effect=AffiliateOrderReportError("unexpected provider data"),
        ):
            with self.assertRaises(CommandError):
                call_command("sync_affiliate_orders", stdout=StringIO())
        saved.refresh_from_db()
        self.assertEqual(saved.payload, {"paid_count": 2})
