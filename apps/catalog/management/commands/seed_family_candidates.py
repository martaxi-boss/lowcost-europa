from django.core.management.base import BaseCommand, CommandError

from apps.catalog.models import ProductFamily
from apps.catalog.services.candidate_discovery import seed_candidates_from_existing_offers


class Command(BaseCommand):
    help = "Create pending review candidates from existing family offers without live API calls."

    def add_arguments(self, parser):
        parser.add_argument("--family", required=True)

    def handle(self, *args, **options):
        try:
            family = ProductFamily.objects.get(slug=options["family"])
        except ProductFamily.DoesNotExist as exc:
            raise CommandError("Unknown family") from exc
        self.stdout.write(f"Candidates created: {seed_candidates_from_existing_offers(family)}")
