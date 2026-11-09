"""Refresh each private provider report independently; keep last-known-good snapshots."""

import os

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Refresh authorized AliExpress and Google Search Console metrics."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        flags = ["--dry-run"] if options["dry_run"] else []
        failures = []
        try:
            call_command("sync_affiliate_orders", *flags)
        except CommandError:
            failures.append("ALIEXPRESS")
            self.stderr.write("ALIEXPRESS_REPORT=UNAVAILABLE")

        # Meta advertising was disconnected by the owner. Never sync it here.
        has_windsor_key = bool(os.environ.get("WINDSOR_API_KEY"))
        # Search Console uses the independent site property and must remain active.
        property_id = os.environ.get("GOOGLE_SEARCH_CONSOLE_PROPERTY", "").strip()
        if not property_id:
            self.stdout.write("GOOGLE_SEARCH_REPORT=AWAITING_PROPERTY_AUTHORIZATION")
        elif property_id != "sc-domain:lowcost-europa.eu" or not has_windsor_key:
            failures.append("GOOGLE_SEARCH_CONFIG")
            self.stderr.write("GOOGLE_SEARCH_REPORT=INCOMPLETE_SERVER_CONFIGURATION")
        else:
            try:
                call_command("sync_google_search_console", *flags)
            except CommandError:
                failures.append("GOOGLE_SEARCH")
                self.stderr.write("GOOGLE_SEARCH_REPORT=UNAVAILABLE")

        # Report partial failure to systemd without blocking successful
        # independent snapshots or hiding either provider's error.
        if failures:
            raise CommandError("EXTERNAL_METRICS_FAILED=" + ",".join(failures))
