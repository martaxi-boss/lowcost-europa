from django.core.management.base import BaseCommand, CommandError

from apps.catalog.models import ProductFamily
from apps.catalog.services.candidate_discovery import discover_family_candidates
from apps.integrations.aliexpress.client import AliExpressClient, format_execution_metrics
from apps.integrations.aliexpress.exceptions import AliExpressError, AliExpressRateLimitError


class Command(BaseCommand):
    help = "Run one bounded family discovery into the private candidate queue."

    def add_arguments(self, parser):
        parser.add_argument("--family", required=True)
        parser.add_argument("--keyword", required=True)
        parser.add_argument("--page", type=int, default=1)
        parser.add_argument("--limit", type=int, default=10)
        parser.add_argument("--max-details", type=int, default=10)

    def handle(self, *args, **options):
        try:
            family = ProductFamily.objects.get(slug=options["family"])
        except ProductFamily.DoesNotExist as exc:
            raise CommandError("Unknown family") from exc
        if family.status == ProductFamily.Status.RETIRED:
            raise CommandError("Retired family cannot receive discovery")
        client = AliExpressClient()
        try:
            result = discover_family_candidates(
                family,
                options["keyword"],
                page_no=options["page"],
                limit=options["limit"],
                max_details=options["max_details"],
                client=client,
            )
        except AliExpressRateLimitError as exc:
            self.stdout.write("\n".join(format_execution_metrics(client.execution_metrics)))
            raise CommandError("AliExpress rate-limit abort") from exc
        except AliExpressError as exc:
            self.stdout.write("\n".join(format_execution_metrics(client.execution_metrics)))
            raise CommandError(exc.__class__.__name__) from exc
        self.stdout.write(f"Page: {options['page']}")
        self.stdout.write(f"Search results: {result.search_results}")
        self.stdout.write(f"Skipped irrelevant family: {result.skipped_irrelevant_family}")
        self.stdout.write(f"Skipped accessory/part: {result.skipped_accessory_part}")
        self.stdout.write(f"Skipped existing offer: {result.skipped_existing_offer}")
        self.stdout.write(f"Skipped existing candidate: {result.skipped_existing_candidate}")
        self.stdout.write(f"Skipped known other family: {result.skipped_known_other_family}")
        self.stdout.write(f"Skipped previously rejected: {result.skipped_previously_rejected}")
        self.stdout.write(f"Skipped not shippable to PT: {result.skipped_not_shippable_to_pt}")
        self.stdout.write(f"Detail attempts: {result.detail_attempts}")
        self.stdout.write(f"Detail failures: {result.detail_failures}")
        self.stdout.write(f"Candidates created: {result.created}")
        self.stdout.write(f"Candidates updated: {result.updated}")
        if result.failures:
            self.stdout.write("Failures: " + ", ".join(result.failures))
        self.stdout.write("\n".join(format_execution_metrics(client.execution_metrics)))
