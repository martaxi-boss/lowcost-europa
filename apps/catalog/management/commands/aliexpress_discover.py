from django.core.management.base import BaseCommand, CommandError

from apps.catalog.services.discovery import DEFAULT_LIMIT, discover_aliexpress, validate_limit
from apps.integrations.aliexpress.exceptions import AliExpressError


class Command(BaseCommand):
    help = "Run one bounded AliExpress discovery study for Portugal (PT/EUR)."

    def add_arguments(self, parser):
        parser.add_argument("--keyword", required=True)
        parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        try:
            validate_limit(options["limit"])
            result = discover_aliexpress(
                options["keyword"],
                options["limit"],
                dry_run=options["dry_run"],
            )
        except (ValueError, AliExpressError) as exc:
            raise CommandError(str(exc)) from exc

        m = result.metrics
        lines = [
            f"Keyword: {result.keyword}",
            "Country: PT",
            "Currency: EUR",
            f"Search results: {result.search_results_received}",
            f"Unique candidates: {result.unique_candidates}",
            f"Duplicates: {result.duplicates_in_batch}",
            f"Invalid IDs: {result.invalid_ids}",
            f"Attempted: {result.attempted}",
            f"Successful: {result.successful}",
            f"Failed: {result.failed}",
            f"External errors: {result.external_errors}",
            f"Persistence errors: {result.persistence_errors}",
            f"Price present: {m.price_present}/{result.successful}",
            f"Currency present: {m.currency_present}/{result.successful}",
            f"Evaluation rate present: {m.evaluation_rate_present}/{result.successful}",
            f"Sales count present: {m.sales_count_present}/{result.successful}",
            f"Commission present: {m.commission_rate_present}/{result.successful}",
            f"Shipping raw present: {m.shipping_raw_present}/{result.successful}",
            f"Delivery days present: {m.delivery_days_present}/{result.successful}",
            f"Delivery <= 5 days: {m.delivery_within_5_days}",
            f"Delivery > 5 days: {m.delivery_over_5_days}",
            f"Offers that would be created: {result.offers_created}",
            f"Offers reused: {result.offers_reused}",
            f"Observations that would be created: {result.observations_created}",
        ]
        if result.errors:
            lines.append("Errors: " + ", ".join(result.errors[:25]))
        if options["dry_run"]:
            lines.append("DRY_RUN — no database changes persisted")
        else:
            lines.append("COMMIT — discovery persistence completed")
        self.stdout.write("\n".join(lines))
