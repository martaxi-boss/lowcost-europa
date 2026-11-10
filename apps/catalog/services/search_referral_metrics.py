"""Privacy-conscious SEO referrer counts from this site's own Nginx log.

Not Search Console, not unique visitors, and not trustworthy proof of the
claimed Referer: this is an observed HTTP request count, with no IP/UA storage.
Requires no OAuth, external service, Django database migration or pixel.
"""

import argparse
import gzip
import json
import os
import re
import tempfile
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

SOURCE = "NGINX_REFERRER"
LOG_NAME = "lowcost-europa.access.log"
ENGINES = ("Google", "Bing", "Yahoo", "DuckDuckGo", "Brave", "Seznam", "Yandex")
MAX_LOG_BYTES = 128 * 1024 * 1024
MAX_LINES = 2_000_000

# Standard Nginx "combined" log. Sensitive IP/User-Agent are deliberately
# neither retained nor included in the derived private aggregate.
COMBINED = re.compile(
    r'^\S+ \S+ \S+ \[(?P<when>[^\]]{10,55})\] '
    r'"(?P<request>[^"]{0,2048})" (?P<status>\d{3}) \S+ '
    r'"(?P<referer>[^"]{0,2048})" "[^"]{0,4096}"(?: .*)?$'
)


def _engine(referer):
    if not referer or referer == "-":
        return None
    try:
        parsed = urlsplit(referer)
        if parsed.scheme not in {"http", "https"}:
            return None
        host = (parsed.hostname or "").lower().rstrip(".")
    except ValueError:
        return None
    if re.fullmatch(r"(?:[a-z0-9-]+\.)?google\.[a-z]{2,3}(?:\.[a-z]{2})?", host):
        return "Google"
    if host == "bing.com" or host.endswith(".bing.com"):
        return "Bing"
    if host == "yahoo.com" or host.endswith(".yahoo.com"):
        return "Yahoo"
    if host == "duckduckgo.com" or host.endswith(".duckduckgo.com"):
        return "DuckDuckGo"
    if host == "search.brave.com":
        return "Brave"
    if host == "seznam.cz" or host.endswith(".seznam.cz"):
        return "Seznam"
    if host == "yandex.ru" or host.endswith(".yandex.ru"):
        return "Yandex"
    return None



def _meta_origin(request_line, referer):
    """Classify a public-page arrival, never identifying a person or sale.

    A Facebook/Instagram Referer, Meta UTM or fbclid is an indication of
    origin, NOT a confirmed paid-ad click. Only explicit paid UTM media are
    flagged as tagged campaigns.
    """
    parts = request_line.split(" ", 2)
    if len(parts) < 2:
        return None
    try:
        query = parse_qs(urlsplit(parts[1]).query)
        referer_url = urlsplit(referer)
        host = (referer_url.hostname or "").lower().rstrip(".")
        if referer_url.scheme not in {"http", "https"}:
            host = ""
    except ValueError:
        return None

    def first(key):
        return str(query.get(key, [""])[0]).lower().strip()

    utm_source = first("utm_source")
    if utm_source in {"facebook", "fb", "fb_ads", "facebook_ads"}:
        origin = "facebook"
    elif utm_source in {"instagram", "ig", "instagram_ads"}:
        origin = "instagram"
    elif utm_source in {"meta", "meta_ads"}:
        origin = "unspecified"
    elif host == "facebook.com" or host.endswith(".facebook.com") or (
        host == "fb.com" or host.endswith(".fb.com")
    ):
        origin = "facebook"
    elif host == "instagram.com" or host.endswith(".instagram.com"):
        origin = "instagram"
    elif first("fbclid") or first("igshid"):
        origin = "unspecified"
    else:
        return None

    paid_media = {"paid", "paid_social", "paidsocial", "cpc", "ppc", "ads", "meta_ads"}
    paid_tagged = first("utm_medium") in paid_media and utm_source in {
        "facebook", "fb", "fb_ads", "facebook_ads", "instagram", "ig",
        "instagram_ads", "meta", "meta_ads",
    }
    return origin, paid_tagged


def _public_page(request_path):
    parts = request_path.split(" ", 2)
    if len(parts) < 2 or parts[0] != "GET":
        return False
    path = parts[1].split("?", 1)[0]
    if not path.startswith("/") or len(path) > 700:
        return False
    return not path.startswith((
        "/admin", "/painel", "/ops", "/go/", "/static/", "/.well-known/",
        "/i18n/", "/aliexpress/", "/favicon", "/robots.txt", "/sitemap",
    ))


def _log_files(directory):
    if not directory.is_dir() or directory.is_symlink():
        raise ValueError("nginx_log_directory_unavailable")
    results = []
    for entry in directory.iterdir():
        if not re.fullmatch(r"lowcost-europa\.access\.log(?:\.\d+(?:\.gz)?)?", entry.name):
            continue
        if entry.is_symlink() or not entry.is_file():
            raise ValueError("nginx_log_symlink_or_invalid")
        if entry.stat().st_size > MAX_LOG_BYTES:
            raise ValueError("nginx_log_too_large")
        results.append(entry)
    if not any(p.name == LOG_NAME for p in results):
        raise ValueError("dedicated_nginx_log_missing")
    if len(results) > 24:
        raise ValueError("nginx_log_inventory_unexpected")
    return sorted(results)


def summarize_logs(directory, *, now=None):
    """Return last seven days of *observed requests* from a dedicated vhost.

    Counters are not sessions or unique visitors; an absent Referer is not
    attributed to Google. Partial log retention must not be described as full.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("naive_now")
    now = now.astimezone(timezone.utc)
    start = now - timedelta(days=7)
    files = _log_files(Path(directory))
    counts = Counter()
    meta_counts = Counter()
    meta_daily = Counter()
    meta_paid_tagged = 0
    parsed_entries = 0
    total_lines = 0
    first_observed = None
    last_observed = None
    for path in files:
        opening = gzip.open if path.suffix == ".gz" else open
        with opening(path, "rt", encoding="utf-8", errors="replace") as src:
            for line in src:
                total_lines += 1
                if total_lines > MAX_LINES:
                    raise ValueError("nginx_log_size_budget_exceeded")
                match = COMBINED.match(line.rstrip("\n"))
                if not match:
                    continue
                try:
                    stamp = datetime.strptime(
                        match.group("when"), "%d/%b/%Y:%H:%M:%S %z"
                    ).astimezone(timezone.utc)
                except ValueError:
                    continue
                if stamp < start or stamp > now:
                    continue
                parsed_entries += 1
                if first_observed is None or stamp < first_observed:
                    first_observed = stamp
                if last_observed is None or stamp > last_observed:
                    last_observed = stamp
                if match.group("status") not in {"200", "304"}:
                    continue
                if not _public_page(match.group("request")):
                    continue
                engine = _engine(match.group("referer"))
                if engine:
                    counts[engine] += 1
                meta = _meta_origin(match.group("request"), match.group("referer"))
                if meta:
                    origin, paid_tagged = meta
                    meta_counts[origin] += 1
                    meta_daily[stamp.astimezone(ZoneInfo("Europe/Lisbon")).date().isoformat()] += 1
                    if paid_tagged:
                        meta_paid_tagged += 1
    if parsed_entries == 0:
        raise ValueError("nginx_no_valid_recent_entries")
    today = now.astimezone(ZoneInfo("Europe/Lisbon")).date()
    daily = [
        {
            "date": (today - timedelta(days=offset)).isoformat(),
            "requests": meta_daily[(today - timedelta(days=offset)).isoformat()],
        }
        for offset in range(7, -1, -1)
    ]
    return {
        "schema": 2,
        "meta": {
            "total": sum(meta_counts.values()),
            "facebook": meta_counts["facebook"],
            "instagram": meta_counts["instagram"],
            "unspecified": meta_counts["unspecified"],
            "paid_tagged": meta_paid_tagged,
            "today": meta_daily[today.isoformat()],
            "yesterday": meta_daily[(today - timedelta(days=1)).isoformat()],
            "daily": daily,
        },
        "source": SOURCE,
        "domain": "www.lowcost-europa.eu",
        "checked_at": now.isoformat(),
        "window_start": start.isoformat(),
        "window_end": now.isoformat(),
        "first_observed": first_observed.isoformat(),
        "last_observed": last_observed.isoformat(),
        "log_files_read": len(files),
        "observed_public_search_requests": sum(counts.values()),
        "engines": {engine: counts[engine] for engine in ENGINES},
        "caveat": "observed_requests_not_unique_visits_or_search_console_clicks",
    }


def write_report(report, output_path):
    """Write only sanitized aggregate, atomically, inside the private project."""
    output = Path(output_path)
    if output.is_symlink() or not output.parent.is_dir() or output.parent.is_symlink():
        raise ValueError("unsafe_report_target")
    fd, temporary = tempfile.mkstemp(prefix=".search-report-", dir=output.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(report, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_private_report(path, *, now=None):
    """Fail closed if report missing, malformed, stale or contains unexpected data."""
    file = Path(path)
    try:
        if not file.is_file() or file.is_symlink() or file.stat().st_size > 8192:
            return None
        data = json.loads(file.read_text(encoding="utf-8"))
        checked = datetime.fromisoformat(data["checked_at"])
        now = now or datetime.now(timezone.utc)
        if checked.tzinfo is None or not timedelta(0) <= now - checked <= timedelta(hours=48):
            return None
        if data.get("schema") not in (1, 2) or data.get("source") != SOURCE:
            return None
        if data.get("domain") != "www.lowcost-europa.eu":
            return None
        rows = data.get("engines")
        if not isinstance(rows, dict) or any(
            not isinstance(rows.get(key), int) or isinstance(rows.get(key), bool)
            or not 0 <= rows[key] <= 2_000_000
            for key in ENGINES
        ):
            return None
        total = data.get("observed_public_search_requests")
        if not isinstance(total, int) or total != sum(rows[x] for x in ENGINES):
            return None
        meta = None
        if data["schema"] == 2:
            meta = data.get("meta")
            if not isinstance(meta, dict):
                return None
            integer_fields = ("total", "facebook", "instagram", "unspecified",
                              "paid_tagged", "today", "yesterday")
            if any(type(meta.get(key)) is not int or not 0 <= meta[key] <= 2_000_000
                   for key in integer_fields):
                return None
            if meta["total"] != (meta["facebook"] + meta["instagram"]
                                 + meta["unspecified"]):
                return None
            if meta["paid_tagged"] > meta["total"]:
                return None
            daily = meta.get("daily")
            if not isinstance(daily, list) or len(daily) != 8:
                return None
            if any(not isinstance(day, dict)
                   or not isinstance(day.get("date"), str)
                   or type(day.get("requests")) is not int
                   or not 0 <= day["requests"] <= 2_000_000
                   for day in daily):
                return None
            dates = [date.fromisoformat(day["date"]) for day in daily]
            if (dates != sorted(set(dates))
                    or sum(day["requests"] for day in daily) != meta["total"]):
                return None
            if (meta["today"] != daily[-1]["requests"]
                    or meta["yesterday"] != daily[-2]["requests"]):
                return None
        return {
            "checked_at": checked,
            "total": total,
            "rows": [{"name": key, "requests": rows[key]} for key in ENGINES],
            "meta": meta,
        }
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError, OverflowError):
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = summarize_logs(args.log_dir)
    write_report(report, args.output)
    print(
        "LOWCOST_REFERRER_SUMMARY=PASS "
        "observed_search_requests=" + str(report["observed_public_search_requests"])
    )


if __name__ == "__main__":
    main()
