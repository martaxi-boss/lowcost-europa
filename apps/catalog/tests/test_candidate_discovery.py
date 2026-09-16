from decimal import Decimal
from unittest.mock import Mock

from django.test import TestCase

from apps.catalog.models import Offer, OfferCandidate, ProductFamily
from apps.catalog.services.candidate_discovery import discover_family_candidates
from apps.integrations.aliexpress.types import AliExpressProduct, AliExpressSearchResult


class CandidateDiscoveryTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(name="HIFU", slug="hifu")

    def product(self, product_id, title="Professional HIFU"):
        return AliExpressProduct(
            product_id=product_id,
            title=title,
            image_url=f"https://img.example/{product_id}.jpg",
            product_url=f"https://example.com/{product_id}",
            price=Decimal("123.45"),
            currency="EUR",
            evaluation_rate_percent=Decimal("98.5"),
            sales_count=12,
            commission_rate=Decimal("7"),
            destination_country="PT",
        )

    def test_discovery_creates_candidate_not_offer_and_no_affiliate_generation(self):
        client = Mock()
        search = self.product("100")
        detail = self.product("100")
        client.search_products_diagnostic.return_value = AliExpressSearchResult(products=[search])
        client.get_product_detail.return_value = detail
        result = discover_family_candidates(
            self.family, "HIFU machine", limit=10, max_details=5, client=client
        )
        self.assertEqual(result.created, 1)
        self.assertEqual(OfferCandidate.objects.count(), 1)
        self.assertEqual(Offer.objects.count(), 0)
        client.generate_affiliate_link.assert_not_called()

    def test_existing_rejected_candidate_is_skipped_before_detail(self):
        candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="101",
            status=OfferCandidate.Status.REJECTED,
            title="Old",
        )
        client = Mock()
        client.search_products_diagnostic.return_value = AliExpressSearchResult(
            products=[self.product("101")]
        )
        result = discover_family_candidates(self.family, "HIFU", client=client)
        candidate.refresh_from_db()
        self.assertEqual(result.skipped_previously_rejected, 1)
        self.assertEqual(candidate.status, OfferCandidate.Status.REJECTED)
        self.assertEqual(candidate.title, "Old")
        client.get_product_detail.assert_not_called()

    def test_existing_offer_is_skipped_without_detail(self):
        Offer.objects.create(source=Offer.Source.ALIEXPRESS, external_product_id="102")
        client = Mock()
        client.search_products_diagnostic.return_value = AliExpressSearchResult(
            products=[self.product("102")]
        )
        result = discover_family_candidates(self.family, "HIFU", client=client)
        self.assertEqual(result.skipped_existing_offer, 1)
        client.get_product_detail.assert_not_called()
        self.assertEqual(OfferCandidate.objects.count(), 0)

    def test_obvious_accessory_is_filtered_before_detail(self):
        client = Mock()
        client.search_products_diagnostic.return_value = AliExpressSearchResult(
            products=[self.product("103", title="HIFU replacement cartridge only")]
        )
        result = discover_family_candidates(self.family, "HIFU", client=client)
        self.assertEqual(result.shortlisted, 0)
        client.get_product_detail.assert_not_called()

    def test_null_delivery_days_is_unknown_not_not_shippable(self):
        client = Mock()
        product = self.product("104")
        self.assertIsNone(product.delivery_days)
        client.search_products_diagnostic.return_value = AliExpressSearchResult(products=[product])
        client.get_product_detail.return_value = product
        result = discover_family_candidates(self.family, "HIFU", client=client)
        self.assertEqual(result.created, 1)
        self.assertEqual(result.skipped_not_shippable_to_pt, 0)

    def test_factual_not_shippable_to_pt_is_skipped_before_detail(self):
        client = Mock()
        product = self.product("105")
        product = type(product)(
            **{**product.__dict__, "ship_to_days_raw": "Cannot ship to Portugal"}
        )
        client.search_products_diagnostic.return_value = AliExpressSearchResult(products=[product])
        result = discover_family_candidates(self.family, "HIFU", client=client)
        self.assertEqual(result.skipped_not_shippable_to_pt, 1)
        self.assertEqual(result.detail_attempts, 0)
        client.get_product_detail.assert_not_called()

    def test_metrics_distinguish_accessory_irrelevant_and_rejected(self):
        OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="rejected-1",
            status=OfferCandidate.Status.REJECTED,
        )
        client = Mock()
        client.search_products_diagnostic.return_value = AliExpressSearchResult(
            products=[
                self.product("acc", "HIFU replacement cartridge"),
                self.product("wrong", "EMS facial massager"),
                self.product("rejected-1", "Professional HIFU"),
            ]
        )
        result = discover_family_candidates(self.family, "HIFU", client=client)
        self.assertEqual(result.skipped_accessory_part, 1)
        self.assertEqual(result.skipped_irrelevant_family, 1)
        self.assertEqual(result.skipped_previously_rejected, 1)
        client.get_product_detail.assert_not_called()
