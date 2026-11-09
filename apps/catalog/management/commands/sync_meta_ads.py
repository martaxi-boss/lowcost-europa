"""Disabled legacy command: this site's Meta Ads association was removed by its owner."""

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Meta Ads reporting is disabled for Low Cost Europa."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        # Fail closed, even if historical credentials still exist in an environment.
        # Do not contact Meta/Windsor or write an old account's metrics.
        raise CommandError("META_REPORT=DISABLED_BY_OWNER")
