from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TransactionTestCase

from apps.catalog.models import Offer, OfferObservation, ProductFamily
from apps.catalog.services.discovery import (
    COUNTRY,
    CURRENCY,
    DEFAULT_LIMIT,
    MAX_LIMIT,
    discover_aliexpress,
    validate_limit,
)
from apps.integrations.aliexpress.exceptions import AliExpressAPIError
from apps.integrations.aliexpress.types import AliExpressProduct


def product(product_id="42", **overrides):
    values = {
        "product_id": product_id,
        "title": f"Product {product_id}",
        "image_url": f"https://images.example/{product_id}.jpg",
        "product_url": f"https://source.example/{product_id}",
        "price": Decimal("99.90"),
        "currency": "EUR",
        "original_price": Decimal("120.00"),
        "evaluation_rate_percent": Decimal("96.5"),
        "sales_count": 21,
        "commission_rate": Decimal("7.5"),
        "ship_to_days_raw": "Ship to PT in 3 Days",
        "delivery_days": 3,
        "destination_country": "PT",
    }
    values.update(overrides)
    return AliExpressProduct(**values)


class FakeDiscoveryClient:
    def __init__(self, search_results, details=None, failing_ids=None):
        self.search_results = search_results
        self.details = details or {p.product_id: p for p in search_results if p.product_id}
        self.failing_ids = set(failing_ids or [])
        self.search_calls = []
        self.detail_calls = []

    def search_products(self, keyword, country, currency, page_no=1, page_size=20):
        self.search_calls.append((keyword, country, currency, page_no, page_size))
        return self.search_results

    def get_product_detail(self, product_id, country, currency):
        self.detail_calls.append((product_id, country, currency))
        if product_id in self.failing_ids:
            raise AliExpressAPIError("external failure SECRET_SHOULD_NOT_APPEAR")
        return self.details[product_id]

    def generate_affiliate_link(self, source_url):
        return "https://affiliate.example/item"


class DiscoveryTests(TransactionTestCase):
    def test_limit_contract(self):
        self.assertEqual(DEFAULT_LIMIT, 10)
        self.assertEqual(MAX_LIMIT, 25)
        for valid in (1, 10, 25):
            self.assertEqual(validate_limit(valid), valid)
        for invalid in (0, -1, 26, 100):
            with self.assertRaises(ValueError):
                validate_limit(invalid)

    def test_search_uses_one_keyword_pt_eur_and_requested_limit(self):
        client = FakeDiscoveryClient([product("42")])
        discover_aliexpress("HIFU", 1, client=client, dry_run=True)
        self.assertEqual(client.search_calls, [("HIFU", COUNTRY, CURRENCY, 1, 1)])

    def test_deduplicates_batch_and_counts_invalid_id(self):
        client = FakeDiscoveryClient([product("42"), product("42"), product(""), product("84")])
        result = discover_aliexpress("HIFU", 4, client=client, dry_run=True)
        self.assertEqual(
            (result.unique_candidates, result.duplicates_in_batch, result.invalid_ids), (2, 1, 1)
        )
        self.assertEqual([call[0] for call in client.detail_calls], ["42", "84"])

    def test_new_existing_offer_and_product_family(self):
        family = ProductFamily.objects.create(name="HIFU", slug="hifu")
        Offer.objects.create(
            source=Offer.Source.ALIEXPRESS, external_product_id="42", product_family=family
        )
        result = discover_aliexpress(
            "HIFU", 2, client=FakeDiscoveryClient([product("42"), product("84")])
        )
        self.assertEqual(
            (result.offers_created, result.offers_reused, result.observations_created), (1, 1, 2)
        )
        self.assertEqual(Offer.objects.get(external_product_id="42").product_family, family)
        self.assertIsNone(Offer.objects.get(external_product_id="84").product_family)

    def test_metrics_preserve_none_and_zero_semantics(self):
        rich = product("42")
        sparse = product(
            "84",
            price=None,
            currency=None,
            evaluation_rate_percent=Decimal("0"),
            sales_count=0,
            commission_rate=Decimal("0"),
            ship_to_days_raw=None,
            delivery_days=None,
        )
        slow = product("126", delivery_days=8)
        c = discover_aliexpress(
            "HIFU", 3, client=FakeDiscoveryClient([rich, sparse, slow]), dry_run=True
        ).metrics
        self.assertEqual((c.price_present, c.price_missing), (2, 1))
        self.assertEqual((c.currency_present, c.currency_missing), (2, 1))
        self.assertEqual((c.evaluation_rate_present, c.evaluation_rate_missing), (3, 0))
        self.assertEqual((c.sales_count_present, c.sales_count_missing), (3, 0))
        self.assertEqual((c.commission_rate_present, c.commission_rate_missing), (3, 0))
        self.assertEqual((c.shipping_raw_present, c.shipping_raw_missing), (2, 1))
        self.assertEqual((c.delivery_days_present, c.delivery_days_missing), (2, 1))
        self.assertEqual((c.delivery_within_5_days, c.delivery_over_5_days), (1, 1))

    def test_product_failure_is_counted_and_batch_continues(self):
        client = FakeDiscoveryClient(
            [product("42"), product("84"), product("126")], failing_ids={"84"}
        )
        result = discover_aliexpress("HIFU", 3, client=client)
        self.assertEqual((result.attempted, result.successful, result.failed), (3, 2, 1))
        self.assertEqual((result.external_errors, result.persistence_errors), (1, 0))
        self.assertEqual((Offer.objects.count(), OfferObservation.objects.count()), (2, 2))

    def test_dry_run_preserves_database_state(self):
        family = ProductFamily.objects.create(name="HIFU", slug="hifu")
        existing = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="42",
            product_family=family,
            title="Existing title",
        )
        original_last_seen = existing.last_seen_at
        result = discover_aliexpress(
            "HIFU",
            2,
            client=FakeDiscoveryClient([product("42", title="Changed"), product("84")]),
            dry_run=True,
        )
        existing.refresh_from_db()
        self.assertEqual((result.offers_reused, result.offers_created), (1, 1))
        self.assertEqual((Offer.objects.count(), OfferObservation.objects.count()), (1, 0))
        self.assertEqual(existing.title, "Existing title")
        self.assertEqual(existing.last_seen_at, original_last_seen)
        self.assertEqual(existing.product_family, family)

    def test_command_rejects_limit_above_cap(self):
        with self.assertRaises(CommandError):
            call_command("aliexpress_discover", keyword="HIFU", limit=26, dry_run=True)

    def test_external_error_message_is_not_retained(self):
        result = discover_aliexpress(
            "HIFU", 1, client=FakeDiscoveryClient([product("42")], failing_ids={"42"}), dry_run=True
        )
        self.assertEqual(result.external_errors, 1)
        self.assertEqual(result.errors, ["product 42: AliExpressAPIError"])
        self.assertNotIn("SECRET_SHOULD_NOT_APPEAR", repr(result))

    def test_real_persistence_dry_run_leaves_database_unchanged(self):
        p42 = product("42", product_url=None)

        class FullClient(FakeDiscoveryClient):
            def get_product_detail(self, product_id, country, currency):
                return p42

        client = FullClient([p42], details={"42": p42})
        before = (Offer.objects.count(), OfferObservation.objects.count())
        result = discover_aliexpress("HIFU", 10, client=client, dry_run=True)
        self.assertEqual(result.successful, 1)
        self.assertEqual((Offer.objects.count(), OfferObservation.objects.count()), before)
