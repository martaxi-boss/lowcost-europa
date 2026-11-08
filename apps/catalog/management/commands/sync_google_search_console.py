"""Read-only Search Console performance sync into the private owner snapshot."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import ExternalMetricsSnapshot
from apps.catalog.services.windsor_search_console_reporting import (
    SearchConsoleReportError,
    collect_search_console_report,
)


class Command(BaseCommand):
    help = "Fetch official Google organic clicks and impressions through authorized Windsor.ai."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        try:
            report, period_start, period_end = collect_search_console_report()
        except SearchConsoleReportError as exc:
            # Do not leak provider URLs (Windsor's api_key is in the URL).
            raise CommandError(
                "GOOGLE_SEARCH_REPORT=UNAVAILABLE_" + type(exc).__name__
            ) from None
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
