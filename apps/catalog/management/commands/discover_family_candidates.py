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
        parser.add_argument("--limit", type=int, default=10)
        parser.add_argument("--max-details", type=int, default=10)

    def handle(self, *args, **options):
        try:
            family = ProductFamily.objects.get(slug=options["family"])
        except ProductFamily.DoesNotExist as exc:
            raise CommandError("Unknown family") from exc
        client = AliExpressClient()
        try:
            result = discover_family_candidates(
                family,
                options["keyword"],
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
        self.stdout.write(f"Search results: {result.search_results}")
        self.stdout.write(f"Shortlisted: {result.shortlisted}")
        self.stdout.write(f"Detailed: {result.detailed}")
        self.stdout.write(f"Candidates created: {result.created}")
        self.stdout.write(f"Candidates updated: {result.updated}")
        self.stdout.write(f"Existing offers skipped: {result.skipped_existing_offer}")
        if result.failures:
            self.stdout.write("Failures: " + ", ".join(result.failures))
        self.stdout.write("\n".join(format_execution_metrics(client.execution_metrics)))
