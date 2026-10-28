"""Bounded periodic report refresh for existing Lowcost Europa provider accounts."""

import os

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Refresh AliExpress orders and, when authorized, Meta read-only insights."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        call_command("sync_affiliate_orders", *([] if not dry_run else ["--dry-run"]))
        has_graph_token = bool(os.environ.get("META_ACCESS_TOKEN"))
        has_windsor_key = bool(os.environ.get("WINDSOR_API_KEY"))
        has_account = bool(os.environ.get("META_AD_ACCOUNT_ID"))
        if has_account != (has_graph_token or has_windsor_key):
            raise CommandError("META_REPORT=INCOMPLETE_SERVER_CONFIGURATION")
        if not has_account:
            self.stdout.write("META_REPORT=AWAITING_SERVER_AUTHORIZATION")
            return
        call_command("sync_meta_ads", *([] if not dry_run else ["--dry-run"]))
