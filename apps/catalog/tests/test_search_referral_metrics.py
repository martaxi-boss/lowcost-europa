"""Tests for local Nginx referral counts without external metrics services."""

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from django.test import SimpleTestCase

from apps.catalog.services.search_referral_metrics import (
    read_private_report,
    summarize_logs,
    write_report,
)


class ReferralSummaryTests(SimpleTestCase):
    def test_counts_only_observed_public_search_requests(self):
        now = datetime(2026, 11, 9, 16, tzinfo=timezone.utc)
        stamp = (now - timedelta(hours=1)).strftime("%d/%b/%Y:%H:%M:%S %z")
        line = (
            '127.0.0.1 - - [' + stamp
            + '] "GET /pt/ HTTP/1.1" 200 100 '
            + '"https://www.google.pt/search?q=example" "test"\n'
        )
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            (folder / "lowcost-europa.access.log").write_text(line, encoding="utf-8")
            report = summarize_logs(folder, now=now)
            self.assertEqual(report["engines"]["Google"], 1)
            self.assertEqual(report["engines"]["Bing"], 0)
            self.assertEqual(report["observed_public_search_requests"], 1)
            output = folder / "report.json"
            write_report(report, output)
            self.assertEqual(read_private_report(output, now=now)["total"], 1)
            self.assertNotIn("127.0.0.1", output.read_text(encoding="utf-8"))

    def test_local_meta_arrivals_are_distinct_from_paid_clicks_and_google(self):
        now = datetime(2026, 11, 10, 20, tzinfo=timezone.utc)

        def line(when, path, referer, status=200):
            stamp = when.strftime("%d/%b/%Y:%H:%M:%S %z")
            return (
                f'192.0.2.45 - - [{stamp}] "GET {path} HTTP/1.1" {status} 100 '
                f'"{referer}" "Synthetic-UserAgent"\n'
            )

        observed = "".join([
            line(now - timedelta(hours=1), "/pt/", "https://l.facebook.com/l.php"),
            line(now - timedelta(hours=23), "/es/", "https://www.instagram.com/"),
            line(now - timedelta(hours=2),
                 "/pt/?utm_source=facebook&utm_medium=paid_social&fbclid=abc", "-"),
            line(now - timedelta(hours=3), "/?fbclid=synthetic", "-"),
            line(now - timedelta(hours=4), "/pt/", "https://notfacebook.com/"),
            line(now - timedelta(hours=4), "/go/211/?fbclid=abc", "-"),
            line(now - timedelta(hours=5), "/pt/?utm_source=facebook", "-", status=404),
        ])
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            (folder / "lowcost-europa.access.log").write_text(observed, encoding="utf-8")
            report = summarize_logs(folder, now=now)
            meta = report["meta"]
            self.assertEqual(report["observed_public_search_requests"], 0)
            self.assertEqual(meta["total"], 4)
            self.assertEqual(meta["facebook"], 2)
            self.assertEqual(meta["instagram"], 1)
            self.assertEqual(meta["unspecified"], 1)
            self.assertEqual(meta["paid_tagged"], 1)
            self.assertEqual(meta["today"], 3)
            self.assertEqual(meta["yesterday"], 1)
            output = folder / "report.json"
            write_report(report, output)
            read_back = read_private_report(output, now=now)
            self.assertEqual(read_back["meta"]["total"], 4)
            self.assertNotIn("192.0.2.45", output.read_text(encoding="utf-8"))
            self.assertNotIn("fbclid", output.read_text(encoding="utf-8"))

    def test_missing_source_is_not_reported_as_zero(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                summarize_logs(Path(root))
