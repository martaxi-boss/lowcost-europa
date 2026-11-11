"""Refresh independent AliExpress and official Google reports.

Do not fail the AliExpress timer while Google Search Console awaits owner OAuth.
"""

import os

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from apps.catalog.management.commands.sync_google_search_console import (
    official_google_oauth_ready,
)
from apps.catalog.services.search_console_metrics import EXPECTED_PROPERTY


class Command(BaseCommand):
    help = "Refresh AliExpress orders and authorized official Google Search Console metrics."

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

        provider = os.environ.get("GOOGLE_SEARCH_CONSOLE_PROVIDER", "GOOGLE_OFFICIAL").upper()
        property_id = os.environ.get("GOOGLE_SEARCH_CONSOLE_PROPERTY", "")
        if provider != "GOOGLE_OFFICIAL":
            failures.append("GOOGLE_SEARCH_PROVIDER")
            self.stderr.write("GOOGLE_SEARCH_REPORT=UNSUPPORTED_PROVIDER")
        elif property_id != EXPECTED_PROPERTY:
            failures.append("GOOGLE_SEARCH_PROPERTY")
            self.stderr.write("GOOGLE_SEARCH_REPORT=PROPERTY_NOT_AUTHORIZED")
        elif not official_google_oauth_ready():
            # A genuine incomplete migration is an explicit pending state, not
            # a reason to break independent AliExpress reporting or use a fallback.
            self.stdout.write("GOOGLE_SEARCH_REPORT=AWAITING_OFFICIAL_OAUTH")
        else:
            try:
                call_command("sync_google_search_console", *flags)
            except CommandError:
                failures.append("GOOGLE_SEARCH")
                self.stderr.write("GOOGLE_SEARCH_REPORT=UNAVAILABLE")

        if failures:
            raise CommandError("EXTERNAL_METRICS_FAILED=" + ",".join(failures))
