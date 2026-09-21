from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.catalog.services.offer_maintenance import maintain_catalog_offers
from apps.integrations.aliexpress.client import AliExpressClient, format_execution_metrics
from apps.integrations.aliexpress.exceptions import AliExpressRateLimitError


class Command(BaseCommand):
    help = (
        "Check a bounded rotating batch of existing offers without renewing "
        "human protocol freshness."
    )

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int)

    def handle(self, *args, **options):
        batch_size = options["batch_size"] or settings.CATALOG_MAINTENANCE_BATCH_SIZE
        if not 1 <= batch_size <= 20:
            raise CommandError("batch-size must be between 1 and 20")
        client = AliExpressClient()
        try:
            result = maintain_catalog_offers(batch_size=batch_size, client=client)
        except AliExpressRateLimitError as exc:
            self.stdout.write("\n".join(format_execution_metrics(client.execution_metrics)))
            raise CommandError("AliExpress rate-limit abort") from exc
        except RuntimeError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(f"Offers selected: {result.offers_selected}")
        self.stdout.write(f"Detail attempts: {result.detail_attempts}")
        self.stdout.write(f"Available confirmed: {result.available_confirmed}")
        self.stdout.write(f"Unavailable confirmed: {result.unavailable_confirmed}")
        self.stdout.write(f"Transient failures: {result.transient_failures}")
        self.stdout.write(f"Offers deactivated: {result.offers_deactivated}")
        self.stdout.write(f"Promotion attempts: {result.promotion_attempts}")
        self.stdout.write(f"Promotion eligible: {result.promotion_eligible}")
        self.stdout.write(f"Promotion ineligible: {result.promotion_ineligible}")
        self.stdout.write(
            f"Promotion transient failures: {result.promotion_transient_failures}"
        )
        if result.failures:
            self.stdout.write("Failures: " + ", ".join(result.failures))
        self.stdout.write("\n".join(format_execution_metrics(client.execution_metrics)))
