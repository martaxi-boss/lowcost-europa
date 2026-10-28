"""Read-only account-level Meta Ads Insights; no browser pixels or ad mutations."""

import json
import os
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from urllib import error, parse, request

from django.utils import timezone

API_VERSION = "v26.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"


class MetaAdsReportError(Exception):
    """Meta reporting is unavailable or has not passed source verification."""


class MetaAdsNotConfigured(MetaAdsReportError):
    pass


def _safe_int(raw):
    try:
        number = int(raw)
    except (ValueError, TypeError) as exc:
        raise MetaAdsReportError("invalid_count") from exc
    if number < 0:
        raise MetaAdsReportError("invalid_count")
    return number


def _safe_spend(raw):
    try:
        amount = Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise MetaAdsReportError("invalid_spend") from exc
    if not amount.is_finite() or amount < 0:
        raise MetaAdsReportError("invalid_spend")
    return str(amount.quantize(Decimal("0.01")))


def _fetch_json(url, access_token, opener):
    req = request.Request(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with opener(req, timeout=15) as response:
            if response.status != 200:
                raise MetaAdsReportError("meta_http_error")
            data = json.loads(response.read().decode("utf-8"))
    except (error.HTTPError, error.URLError, TimeoutError) as exc:
        raise MetaAdsReportError("meta_transport_or_auth_error") from None
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MetaAdsReportError("invalid_meta_json") from None
    if not isinstance(data, dict) or "error" in data:
        raise MetaAdsReportError("meta_error_response")
    return data


def collect_meta_ads_report(*, now=None, opener=request.urlopen, account_id=None, token=None):
    account_id = account_id or os.environ.get("META_AD_ACCOUNT_ID", "")
    token = token or os.environ.get("META_ACCESS_TOKEN", "")
    account_id = str(account_id).removeprefix("act_").strip()
    if not account_id or not account_id.isdecimal() or not token:
        raise MetaAdsNotConfigured("meta_account_read_access_missing")

    now = now or timezone.now()
    begin = now - timedelta(days=30)
    account = _fetch_json(
        f"{BASE_URL}/act_{account_id}?" + parse.urlencode({"fields": "id,name,currency"}),
        token,
        opener,
    )
    if str(account.get("id", "")) != f"act_{account_id}":
        raise MetaAdsReportError("account_identity_mismatch")
    currency = str(account.get("currency") or "").strip().upper()
    if len(currency) != 3 or not currency.isalpha() or not currency.isascii():
        raise MetaAdsReportError("invalid_currency")

    query = {
        "fields": "spend,impressions,clicks,reach,inline_link_clicks",
        "level": "account",
        "time_range": json.dumps(
            {"since": begin.date().isoformat(), "until": now.date().isoformat()},
            separators=(",", ":"),
        ),
        "limit": 2,
    }
    result = _fetch_json(
        f"{BASE_URL}/act_{account_id}/insights?" + parse.urlencode(query),
        token,
        opener,
    )
    rows = result.get("data")
    if not isinstance(rows, list) or len(rows) > 1:
        raise MetaAdsReportError("unexpected_insights_shape")
    if rows and not isinstance(rows[0], dict):
        raise MetaAdsReportError("invalid_insights")
    item = rows[0] if rows else {}
    spend = _safe_spend(item.get("spend", 0))
    impressions = _safe_int(item.get("impressions", 0))
    clicks = _safe_int(item.get("clicks", 0))
    reach = _safe_int(item.get("reach", 0))
    link_clicks = item.get("inline_link_clicks")
    if link_clicks is not None:
        link_clicks = _safe_int(link_clicks)
    return (
        {
            "source": "META",
            "days": 30,
            "currency": currency,
            "spend": spend,
            "impressions": impressions,
            "clicks": clicks,
            "reach": reach,
            "link_clicks": link_clicks,
            "account_name": str(account.get("name") or "")[:120],
        },
        begin,
        now,
    )
