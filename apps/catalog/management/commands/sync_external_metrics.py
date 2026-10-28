"""Refresh both provider reports independently; keep each last-known-good snapshot."""

import os

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Refresh AliExpress orders and, when authorized, Meta read-only insights."

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

        # Report partial failure to systemd without blocking successful
        # independent snapshots or hiding either provider's error.
        if failures:
            raise CommandError("EXTERNAL_METRICS_FAILED=" + ",".join(failures))
