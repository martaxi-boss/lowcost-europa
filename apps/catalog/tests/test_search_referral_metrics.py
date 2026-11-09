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

    def test_missing_source_is_not_reported_as_zero(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                summarize_logs(Path(root))
