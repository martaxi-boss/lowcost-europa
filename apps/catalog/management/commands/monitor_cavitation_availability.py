from django.core.management.base import BaseCommand, CommandError

from apps.catalog.services.cavitation_availability import (
    MAX_BATCH_SIZE,
    monitor_cavitation_availability,
)
from apps.integrations.aliexpress.exceptions import (
    AliExpressRateLimitError,
    AliExpressRuntimeStateError,
)


class Command(BaseCommand):
    help = (
        "Check all five Owner-curated categories for explicit unavailability; "
        "no automatic discovery, approval, publication or affiliate URL regeneration."
    )

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=MAX_BATCH_SIZE)

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        if not 1 <= batch_size <= MAX_BATCH_SIZE:
            raise CommandError("batch-size must be between 1 and 10")
        try:
            report = monitor_cavitation_availability(batch_size=batch_size)
        except (AliExpressRateLimitError, AliExpressRuntimeStateError) as exc:
            raise CommandError(
                "Não foi possível verificar a disponibilidade: API temporariamente "
                "indisponível. Nenhum link foi eliminado por esta falha."
            ) from exc
        self.stdout.write(
            "CAVITATION_MANUAL_AVAILABILITY"
            f" selected={report.selected} checked={report.checked}"
            f" explicit_unavailable={report.explicit_unavailable}"
            f" awaiting_confirmation={report.awaiting_confirmation}"
            f" removed_from_storefront={report.removed_from_storefront}"
            f" available={report.available} unknown={report.unknown}"
            f" errors={len(report.errors)}"
        )
        for reason in report.errors:
            self.stderr.write("CAVITATION_CHECK_UNKNOWN " + reason)
