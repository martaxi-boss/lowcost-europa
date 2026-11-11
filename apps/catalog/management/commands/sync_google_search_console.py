"""Synchronize verified Google Search Console data via the official free API only.

No third-party provider is supported. An owner OAuth grant is required.
"""

import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import ExternalMetricsSnapshot
from apps.catalog.services.official_search_console_reporting import (
    collect_official_search_console_report,
)
from apps.catalog.services.search_console_metrics import (
    EXPECTED_PROPERTY,
    SearchConsoleAwaitingData,
    SearchConsoleReportError,
)


def official_google_oauth_ready():
    """Check authorization presence without exposing or logging secrets."""
    return (
        os.environ.get("GOOGLE_SEARCH_CONSOLE_PROVIDER", "GOOGLE_OFFICIAL").upper()
        == "GOOGLE_OFFICIAL"
        and os.environ.get("GOOGLE_SEARCH_CONSOLE_PROPERTY", "") == EXPECTED_PROPERTY
        and all(
            os.environ.get(key)
            for key in (
                "GOOGLE_OAUTH_CLIENT_ID",
                "GOOGLE_OAUTH_CLIENT_SECRET",
                "GOOGLE_OAUTH_REFRESH_TOKEN",
            )
        )
    )


class Command(BaseCommand):
    help = "Synchronize official Google Search Console metrics, read-only provider API."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        provider = os.environ.get("GOOGLE_SEARCH_CONSOLE_PROVIDER", "GOOGLE_OFFICIAL").upper()
        if provider != "GOOGLE_OFFICIAL":
            raise CommandError("GOOGLE_SEARCH_REPORT=UNSUPPORTED_PROVIDER")
        property_id = os.environ.get("GOOGLE_SEARCH_CONSOLE_PROPERTY", "")
        if property_id != EXPECTED_PROPERTY:
            raise CommandError("GOOGLE_SEARCH_REPORT=PROPERTY_NOT_AUTHORIZED")
        if not official_google_oauth_ready():
            # Do not call unconfigured providers or overwrite historical figures.
            self.stdout.write("GOOGLE_SEARCH_REPORT=AWAITING_OFFICIAL_OAUTH")
            return
        try:
            report, period_start, period_end = collect_official_search_console_report()
        except SearchConsoleAwaitingData:
            self.stdout.write("GOOGLE_SEARCH_REPORT=AWAITING_DATA")
            return
        except SearchConsoleReportError as exc:
            # Deliberately no exception body, OAuth token, URL or user data.
            raise CommandError(
                "GOOGLE_SEARCH_REPORT=UNAVAILABLE_" + type(exc).__name__
            ) from None
        if report.get("provider") != "GOOGLE_OFFICIAL" or report.get("property") != EXPECTED_PROPERTY:
            raise CommandError("GOOGLE_SEARCH_REPORT=PROVIDER_OR_PROPERTY_MISMATCH")
        if not options["dry_run"]:
            with transaction.atomic():
                ExternalMetricsSnapshot.objects.update_or_create(
                    source="GOOGLE_SEARCH_CONSOLE",
                    defaults={
                        "period_start": period_start,
                        "period_end": period_end,
                        "checked_at": timezone.now(),
                        "payload": report,
                    },
                )
        self.stdout.write(
            "GOOGLE_SEARCH_REPORT=" + ("DRY_RUN_PASS" if options["dry_run"] else "SNAPSHOT_UPDATED")
        )
