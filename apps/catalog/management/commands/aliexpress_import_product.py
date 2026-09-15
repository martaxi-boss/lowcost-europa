from django.core.management.base import BaseCommand, CommandError

from apps.catalog.services.aliexpress_persistence import import_aliexpress_product
from apps.integrations.aliexpress.client import AliExpressClient, format_execution_metrics
from apps.integrations.aliexpress.exceptions import AliExpressError, AliExpressRateLimitError


class Command(BaseCommand):
    help = "Import one known AliExpress product into Offer and OfferObservation."

    def add_arguments(self, parser):
        parser.add_argument("--product-id", required=True)
        parser.add_argument("--country", default="PT")
        parser.add_argument("--currency", default="EUR")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        client = AliExpressClient()
        try:
            result = import_aliexpress_product(
                options["product_id"],
                options["country"],
                options["currency"],
                dry_run=options["dry_run"],
                client=client,
            )
        except AliExpressRateLimitError as exc:
            self.stdout.write("\n".join(format_execution_metrics(client.execution_metrics)))
            self.stdout.write("RATE_LIMIT_ABORT = YES")
            raise CommandError("AliExpress rate-limit abort") from exc
        except AliExpressError as exc:
            self.stdout.write("\n".join(format_execution_metrics(client.execution_metrics)))
            raise CommandError(str(exc)) from exc

        product = result.product
        self.stdout.write(f"Product: {product.product_id}")
        self.stdout.write(f"Offer: {'created' if result.offer_created else 'reused'}")
        self.stdout.write("Observation: prepared" if result.dry_run else "Observation: created")
        self.stdout.write(f"Country: {options['country']}")
        self.stdout.write(f"Currency present: {product.currency is not None}")
        self.stdout.write(f"Logistics present: {product.ship_to_days_raw is not None}")
        self.stdout.write("\n".join(format_execution_metrics(client.execution_metrics)))
        if result.dry_run:
            self.stdout.write("DRY_RUN — transaction rolled back")
        else:
            self.stdout.write("COMMIT — persistence completed")
