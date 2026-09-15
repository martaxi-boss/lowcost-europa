from unittest.mock import patch

from django.test import TransactionTestCase

from apps.catalog.services.cohort_observation import observe_aliexpress_products
from apps.catalog.services.discovery import discover_aliexpress
from apps.catalog.tests.test_cohort_observation import FakeClient as CohortFakeClient
from apps.catalog.tests.test_discovery import FakeDiscoveryClient, product
from apps.integrations.aliexpress.exceptions import AliExpressRateLimitError


class RateLimitBatchAbortTests(TransactionTestCase):
    def test_discovery_rate_limit_aborts_before_next_product(self):
        client = FakeDiscoveryClient([product("1"), product("2")])
        with patch(
            "apps.catalog.services.discovery.import_aliexpress_product",
            side_effect=AliExpressRateLimitError("rate limited"),
        ) as persist:
            with self.assertRaises(AliExpressRateLimitError):
                discover_aliexpress("HIFU", 2, client=client, dry_run=True)
        self.assertEqual(persist.call_count, 1)

    def test_cohort_rate_limit_aborts_before_next_product(self):
        client = CohortFakeClient(["1", "2"])
        with patch(
            "apps.catalog.services.cohort_observation.import_aliexpress_product",
            side_effect=AliExpressRateLimitError("rate limited"),
        ) as persist:
            with self.assertRaises(AliExpressRateLimitError):
                observe_aliexpress_products(["1", "2"], client=client)
        self.assertEqual(persist.call_count, 1)
