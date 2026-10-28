"""Meta Ads metrics sync with read-only permissions; never modifies an ad."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import ExternalMetricsSnapshot
from apps.catalog.services.meta_ads_reporting import (
    MetaAdsReportError,
    collect_meta_ads_report,
)


class Command(BaseCommand):
    help = "Synchronize private Meta ad account metrics using server-only ads_read token."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        try:
            report, period_start, period_end = collect_meta_ads_report()
        except MetaAdsReportError as exc:
            raise CommandError("Meta Ads reporting unavailable: " + type(exc).__name__) from None

        if not options["dry_run"]:
            with transaction.atomic():
                ExternalMetricsSnapshot.objects.update_or_create(
                    source="META",
                    defaults={
                        "period_start": period_start,
                        "period_end": period_end,
                        "checked_at": period_end,
                        "payload": report,
                    },
                )
        status = "DRY_RUN_PASS" if options["dry_run"] else "SNAPSHOT_UPDATED"
        self.stdout.write(f"META_ADS_REPORT={status}")
