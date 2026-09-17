from django.core.management.base import BaseCommand, CommandError

from apps.catalog.models import ProductFamily
from apps.catalog.services.deep_discovery import discover_family_deep
from apps.integrations.aliexpress.client import AliExpressClient, format_execution_metrics
from apps.integrations.aliexpress.exceptions import AliExpressError, AliExpressRateLimitError


class Command(BaseCommand):
    help = "Run bounded paginated discovery for one family."

    def add_arguments(self, parser):
        parser.add_argument("--family", required=True)
        parser.add_argument("--keyword", action="append", required=True)
        parser.add_argument("--start-keyword-index", type=int, default=1)
        parser.add_argument("--start-page", type=int, default=1)
        parser.add_argument("--max-pages", type=int, default=3)
        parser.add_argument("--limit", type=int, default=15)
        parser.add_argument("--max-details", type=int, default=8)
        parser.add_argument("--max-search-operations", type=int, default=60)
        parser.add_argument("--max-detail-attempts", type=int, default=180)

    def handle(self, *args, **options):
        try:
            family = ProductFamily.objects.get(slug=options["family"])
        except ProductFamily.DoesNotExist as exc:
            raise CommandError("Unknown family") from exc
        if family.status == ProductFamily.Status.RETIRED:
            raise CommandError("Retired family cannot receive discovery")
        client = AliExpressClient()
        try:
            result = discover_family_deep(
                family,
                options["keyword"],
                start_keyword_index=options["start_keyword_index"],
                start_page=options["start_page"],
                max_pages=options["max_pages"],
                limit=options["limit"],
                max_details=options["max_details"],
                max_search_operations=options["max_search_operations"],
                max_detail_attempts=options["max_detail_attempts"],
                client=client,
            )
        except AliExpressRateLimitError as exc:
            self.stdout.write("\n".join(format_execution_metrics(client.execution_metrics)))
            raise CommandError("AliExpress rate-limit abort") from exc
        except AliExpressError as exc:
            self.stdout.write("\n".join(format_execution_metrics(client.execution_metrics)))
            raise CommandError(exc.__class__.__name__) from exc

        for item in result.pages:
            r = item.result
            self.stdout.write(
                " | ".join(
                    [
                        f"Keyword index: {item.keyword_index}",
                        f"Keyword: {item.keyword}",
                        f"Page: {item.page}",
                        f"Search results: {r.search_results}",
                        f"Raw IDs: {len(r.raw_product_ids)}",
                        f"New raw IDs: {item.new_raw_ids}",
                        f"Repeated raw IDs: {item.repeated_raw_ids}",
                        f"Cross-keyword repeated IDs: {item.cross_keyword_repeated_ids}",
                        f"Shortlisted: {r.shortlisted}",
                        f"Detail attempts: {r.detail_attempts}",
                        f"Detailed: {r.detailed}",
                        f"Detail failures: {r.detail_failures}",
                        f"Created: {r.created}",
                        f"Skipped irrelevant: {r.skipped_irrelevant_family}",
                        f"Skipped accessory: {r.skipped_accessory_part}",
                        f"Skipped existing offer: {r.skipped_existing_offer}",
                        f"Skipped existing candidate: {r.skipped_existing_candidate}",
                        f"Skipped rejected: {r.skipped_previously_rejected}",
                        f"Skipped other family: {r.skipped_known_other_family}",
                        f"Skipped not shippable PT: {r.skipped_not_shippable_to_pt}",
                        f"Failures: {','.join(r.failures) or '-'}",
                        f"Stop: {item.stop_reason or '-'}",
                    ]
                )
            )
        self.stdout.write(f"Search operations: {result.search_operations}")
        self.stdout.write(f"Detail attempts: {result.detail_attempts}")
        self.stdout.write(f"Candidates created: {result.created}")
        self.stdout.write(f"Unique product IDs: {len(result.unique_product_ids)}")
        self.stdout.write(f"Cross-page duplicates: {result.cross_page_duplicates}")
        self.stdout.write(f"Cross-keyword duplicates: {result.cross_keyword_duplicates}")
        self.stdout.write(f"Stop reason: {result.stop_reason or '-'}")
        if result.last_keyword:
            self.stdout.write(f"Last checkpoint: {result.last_keyword} page {result.last_page}")
        self.stdout.write("\n".join(format_execution_metrics(client.execution_metrics)))
