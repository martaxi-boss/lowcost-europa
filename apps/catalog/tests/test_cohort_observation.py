from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TransactionTestCase

from apps.catalog.models import Offer, OfferObservation, ProductFamily
from apps.catalog.services.cohort_observation import (
    MAX_COHORT_SIZE,
    normalize_product_ids,
    observe_aliexpress_products,
)
from apps.integrations.aliexpress.client import AliExpressCallMetrics
from apps.integrations.aliexpress.exceptions import AliExpressAPIError
from apps.integrations.aliexpress.types import AliExpressProduct, AliExpressSearchResult


def product(product_id, *, detail_days=None):
    return AliExpressProduct(
        product_id=product_id,
        title=f"7D HIFU Machine {product_id}",
        image_url=None,
        product_url=None,
        price=Decimal("499.00"),
        currency="EUR",
        original_price=Decimal("599.00"),
        evaluation_rate_percent=Decimal("96.5"),
        sales_count=12,
        commission_rate=Decimal("7.0"),
        ship_to_days_raw=("5 days" if detail_days is not None else None),
        delivery_days=detail_days,
        destination_country="PT",
    )


class FakeClient:
    def __init__(self, ids, failing_ids=None):
        self.search_products = [product(i, detail_days=5) for i in ids]
        self.failing_ids = set(failing_ids or [])
        self.search_calls = 0
        self.detail_calls = []
        self.execution_metrics = AliExpressCallMetrics()

    def search_products_diagnostic(self, *args, **kwargs):
        self.search_calls += 1
        return AliExpressSearchResult(products=self.search_products, invalid_items=0)

    def get_product_detail(self, product_id, country, currency):
        self.detail_calls.append(product_id)
        if product_id in self.failing_ids:
            raise AliExpressAPIError("external failure SECRET_SHOULD_NOT_APPEAR")
        return product(product_id, detail_days=None)

    def generate_affiliate_link(self, source_url):
        return None


class CohortObservationTests(TransactionTestCase):
    def test_limits_and_duplicate_contract(self):
        self.assertEqual(MAX_COHORT_SIZE, 3)
        with self.assertRaises(ValueError):
            normalize_product_ids([])
        with self.assertRaises(ValueError):
            normalize_product_ids(["1", "2", "3", "4"])
        self.assertEqual(normalize_product_ids(["42", "42"]), (["42"], 1))

    def test_hard_cap_fails_before_api_or_write(self):
        client = FakeClient(["1", "2", "3", "4"])
        with self.assertRaises(ValueError):
            observe_aliexpress_products(["1", "2", "3", "4"], client=client)
        self.assertEqual(client.search_calls, 0)
        self.assertEqual((Offer.objects.count(), OfferObservation.objects.count()), (0, 0))

    def test_default_dry_run_three_ids_zero_writes(self):
        client = FakeClient(["1", "2", "3"])
        result = observe_aliexpress_products(["1", "2", "3"], client=client)
        self.assertEqual((result.successful, result.observations_created), (3, 3))
        self.assertEqual((Offer.objects.count(), OfferObservation.objects.count()), (0, 0))

    def test_commit_three_ids_writes_once_each_with_provenance(self):
        client = FakeClient(["1", "2", "3"])
        result = observe_aliexpress_products(["1", "2", "3"], client=client, commit=True)
        self.assertEqual((result.successful, result.failed), (3, 0))
        self.assertEqual((Offer.objects.count(), OfferObservation.objects.count()), (3, 3))
        self.assertEqual(
            list(OfferObservation.objects.values_list("search_delivery_days", "delivery_days")),
            [(5, None), (5, None), (5, None)],
        )

    def test_duplicate_id_creates_one_baseline(self):
        client = FakeClient(["42"])
        result = observe_aliexpress_products(["42", "42"], client=client, commit=True)
        self.assertEqual(result.duplicate_ids, 1)
        self.assertEqual((Offer.objects.count(), OfferObservation.objects.count()), (1, 1))

    def test_partial_failure_keeps_successful_product(self):
        client = FakeClient(["1", "2", "3"], failing_ids={"2"})
        result = observe_aliexpress_products(["1", "2", "3"], client=client, commit=True)
        self.assertEqual((result.successful, result.failed), (2, 1))
        self.assertEqual((Offer.objects.count(), OfferObservation.objects.count()), (2, 2))
        self.assertEqual(result.errors, ["product 2: AliExpressAPIError"])

    def test_existing_product_family_is_preserved(self):
        family = ProductFamily.objects.create(name="HIFU", slug="hifu")
        Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="42",
            product_family=family,
        )
        observe_aliexpress_products(["42"], client=FakeClient(["42"]), commit=True)
        self.assertEqual(Offer.objects.get(external_product_id="42").product_family, family)

    def test_command_requires_explicit_commit_for_writes(self):
        fake = FakeClient(["42"])
        with self.settings():
            from unittest.mock import patch

            with patch(
                "apps.catalog.management.commands.aliexpress_observe_products.AliExpressClient",
                return_value=fake,
            ):
                out = StringIO()
                call_command("aliexpress_observe_products", product_id=["42"], stdout=out)
        self.assertIn("DRY_RUN", out.getvalue())
        self.assertEqual((Offer.objects.count(), OfferObservation.objects.count()), (0, 0))

    def test_command_rejects_commit_and_dry_run_together(self):
        with self.assertRaises(CommandError):
            call_command(
                "aliexpress_observe_products",
                product_id=["42"],
                commit=True,
                dry_run=True,
            )
