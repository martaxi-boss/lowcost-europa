"""Periodic AliExpress affiliate order snapshots.

Google/Meta traffic is counted independently and for free from Nginx logs.
No Google Ads, Google OAuth, Windsor.ai, pixels or third-party metric API.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Refresh authorized AliExpress orders; site origin counts use the local Nginx report."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        flags = ["--dry-run"] if options["dry_run"] else []
        try:
            call_command("sync_affiliate_orders", *flags)
        except CommandError:
            self.stderr.write("ALIEXPRESS_REPORT=UNAVAILABLE")
            raise CommandError("EXTERNAL_METRICS_FAILED=ALIEXPRESS") from None
        self.stdout.write("VISITOR_ORIGINS=PRIVATE_NGINX_COUNTER_ONLY")
