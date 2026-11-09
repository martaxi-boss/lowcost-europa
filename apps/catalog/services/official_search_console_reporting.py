"""Official, read-only Google Search Console Search Analytics reporting.

Credentials live only in the existing private server environment. The official
OAuth refresh token is NOT the Windsor authorization and must be granted by the
Search Console property owner separately. No visitor-level records are stored.
"""

import json
import os
from datetime import datetime, time, timedelta
from decimal import Decimal
from urllib import error, parse, request

from django.utils import timezone

from apps.catalog.services.windsor_search_console_reporting import (
    EXPECTED_PROPERTY,
    SearchConsoleAwaitingData,
    SearchConsoleNotConfigured,
    SearchConsoleReportError,
    _average_position,
    _nonnegative_int,
)

OAUTH_ENDPOINT = "https://oauth2.googleapis.com/token"
SEARCH_URL = "https://www.googleapis.com/webmasters/v3/sites/"
MAX_RESPONSE_BYTES = 262144


def _read_json(req, *, opener):
    try:
        with opener(req, timeout=20) as response:
            if response.status != 200:
                raise SearchConsoleReportError("google_http_error")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (error.HTTPError, error.URLError, TimeoutError, OSError):
        # HTTPError includes the URL and may include OAuth client credentials.
        raise SearchConsoleReportError("google_transport_or_authorization_error") from None
    if len(raw) > MAX_RESPONSE_BYTES:
        raise SearchConsoleReportError("google_response_too_large")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise SearchConsoleReportError("google_invalid_json") from None
    if not isinstance(payload, dict) or "error" in payload:
        raise SearchConsoleReportError("google_invalid_response")
    return payload


def _oauth_access_token(*, client_id, client_secret, refresh_token, opener):
    encoded = parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode("utf-8")
    payload = _read_json(
        request.Request(
            OAUTH_ENDPOINT,
            data=encoded,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        ),
        opener=opener,
    )
    access_token = payload.get("access_token")
    if (not isinstance(access_token, str) or not access_token
            or len(access_token) > 8192
            or payload.get("token_type", "Bearer").lower() != "bearer"):
        raise SearchConsoleReportError("google_invalid_token")
    return access_token


def _search_analytics(*, access_token, property_id, begin, end, dimensions, opener):
    endpoint = SEARCH_URL + parse.quote(property_id, safe="") + "/searchAnalytics/query"
    body = json.dumps({
        "startDate": begin.isoformat(),
        "endDate": end.isoformat(),
        "type": "web",
        "dimensions": dimensions,
        "rowLimit": 50,
        "startRow": 0,
        "dataState": "final",
    }).encode("utf-8")
    payload = _read_json(
        request.Request(
            endpoint,
            data=body,
            headers={
                "Authorization": "Bearer " + access_token,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        ),
        opener=opener,
    )
    rows = payload.get("rows", [])
    if not isinstance(rows, list) or any(not isinstance(item, dict) for item in rows):
        raise SearchConsoleReportError("google_invalid_rows")
    if len(rows) > 50:
        raise SearchConsoleReportError("google_too_many_rows")
    return rows


def collect_official_search_console_report(
    *, now=None, opener=request.urlopen, property_id=None,
    client_id=None, client_secret=None, refresh_token=None,
):
    """Return a 30-day aggregate from one fixed domain property.

    Google typically finalizes search data with a delay. Use 30 complete days
    ending 3 days before today, not partial current-day observations.
    An empty summary is *awaiting data*, never an invented zero.
    """
    property_id = property_id or os.environ.get("GOOGLE_SEARCH_CONSOLE_PROPERTY", "")
    client_id = client_id or os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
    client_secret = client_secret or os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "")
    refresh_token = refresh_token or os.environ.get("GOOGLE_OAUTH_REFRESH_TOKEN", "")
    if property_id != EXPECTED_PROPERTY or not all((client_id, client_secret, refresh_token)):
        raise SearchConsoleNotConfigured("google_official_authorization_missing")

    now = now or timezone.now()
    end_date = timezone.localtime(now).date() - timedelta(days=3)
    start_date = end_date - timedelta(days=29)
    token = _oauth_access_token(
        client_id=client_id, client_secret=client_secret,
        refresh_token=refresh_token, opener=opener,
    )
    totals = _search_analytics(
        access_token=token, property_id=property_id, begin=start_date,
        end=end_date, dimensions=[], opener=opener,
    )
    if not totals:
        raise SearchConsoleAwaitingData("google_official_awaiting_data")
    if len(totals) != 1:
        raise SearchConsoleReportError("google_invalid_summary")
    summary = totals[0]
    if summary.get("keys") not in (None, []):
        raise SearchConsoleReportError("google_unexpected_summary_dimensions")
    clicks = _nonnegative_int(summary.get("clicks"), name="clicks")
    impressions = _nonnegative_int(summary.get("impressions"), name="impressions")
    if clicks > impressions:
        raise SearchConsoleReportError("google_clicks_exceed_impressions")
    position = _average_position(summary.get("position"), impressions=impressions)
    ctr_percent = (
        str((Decimal(clicks) * 100 / Decimal(impressions)).quantize(Decimal("0.01")))
        if impressions else "0.00"
    )

    query_rows = _search_analytics(
        access_token=token, property_id=property_id, begin=start_date,
        end=end_date, dimensions=["query"], opener=opener,
    )
    top_queries = []
    for item in query_rows:
        keys = item.get("keys")
        if (not isinstance(keys, list) or len(keys) != 1
                or not isinstance(keys[0], str) or not keys[0].strip()
                or len(keys[0]) > 240):
            raise SearchConsoleReportError("google_invalid_query_keys")
        query_clicks = _nonnegative_int(item.get("clicks"), name="query_clicks")
        query_impressions = _nonnegative_int(
            item.get("impressions"), name="query_impressions"
        )
        if query_clicks > query_impressions:
            raise SearchConsoleReportError("google_invalid_query_metrics")
        top_queries.append({
            "query": keys[0].strip(),
            "clicks": query_clicks,
            "impressions": query_impressions,
        })
    top_queries.sort(key=lambda row: (-row["clicks"], -row["impressions"], row["query"]))
    return (
        {
            "source": "GOOGLE_SEARCH_CONSOLE",
            "provider": "GOOGLE_OFFICIAL",
            "property": property_id,
            "days": 30,
            "search_type": "web",
            "clicks": clicks,
            "impressions": impressions,
            "ctr_percent": ctr_percent,
            "average_position": position,
            "top_queries": top_queries[:10],
        },
        datetime.combine(start_date, time.min, tzinfo=timezone.get_current_timezone()),
        datetime.combine(end_date, time.max, tzinfo=timezone.get_current_timezone()),
    )
