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


    def test_search_uses_original_pt_eur_en_and_paging_without_forced_delivery_filter(self):
        client = Mock()
        client.search_products_diagnostic.return_value = AliExpressSearchResult(products=[])
        discover_family_candidates(
            self.family, "HIFU machine", page_no=3, limit=15, client=client
        )
        client.search_products_diagnostic.assert_called_once_with(
            "HIFU machine",
            country="PT",
            currency="EUR",
            page_no=3,
            page_size=15,
            target_language="EN",
        )

    def test_search_and_detail_delivery_provenance_persist_separately(self):
        client = Mock()
        base = self.product("provenance")
        search = type(base)(
            **{**base.__dict__, "ship_to_days_raw": "3 days", "delivery_days": 3}
        )
        detail = type(search)(
            **{**search.__dict__, "ship_to_days_raw": "4 days", "delivery_days": 4}
        )
        client.search_products_diagnostic.return_value = AliExpressSearchResult(products=[search])
        client.get_product_detail.return_value = detail
        result = discover_family_candidates(self.family, "HIFU", client=client)
        self.assertEqual(result.created, 1)
        candidate = OfferCandidate.objects.get(external_product_id="provenance")
        self.assertEqual(candidate.search_ship_to_days_raw, "3 days")
        self.assertEqual(candidate.search_delivery_days, 3)
        self.assertEqual(candidate.detail_ship_to_days_raw, "4 days")
        self.assertEqual(candidate.detail_delivery_days, 4)

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

    def test_approved_like_professional_hifu_is_prioritized_over_generic_hifu(self):
        OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="approved-pattern",
            status=OfferCandidate.Status.APPROVED,
            title="Approved 22D MAX HIFU machine",
        )
        client = Mock()
        generic = self.product("generic", "HIFU device")
        strong = self.product("strong", "Professional 22D MAX HIFU Beauty Salon Machine")
        client.search_products_diagnostic.return_value = AliExpressSearchResult(
            products=[generic, strong]
        )
        client.get_product_detail.return_value = strong
        result = discover_family_candidates(self.family, "HIFU", max_details=1, client=client)
        self.assertEqual(result.detail_attempts, 1)
        client.get_product_detail.assert_called_once_with("strong", "PT", "EUR")

    def test_accessory_never_ranks_even_with_strong_metadata(self):
        client = Mock()
        accessory = self.product("acc-high", "22D MAX HIFU replacement cartridge")
        accessory = type(accessory)(**{**accessory.__dict__, "sales_count": 999999})
        machine = self.product("machine", "Professional HIFU machine")
        client.search_products_diagnostic.return_value = AliExpressSearchResult(
            products=[accessory, machine]
        )
        client.get_product_detail.return_value = machine
        result = discover_family_candidates(self.family, "HIFU", max_details=1, client=client)
        self.assertEqual(result.skipped_accessory_part, 1)
        client.get_product_detail.assert_called_once_with("machine", "PT", "EUR")

    def test_existing_candidate_in_other_family_is_not_reintroduced(self):
        other = ProductFamily.objects.create(name="RF", slug="rf")
        OfferCandidate.objects.create(
            product_family=other,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="known-global",
            status=OfferCandidate.Status.PENDING,
        )
        client = Mock()
        client.search_products_diagnostic.return_value = AliExpressSearchResult(
            products=[self.product("known-global", "Professional 22D MAX HIFU machine")]
        )
        result = discover_family_candidates(self.family, "HIFU", client=client)
        self.assertEqual(result.skipped_known_other_family, 1)
        client.get_product_detail.assert_not_called()

    def test_same_title_with_different_ids_can_both_be_candidates(self):
        client = Mock()
        one = self.product("same-title-1", "Professional 22D MAX HIFU machine")
        two = self.product("same-title-2", "Professional 22D MAX HIFU machine")
        client.search_products_diagnostic.return_value = AliExpressSearchResult(products=[one, two])
        client.get_product_detail.side_effect = [one, two]
        result = discover_family_candidates(self.family, "HIFU", client=client)
        self.assertEqual(result.created, 2)

    def test_missing_sales_rating_does_not_reject(self):
        client = Mock()
        product = self.product("missing-meta", "Professional HIFU machine")
        product = type(product)(
            **{**product.__dict__, "sales_count": None, "evaluation_rate_percent": None}
        )
        client.search_products_diagnostic.return_value = AliExpressSearchResult(products=[product])
        client.get_product_detail.return_value = product
        result = discover_family_candidates(self.family, "HIFU", client=client)
        self.assertEqual(result.created, 1)
