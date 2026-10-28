"""Read-only AliExpress order report, aggregated without retaining order identifiers."""

from collections import defaultdict
from datetime import timedelta, timezone as datetime_timezone
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from apps.integrations.aliexpress.client import AliExpressClient

ORDER_METHOD = "aliexpress.affiliate.order.list"
ORDER_STATUSES = ("Payment Completed", "Buyer Confirmed Receipt")
TRACKING_IDS = ("lowcost_europa", "default", "meus_links", "outros")
TOP_TIMEZONE = datetime_timezone(timedelta(hours=8))
PAGE_SIZE = 50
MAX_PAGES = 20


class AffiliateOrderReportError(Exception):
    """The provider's data cannot be reported as a complete verified snapshot."""


def _read_page(client, params):
    response = client._call(ORDER_METHOD, params)
    if not isinstance(response, dict):
        raise AffiliateOrderReportError("invalid_provider_response")
    wrapped = response.get("aliexpress_affiliate_order_list_response")
    if not isinstance(wrapped, dict):
        raise AffiliateOrderReportError("unexpected_provider_wrapper")
    body = wrapped.get("resp_result")
    if not isinstance(body, dict):
        raise AffiliateOrderReportError("unexpected_provider_body")

    code = str(body.get("resp_code", ""))
    if code == "405":
        # AliExpress returns a business-level 405 ("The result is empty")
        # for a valid query with no orders. This is not HTTP 405.
        message = str(body.get("resp_msg", "")).lower()
        if "empty" in message or "no result" in message:
            return [], 0
        raise AffiliateOrderReportError("ambiguous_empty_result")
    if code != "200":
        raise AffiliateOrderReportError("provider_report_not_successful")

    result = body.get("result")
    if not isinstance(result, dict):
        raise AffiliateOrderReportError("missing_order_result")
    orders = result.get("orders") or {}
    if not isinstance(orders, dict):
        raise AffiliateOrderReportError("malformed_order_container")
    rows = orders.get("order", [])
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise AffiliateOrderReportError("malformed_order_rows")
    if len(rows) > PAGE_SIZE:
        raise AffiliateOrderReportError("invalid_page_size")
    try:
        page_count = int(result.get("total_page_no") or 0)
    except (TypeError, ValueError) as exc:
        raise AffiliateOrderReportError("invalid_page_count") from exc
    return rows, page_count


def _collect_status(client, status, start_time, end_time):
    collected = []
    for page_no in range(1, MAX_PAGES + 1):
        rows, total_pages = _read_page(
            client,
            {
                "start_time": start_time,
                "end_time": end_time,
                "status": status,
                "page_no": page_no,
                "page_size": PAGE_SIZE,
            },
        )
        collected.extend(rows)
        if total_pages > MAX_PAGES:
            raise AffiliateOrderReportError("report_too_large")
        if total_pages and page_no >= total_pages:
            return collected
        if not total_pages and len(rows) < PAGE_SIZE:
            return collected
        if not rows:
            return collected
    raise AffiliateOrderReportError("incomplete_pagination")


def _money(raw):
    if raw is None or raw == "":
        return None
    if isinstance(raw, bool):
        raise AffiliateOrderReportError("invalid_commission_value")
    try:
        # Provider JSON integer amounts are in cents. Decimal strings are
        # already expressed in whole currency units by the documented SDKs.
        amount = Decimal(raw) / 100 if isinstance(raw, int) else Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise AffiliateOrderReportError("invalid_commission_value") from exc
    if not amount.is_finite():
        raise AffiliateOrderReportError("invalid_commission_value")
    return amount.quantize(Decimal("0.01"))


def _identity(row):
    parent = str(row.get("order_id") or "").strip()
    child = str(row.get("sub_order_id") or "").strip()
    if not parent or not child:
        raise AffiliateOrderReportError("missing_order_identity")
    return parent, child


def collect_affiliate_order_report(*, client=None, days=30, now=None):
    """Fetch a complete bounded window. No database write happens here."""
    if not 1 <= days <= 90:
        raise ValueError("days must be between 1 and 90")
    now = now or timezone.now()
    begin = now - timedelta(days=days)
    start_time = begin.astimezone(TOP_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    end_time = now.astimezone(TOP_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    client = client or AliExpressClient()

    # Each suborder is counted once even when returned in multiple status
    # pages. A confirmed receipt supersedes the payment-stage observation.
    unique = {}
    for status in ORDER_STATUSES:
        rows = _collect_status(client, status, start_time, end_time)
        for row in rows:
            identity = _identity(row)
            current = unique.get(identity)
            if current is None or status == ORDER_STATUSES[-1]:
                unique[identity] = (status, row)

    groups = {
        tracking: {
            "tracking_id": tracking,
            "paid_count": 0,
            "received_count": 0,
            "estimated_paid": defaultdict(Decimal),
            "estimated_finished": defaultdict(Decimal),
        }
        for tracking in TRACKING_IDS
    }
    excluded = 0
    missing_commissions = 0
    for status, row in unique.values():
        effect = str(row.get("effect_detail_status") or "").strip().lower()
        if effect in {"fullrefund", "antispam", "invalid"}:
            excluded += 1
            continue
        tracking = str(row.get("tracking_id") or "").strip()
        tracking = tracking if tracking in TRACKING_IDS[:-1] else "outros"
        group = groups[tracking]
        field = (
            "estimated_finished_commission"
            if status == "Buyer Confirmed Receipt"
            else "estimated_paid_commission"
        )
        amount = _money(row.get(field))
        if status == "Buyer Confirmed Receipt":
            group["received_count"] += 1
            bucket = group["estimated_finished"]
        else:
            group["paid_count"] += 1
            bucket = group["estimated_paid"]
        if amount is None:
            missing_commissions += 1
            continue
        currency = str(row.get("settled_currency") or "").strip().upper()
        if len(currency) != 3 or not currency.isascii() or not currency.isalpha():
            raise AffiliateOrderReportError("invalid_settlement_currency")
        bucket[currency] += amount

    by_tracking = []
    for key, group in groups.items():
        by_tracking.append(
            {
                "tracking_id": key,
                "paid_count": group["paid_count"],
                "received_count": group["received_count"],
                "estimated_paid": [
                    {"currency": currency, "amount": str(value)}
                    for currency, value in sorted(group["estimated_paid"].items())
                ],
                "estimated_finished": [
                    {"currency": currency, "amount": str(value)}
                    for currency, value in sorted(group["estimated_finished"].items())
                ],
            }
        )
    return {
        "source": "ALIEXPRESS",
        "days": days,
        "paid_count": sum(group["paid_count"] for group in groups.values()),
        "received_count": sum(group["received_count"] for group in groups.values()),
        "excluded_count": excluded,
        "missing_commission_count": missing_commissions,
        "by_tracking": by_tracking,
    }, begin, now
