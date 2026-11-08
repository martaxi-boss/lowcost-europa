"""Refresh each private provider report independently; keep last-known-good snapshots."""

import os

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Refresh authorized AliExpress, Meta Ads and Google Search Console metrics."

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

        has_graph_token = bool(os.environ.get("META_ACCESS_TOKEN"))
        has_windsor_key = bool(os.environ.get("WINDSOR_API_KEY"))
        has_account = bool(os.environ.get("META_AD_ACCOUNT_ID"))
        if has_account != (has_graph_token or has_windsor_key):
            failures.append("META_CONFIG")
            self.stderr.write("META_REPORT=INCOMPLETE_SERVER_CONFIGURATION")
        elif not has_account:
            self.stdout.write("META_REPORT=AWAITING_SERVER_AUTHORIZATION")
        else:
            try:
                call_command("sync_meta_ads", *flags)
            except CommandError:
                failures.append("META")
                self.stderr.write("META_REPORT=UNAVAILABLE")

        # Search Console is opt-in. The Windsor key alone may belong to Meta.
        # Do not query an unapproved Google property or infer zero clicks.
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
