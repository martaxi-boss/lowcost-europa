from django.core.management.base import BaseCommand, CommandError

from apps.catalog.services.cohort_observation import observe_aliexpress_products
from apps.integrations.aliexpress.client import AliExpressClient, format_execution_metrics
from apps.integrations.aliexpress.exceptions import AliExpressError, AliExpressRateLimitError


class Command(BaseCommand):
    help = "Observe up to three explicit AliExpress products for the controlled logistics cohort."

    def add_arguments(self, parser):
        parser.add_argument("--product-id", action="append", default=[])
        parser.add_argument("--keyword", default="HIFU machine")
        parser.add_argument("--commit", action="store_true")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        if options["commit"] and options["dry_run"]:
            raise CommandError("--commit and --dry-run cannot be used together")
        client = AliExpressClient()
        try:
            result = observe_aliexpress_products(
                options["product_id"],
                keyword=options["keyword"],
                commit=options["commit"],
                client=client,
            )
        except AliExpressRateLimitError as exc:
            self.stdout.write("\n".join(format_execution_metrics(client.execution_metrics)))
            self.stdout.write("RATE_LIMIT_ABORT = YES")
            raise CommandError("AliExpress rate-limit abort") from exc
        except (ValueError, AliExpressError) as exc:
            self.stdout.write("\n".join(format_execution_metrics(client.execution_metrics)))
            raise CommandError(str(exc)) from exc

        mode = "COMMIT" if result.commit else "DRY_RUN"
        lines = [
            f"Mode: {mode}",
            f"Keyword: {result.keyword}",
            "Country: PT",
            "Currency: EUR",
            "Target language: EN",
            "Delivery filter: 5",
            f"Requested IDs: {len(result.requested_ids)}",
            f"Unique IDs: {len(result.product_ids)}",
            f"Duplicate IDs ignored: {result.duplicate_ids}",
            f"Successful: {result.successful}",
            f"Failed: {result.failed}",
            f"Offers created: {result.offers_created}",
            f"Offers reused: {result.offers_reused}",
            f"Observations created: {result.observations_created}",
        ]
        if result.errors:
            lines.append("Errors: " + ", ".join(result.errors))
        if result.candidates:
            lines.append("Candidates:")
            lines.append(
                "product_id | title | search_days | detail_days | evidence | freshness | "
                "supports_5d | current_5d | outcome"
            )
            for candidate in result.candidates:
                title = " ".join((candidate.title or "").split())[:70]
                lines.append(
                    " | ".join(
                        [
                            candidate.product_id,
                            title,
                            str(candidate.search_delivery_days)
                            if candidate.search_delivery_days is not None
                            else "-",
                            str(candidate.detail_delivery_days)
                            if candidate.detail_delivery_days is not None
                            else "-",
                            candidate.evidence_state or "-",
                            candidate.freshness_state or "-",
                            "yes"
                            if candidate.supports_5d is True
                            else "no"
                            if candidate.supports_5d is False
                            else "-",
                            "yes"
                            if candidate.supports_current_5d is True
                            else "no"
                            if candidate.supports_current_5d is False
                            else "-",
                            candidate.outcome,
                        ]
                    )
                )
        lines.extend(format_execution_metrics(client.execution_metrics))
        if result.commit:
            lines.append("COMMIT — baseline observations persisted")
        else:
            lines.append("DRY_RUN — no database changes persisted")
        self.stdout.write("\n".join(lines))
