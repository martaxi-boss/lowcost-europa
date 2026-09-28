from io import StringIO
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings

from apps.catalog.services.offer_maintenance import MaintenanceResult
from apps.integrations.aliexpress.client import AliExpressCallMetrics
from apps.integrations.aliexpress.exceptions import (
    AliExpressRateLimitError,
    AliExpressRuntimeStateError,
)


class CatalogMaintenanceCommandTests(SimpleTestCase):
    @override_settings(CATALOG_MAINTENANCE_BATCH_SIZE=5)
    @patch("apps.catalog.management.commands.maintain_catalog_offers.maintain_catalog_offers")
    @patch("apps.catalog.management.commands.maintain_catalog_offers.AliExpressClient")
    def test_default_batch_is_configured_and_metrics_are_reported(self, client_cls, maintain):
        client = Mock()
        client.execution_metrics = AliExpressCallMetrics()
        client_cls.return_value = client
        maintain.return_value = MaintenanceResult(
            offers_selected=5,
            detail_attempts=5,
            available_confirmed=4,
            transient_failures=1,
        )
        out = StringIO()
        call_command("maintain_catalog_offers", stdout=out)
        maintain.assert_called_once_with(batch_size=5, client=client)
        text = out.getvalue()
        self.assertIn("Offers selected: 5", text)
        self.assertIn("Detail attempts: 5", text)
        self.assertIn("Available confirmed: 4", text)
        self.assertIn("Transient failures: 1", text)
        self.assertIn("Rate-limit abort: NO", text)

    @patch("apps.catalog.management.commands.maintain_catalog_offers.maintain_catalog_offers")
    @patch("apps.catalog.management.commands.maintain_catalog_offers.AliExpressClient")
    def test_cli_batch_override_is_bounded(self, client_cls, maintain):
        client = Mock()
        client.execution_metrics = AliExpressCallMetrics()
        client_cls.return_value = client
        maintain.return_value = MaintenanceResult(offers_selected=2)
        call_command("maintain_catalog_offers", batch_size=2, stdout=StringIO())
        maintain.assert_called_once_with(batch_size=2, client=client)
        with self.assertRaises(CommandError):
            call_command("maintain_catalog_offers", batch_size=21, stdout=StringIO())

    @patch("apps.catalog.management.commands.maintain_catalog_offers.maintain_catalog_offers")
    @patch("apps.catalog.management.commands.maintain_catalog_offers.AliExpressClient")
    def test_runtime_state_failure_aborts_command_with_zero_http_attempts(
        self, client_cls, maintain
    ):
        client = Mock()
        client.execution_metrics = AliExpressCallMetrics(logical_operations=1, attempts=0)
        client_cls.return_value = client
        maintain.side_effect = AliExpressRuntimeStateError("local runtime unavailable")
        out = StringIO()

        with self.assertRaises(CommandError):
            call_command("maintain_catalog_offers", stdout=out)

        text = out.getvalue()
        self.assertIn("Logical operations: 1", text)
        self.assertIn("HTTP attempts: 0", text)

    @patch("apps.catalog.management.commands.maintain_catalog_offers.maintain_catalog_offers")
    @patch("apps.catalog.management.commands.maintain_catalog_offers.AliExpressClient")
    def test_rate_limit_breaker_aborts_command(self, client_cls, maintain):
        client = Mock()
        client.execution_metrics = AliExpressCallMetrics(rate_limit_abort=True, http_429=3)
        client_cls.return_value = client
        maintain.side_effect = AliExpressRateLimitError("429")
        with self.assertRaises(CommandError):
            call_command("maintain_catalog_offers", stdout=StringIO())
