from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.catalog.models import Offer
from apps.catalog.services.logistics_history import assess_offer_logistics_history

DIAGNOSTIC_MAX_AGE = timedelta(hours=24)


def _fmt_dt(value):
    return value.isoformat() if value is not None else "-"


def _fmt_opt(value):
    return str(value) if value is not None else "-"


def _fmt_span(value):
    if value is None:
        return "-"
    seconds = int(value.total_seconds())
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)


class Command(BaseCommand):
    help = "Inspect read-only AliExpress logistics history for one Offer."

    def add_arguments(self, parser):
        parser.add_argument("--product-id", required=True)

    def handle(self, *args, **options):
        product_id = options["product_id"].strip()
        try:
            offer = Offer.objects.get(
                source=Offer.Source.ALIEXPRESS,
                external_product_id=product_id,
            )
        except Offer.DoesNotExist as exc:
            raise CommandError("Offer not found") from exc

        assessment = assess_offer_logistics_history(
            offer=offer,
            as_of=timezone.now(),
            max_age=DIAGNOSTIC_MAX_AGE,
        )
        lines = [
            f"Product ID: {product_id}",
            f"Observations: {assessment.observation_count}",
            f"First observed: {_fmt_dt(assessment.first_observed_at)}",
            f"Last observed: {_fmt_dt(assessment.last_observed_at)}",
            f"Span: {_fmt_span(assessment.observation_span)}",
        ]
        if assessment.observation_count == 0:
            lines.append("No logistics history available")
            self.stdout.write("\n".join(lines))
            return

        lines.append("Evidence states:")
        for state, count in assessment.evidence_state_counts.items():
            lines.append(f"{state.value}: {count}")
        lines.append("Freshness states:")
        for state, count in assessment.freshness_state_counts.items():
            lines.append(f"{state.value}: {count}")
        lines.extend(
            [
                f"Supports <=5: {assessment.supports_5d_count}",
                f"Supports current <=5: {assessment.supports_current_5d_count}",
                f"Has conflict: {'yes' if assessment.has_conflict else 'no'}",
                f"Has future timestamp: {'yes' if assessment.has_future else 'no'}",
                "Latest:",
            ]
        )
        latest = assessment.latest
        lines.extend(
            [
                f"observed_at: {_fmt_dt(latest.observed_at)}",
                f"search_days: {_fmt_opt(latest.search_delivery_days)}",
                f"detail_days: {_fmt_opt(latest.detail_delivery_days)}",
                f"evidence: {latest.evidence_state.value}",
                f"freshness: {latest.freshness_state.value}",
                f"supports_5d: {'yes' if latest.supports_5d else 'no'}",
                f"supports_current_5d: {'yes' if latest.supports_current_5d else 'no'}",
            ]
        )
        self.stdout.write("\n".join(lines))
