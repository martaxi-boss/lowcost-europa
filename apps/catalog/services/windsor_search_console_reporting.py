"""Read-only, server-side Search Console performance via authorized Windsor.ai.

Search Console clicks are organic entrances from Google, not local offer
redirects. Never store account credentials, visitor IPs or search users.
The upstream API key is query-string-only: never log URLs or error bodies.
"""

import json
import os
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from urllib import error, parse, request

from django.utils import timezone


class SearchConsoleReportError(Exception):
    pass


class SearchConsoleNotConfigured(SearchConsoleReportError):
    pass


class SearchConsoleAwaitingData(SearchConsoleReportError):
    """A successful provider request returned no rows; never a numeric zero report."""


SEARCH_CONSOLE_URL = "https://connectors.windsor.ai/searchconsole"
EXPECTED_PROPERTY = "sc-domain:lowcost-europa.eu"
MAX_RESPONSE_BYTES = 262144


def _nonnegative_int(value, *, name):
    if isinstance(value, bool) or value is None:
        raise SearchConsoleReportError("invalid_" + name)
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise SearchConsoleReportError("invalid_" + name) from None
    if not number.is_finite() or number < 0 or number != number.to_integral_value():
        raise SearchConsoleReportError("invalid_" + name)
    return int(number)


def _average_position(value, *, impressions):
    if impressions == 0:
        return None
    if isinstance(value, bool) or value is None:
        raise SearchConsoleReportError("missing_position")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise SearchConsoleReportError("invalid_position") from None
    if not number.is_finite() or number <= 0 or number > 100000:
        raise SearchConsoleReportError("invalid_position")
    return str(number.quantize(Decimal("0.01")))


def _fetch_rows(params, *, opener):
    url = SEARCH_CONSOLE_URL + "?" + parse.urlencode(params)
    req = request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "Lowcost-Europa-Owner-Reporting/1.0"},
        method="GET",
    )
    try:
        with opener(req, timeout=20) as response:
            if response.status != 200:
                raise SearchConsoleReportError("provider_http_error")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (error.HTTPError, error.URLError, TimeoutError):
        # Provider errors can contain URLs with the API key: never include them.
        raise SearchConsoleReportError("provider_transport_or_auth_error") from None

    if len(raw) > MAX_RESPONSE_BYTES:
        raise SearchConsoleReportError("provider_payload_too_large")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise SearchConsoleReportError("invalid_provider_json") from None
    if isinstance(payload, dict):
        if "error" in payload or payload.get("status") == "pending":
            raise SearchConsoleReportError("provider_unavailable")
        rows = payload.get("data")
    else:
        rows = payload
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise SearchConsoleReportError("invalid_provider_rows")
    return rows


def _verify_property(row, property_id):
    identity = str(row.get("account_id") or "").strip()
    if identity != property_id:
        raise SearchConsoleReportError("search_console_property_mismatch")


def collect_search_console_report(
    *, now=None, opener=request.urlopen, api_key=None, property_id=None
):
    """Return one verified site's 30-day organic metrics; never invent zeros.

    A new, connected property without rows is not equivalent to proven zero
    Google clicks. Keep the panel in 'awaiting first report' until verified.
    """
    api_key = api_key or os.environ.get("WINDSOR_API_KEY", "")
    property_id = property_id or os.environ.get("GOOGLE_SEARCH_CONSOLE_PROPERTY", "")
    if property_id != EXPECTED_PROPERTY or not api_key:
        raise SearchConsoleNotConfigured("search_console_authorization_missing")

    now = now or timezone.now()
    base = {
        "api_key": api_key,
        "select_accounts": property_id,
        "date_preset": "last_30d",
        "_renderer": "json",
    }
    summary_rows = _fetch_rows(
        {**base, "fields": "account_id,clicks,impressions,position"},
        opener=opener,
    )
    if not summary_rows:
        raise SearchConsoleAwaitingData("awaiting_first_data")
    if len(summary_rows) != 1:
        raise SearchConsoleReportError("search_console_summary_not_verified")
    summary = summary_rows[0]
    _verify_property(summary, property_id)

    clicks = _nonnegative_int(summary.get("clicks"), name="clicks")
    impressions = _nonnegative_int(summary.get("impressions"), name="impressions")
    average_position = _average_position(
        summary.get("position"), impressions=impressions
    )
    ctr_percent = (
        str((Decimal(clicks) * 100 / Decimal(impressions)).quantize(Decimal("0.01")))
        if impressions
        else "0.00"
    )

    query_rows = _fetch_rows(
        {**base, "fields": "account_id,query,clicks,impressions"},
        opener=opener,
    )
    top_queries = []
    for row in query_rows:
        _verify_property(row, property_id)
        query = row.get("query")
        if not isinstance(query, str) or not query.strip() or len(query) > 240:
            raise SearchConsoleReportError("invalid_query")
        top_queries.append(
            {
                "query": query.strip(),
                "clicks": _nonnegative_int(row.get("clicks"), name="query_clicks"),
                "impressions": _nonnegative_int(
                    row.get("impressions"), name="query_impressions"
                ),
            }
        )
    top_queries.sort(key=lambda item: (-item["clicks"], -item["impressions"], item["query"]))
    return (
        {
            "source": "GOOGLE_SEARCH_CONSOLE",
            "provider": "WINDSOR",
            "property": property_id,
            "days": 30,
            "search_type": "web",
            "clicks": clicks,
            "impressions": impressions,
            "ctr_percent": ctr_percent,
            "average_position": average_position,
            "top_queries": top_queries[:10],
        },
        now - timedelta(days=30),
        now,
    )
