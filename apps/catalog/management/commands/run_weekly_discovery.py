from django.core.management.base import BaseCommand, CommandError

from apps.catalog.services.weekly_discovery import run_weekly_discovery
from apps.integrations.aliexpress.client import AliExpressClient
from apps.integrations.aliexpress.exceptions import (
    AliExpressAuthenticationError,
    AliExpressConfigurationError,
    AliExpressRateLimitError,
    AliExpressRuntimeStateError,
)


class Command(BaseCommand):
    help = "Executa uma campanha semanal limitada de descoberta para as cinco famílias."

    def handle(self, *args, **options):
        client = AliExpressClient()
        try:
            report = run_weekly_discovery(client=client)
        except (
            AliExpressAuthenticationError,
            AliExpressConfigurationError,
            AliExpressRateLimitError,
            AliExpressRuntimeStateError,
        ) as exc:
            report = getattr(exc, "weekly_discovery_report", None)
            if report is not None:
                self._write_report(report, client)
            raise CommandError(
                "Campanha semanal abortada por autenticação, rate limit ou estado local."
            ) from exc

        self._write_report(report, client)

    def _write_report(self, report, client):
        for item in report.families:
            self.stdout.write(f"FAMÍLIA={item.family_slug}")
            self.stdout.write(f"PENDENTES ANTES={item.pending_before}")
            self.stdout.write(f"PESQUISAS API={item.search_operations}")
            self.stdout.write(f"DETALHES API={item.detail_attempts}")
            self.stdout.write(f"NOVOS CANDIDATOS={item.new_candidates}")
            self.stdout.write(f"DUPLICADOS IGNORADOS={item.duplicates_ignored}")
            self.stdout.write(
                f"REJEITADOS HISTÓRICOS IGNORADOS={item.historical_rejections_ignored}"
            )
            self.stdout.write(f"ERROS TRANSITÓRIOS={item.transient_errors}")
            self.stdout.write(f"PENDENTES DEPOIS={item.pending_after}")
            self.stdout.write(
                "LIMITE DE FILA ATINGIDO="
                + ("SIM" if item.queue_cap_hit else "NÃO")
            )
        metrics = client.execution_metrics
        self.stdout.write(f"OPERAÇÕES LÓGICAS={metrics.logical_operations}")
        self.stdout.write(f"TENTATIVAS HTTP={metrics.attempts}")
        self.stdout.write(f"RETRIES={metrics.retries}")
        self.stdout.write(f"429={metrics.http_429}")
        self.stdout.write(f"5XX={metrics.http_5xx}")
        self.stdout.write(f"FALHAS TRANSPORTE={metrics.transport_failures}")
        self.stdout.write(
            "RATE-LIMIT ABORT=" + ("SIM" if metrics.rate_limit_abort else "NÃO")
        )
        self.stdout.write(f"DURAÇÃO={metrics.duration_ms}ms")
        self.stdout.write("AUTO APROVADOS=0")
        self.stdout.write("AUTO PUBLICADOS=0")
        self.stdout.write("LINKS AFILIADOS GERADOS PELA DESCOBERTA=0")
