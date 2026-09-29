from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError

from apps.catalog.services.discovery import (
    DEFAULT_LIMIT,
    discover_aliexpress,
    validate_delivery_days,
    validate_limit,
    validate_target_language,
)
from apps.integrations.aliexpress.client import AliExpressClient, format_execution_metrics
from apps.integrations.aliexpress.exceptions import AliExpressError, AliExpressRateLimitError


def _format_age(age: timedelta | None) -> str:
    if age is None:
        return "-"
    future = age.total_seconds() < 0
    seconds = int(abs(age.total_seconds()))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days:
        text = f"{days}d {hours}h"
    elif hours:
        text = f"{hours}h"
    elif minutes:
        text = f"{minutes}m"
    else:
        text = f"{seconds}s"
    return f"future {text}" if future else text


class Command(BaseCommand):
    help = "Run one bounded AliExpress discovery study for Portugal (PT/EUR)."

    def add_arguments(self, parser):
        parser.add_argument("--keyword", required=True)
        parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
        parser.add_argument("--target-language", choices=["EN", "PT"], default="EN")
        parser.add_argument("--delivery-days", type=int)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        if not options["dry_run"]:
            raise CommandError(
                "Este comando legado é apenas diagnóstico; use --dry-run ou a fila A rever."
            )
        try:
            validate_limit(options["limit"])
            target_language = validate_target_language(options["target_language"])
            delivery_days = validate_delivery_days(options["delivery_days"])
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        client = AliExpressClient()
        try:
            result = discover_aliexpress(
                options["keyword"],
                options["limit"],
                target_language=target_language,
                delivery_days=delivery_days,
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

        m = result.metrics
        lines = [
            f"Keyword: {result.keyword}",
            "Country: PT",
            "Currency: EUR",
            f"Target language: {result.target_language or 'not set'}",
            f"Delivery filter: {result.delivery_days_filter or 'not set'}",
            f"Search results: {result.search_results_received}",
            f"Unique candidates: {result.unique_candidates}",
            f"Duplicates: {result.duplicates_in_batch}",
            f"Invalid IDs: {result.invalid_ids}",
            f"Attempted: {result.attempted}",
            f"Successful: {result.successful}",
            f"Failed: {result.failed}",
            f"External errors: {result.external_errors}",
            f"Persistence errors: {result.persistence_errors}",
            f"Price present (detail): {m.price_present}/{result.successful}",
            f"Currency present (detail): {m.currency_present}/{result.successful}",
            f"Evaluation rate present (detail): {m.evaluation_rate_present}/{result.successful}",
            f"Sales count present (detail): {m.sales_count_present}/{result.successful}",
            f"Commission present (detail): {m.commission_rate_present}/{result.successful}",
            f"Search shipping raw: {m.search_shipping_raw_present}/{result.unique_candidates}",
            f"Search delivery days: {m.search_delivery_days_present}/{result.unique_candidates}",
            f"Delivery <= 5 days (search): {m.search_delivery_within_5_days}",
            f"Shipping raw present (detail): {m.shipping_raw_present}/{result.successful}",
            f"Delivery days present (detail): {m.delivery_days_present}/{result.successful}",
            f"Delivery <= 5 days (detail): {m.delivery_within_5_days}",
            f"Search/detail delivery mismatches: {m.delivery_search_detail_mismatch}",
            f"Offers that would be created: {result.offers_created}",
            f"Offers reused: {result.offers_reused}",
            f"Observations that would be created: {result.observations_created}",
        ]
        if result.errors:
            lines.append("Errors: " + ", ".join(result.errors[:25]))
        if result.candidates:
            lines.append("Candidates:")
            lines.append(
                "product_id | title | price | currency | eval% | sales | commission% | "
                "search_days | detail_days | evidence_state | supports_5d | freshness_state | "
                "age | supports_current_5d | outcome"
            )
            for candidate in result.candidates[:25]:
                title = " ".join((candidate.title or "").split())[:70]
                lines.append(
                    " | ".join(
                        [
                            candidate.product_id,
                            title,
                            str(candidate.price) if candidate.price is not None else "-",
                            candidate.currency or "-",
                            (
                                str(candidate.evaluation_rate_percent)
                                if candidate.evaluation_rate_percent is not None
                                else "-"
                            ),
                            str(candidate.sales_count)
                            if candidate.sales_count is not None
                            else "-",
                            (
                                str(candidate.commission_rate)
                                if candidate.commission_rate is not None
                                else "-"
                            ),
                            (
                                str(candidate.search_delivery_days)
                                if candidate.search_delivery_days is not None
                                else "-"
                            ),
                            (
                                str(candidate.detail_delivery_days)
                                if candidate.detail_delivery_days is not None
                                else "-"
                            ),
                            candidate.evidence_state or "-",
                            (
                                "yes"
                                if candidate.supports_within_5_days is True
                                else "no"
                                if candidate.supports_within_5_days is False
                                else "-"
                            ),
                            candidate.freshness_state or "-",
                            _format_age(candidate.freshness_age),
                            (
                                "yes"
                                if candidate.supports_current_5d_candidate is True
                                else "no"
                                if candidate.supports_current_5d_candidate is False
                                else "-"
                            ),
                            candidate.outcome,
                        ]
                    )
                )
        lines.extend(format_execution_metrics(client.execution_metrics))
        if options["dry_run"]:
            lines.append("DRY_RUN — no database changes persisted")
        else:
            lines.append("COMMIT — discovery persistence completed")
        self.stdout.write("\n".join(lines))
