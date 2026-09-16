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

    def test_existing_candidate_snapshot_updates_without_resetting_rejected_status(self):
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
        client.get_product_detail.return_value = self.product("101", title="Updated")
        result = discover_family_candidates(self.family, "HIFU", client=client)
        candidate.refresh_from_db()
        self.assertEqual(result.updated, 1)
        self.assertEqual(candidate.status, OfferCandidate.Status.REJECTED)
        self.assertEqual(candidate.title, "Updated")

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
