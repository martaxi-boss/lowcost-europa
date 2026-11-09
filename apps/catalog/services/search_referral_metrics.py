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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

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
    if parsed_entries == 0:
        raise ValueError("nginx_no_valid_recent_entries")
    return {
        "schema": 1,
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
        if data.get("schema") != 1 or data.get("source") != SOURCE:
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
        return {
            "checked_at": checked,
            "total": total,
            "rows": [{"name": key, "requests": rows[key]} for key in ENGINES],
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
