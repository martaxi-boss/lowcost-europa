"""Read-only Meta Ads report through an existing authorized Windsor.ai account.

Windsor's API accepts the API key *only* in the query string, so this
module must never log full request URLs or include exception strings.
"""

import json
import os
from datetime import timedelta
from urllib import error, parse, request

from django.utils import timezone

from .meta_ads_reporting import MetaAdsNotConfigured, MetaAdsReportError, _safe_int, _safe_spend

WINDSOR_FACEBOOK_URL = "https://connectors.windsor.ai/facebook"
MAX_BODY_BYTES = 262144


def _account_id(value):
    return str(value or "").strip().removeprefix("act_")


def _fetch_rows(params, *, opener):
    url = WINDSOR_FACEBOOK_URL + "?" + parse.urlencode(params)
    req = request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "Windsor/1.0"}, method="GET"
    )
    try:
        with opener(req, timeout=15) as response:
            if response.status != 200:
                raise MetaAdsReportError("windsor_http_error")
            payload_raw = response.read(MAX_BODY_BYTES + 1)
        if len(payload_raw) > MAX_BODY_BYTES:
            raise MetaAdsReportError("windsor_response_too_large")
        payload = json.loads(payload_raw.decode("utf-8"))
    except (error.HTTPError, error.URLError, TimeoutError):
        raise MetaAdsReportError("windsor_transport_or_auth_error") from None
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise MetaAdsReportError("invalid_windsor_json") from None

    if isinstance(payload, dict):
        if "error" in payload or payload.get("status") == "pending":
            raise MetaAdsReportError("windsor_provider_unavailable")
        rows = payload.get("data")
    else:
        rows = payload
    if not isinstance(rows, list) or any(not isinstance(item, dict) for item in rows):
        raise MetaAdsReportError("windsor_unexpected_result")
    return rows


def collect_windsor_meta_ads_report(
    *, now=None, opener=request.urlopen, account_id=None, api_key=None
):
    """Query only the verified account; missing insights require a valid account read."""
    account_id = _account_id(account_id or os.environ.get("META_AD_ACCOUNT_ID"))
    api_key = api_key or os.environ.get("WINDSOR_API_KEY")
    if not account_id.isdecimal() or not api_key:
        raise MetaAdsNotConfigured("windsor_server_access_missing")

    now = now or timezone.now()
    begin = now - timedelta(days=30)
    base = {"api_key": api_key, "select_accounts": account_id, "_renderer": "json"}

    account_rows = _fetch_rows(
        {
            **base,
            "fields": "account_id,account_name,account_currency,account_status",
        },
        opener=opener,
    )
    if len(account_rows) != 1 or _account_id(account_rows[0].get("account_id")) != account_id:
        raise MetaAdsReportError("windsor_account_identity_mismatch")
    account = account_rows[0]
    currency = str(account.get("account_currency") or "").strip().upper()
    if len(currency) != 3 or not currency.isascii() or not currency.isalpha():
        raise MetaAdsReportError("windsor_account_currency_invalid")

    metric_rows = _fetch_rows(
        {
            **base,
            "date_preset": "last_30d",
            "fields": "account_id,spend,impressions,clicks,reach,actions_link_click",
        },
        opener=opener,
    )
    if len(metric_rows) > 1:
        raise MetaAdsReportError("windsor_unexpected_metrics_groups")
    if metric_rows:
        item = metric_rows[0]
        if _account_id(item.get("account_id")) != account_id:
            raise MetaAdsReportError("windsor_metrics_account_mismatch")
        required = ("spend", "impressions", "clicks", "reach")
        if any(item.get(k) is None for k in required):
            raise MetaAdsReportError("windsor_metrics_incomplete")
        spend = _safe_spend(item["spend"])
        impressions = _safe_int(item["impressions"])
        clicks = _safe_int(item["clicks"])
        reach = _safe_int(item["reach"])
        link_clicks = item.get("actions_link_click")
        if link_clicks is not None:
            link_clicks = _safe_int(link_clicks)
    else:
        # The requested *account* was verified first, so no Insights rows
        # means no reported spend/impressions/clicks for the date window.
        spend, impressions, clicks, reach, link_clicks = "0.00", 0, 0, 0, None

    return (
        {
            "source": "META",
            "provider": "WINDSOR",
            "days": 30,
            "currency": currency,
            "spend": spend,
            "impressions": impressions,
            "clicks": clicks,
            "reach": reach,
            "link_clicks": link_clicks,
            "account_name": str(account.get("account_name") or "")[:120],
        },
        begin,
        now,
    )
