"""Read-only provider fetch followed by one atomic aggregate snapshot update."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import ExternalMetricsSnapshot
from apps.catalog.services.affiliate_order_reporting import (
    AffiliateOrderReportError,
    collect_affiliate_order_report,
)
from apps.integrations.aliexpress.exceptions import AliExpressError


class Command(BaseCommand):
    help = "Synchronize a verified AliExpress order aggregate without storing buyer data."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        days = options["days"]
        if not 1 <= days <= 90:
            raise CommandError("days must be between 1 and 90")
        try:
            report, period_start, period_end = collect_affiliate_order_report(days=days)
        except (AffiliateOrderReportError, AliExpressError) as exc:
            # Do not leak provider responses or credentials into systemd logs.
            raise CommandError("AliExpress order report unavailable: " + type(exc).__name__) from None

        if not options["dry_run"]:
            with transaction.atomic():
                ExternalMetricsSnapshot.objects.update_or_create(
                    source="ALIEXPRESS",
                    defaults={
                        "period_start": period_start,
                        "period_end": period_end,
                        "checked_at": period_end,
                        "payload": report,
                    },
                )
        outcome = "DRY_RUN_PASS" if options["dry_run"] else "SNAPSHOT_UPDATED"
        self.stdout.write(
            f"ALIEXPRESS_ORDERS={outcome} "
            f"paid={report['paid_count']} received={report['received_count']} "
            f"invalid={report['excluded_count']}"
        )
