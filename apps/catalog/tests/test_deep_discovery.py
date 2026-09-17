from decimal import Decimal
from io import StringIO
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.catalog.models import CandidateDecision, Offer, OfferCandidate, ProductFamily
from apps.catalog.services.candidate_discovery import _learning_inputs, discover_family_candidates
from apps.catalog.services.deep_discovery import discover_family_deep
from apps.catalog.services.family_profiles import LASER_TATTOO_PROFILE
from apps.integrations.aliexpress.types import AliExpressProduct, AliExpressSearchResult


class DeepDiscoveryTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(
            name="Laser", slug="diodo-laser-remocao-tatuagens-pigmentacao"
        )
        self.user = get_user_model().objects.create_user(
            username="deep-discovery-staff", is_staff=True
        )

    def product(self, product_id, title="Professional diode laser hair removal machine"):
        return AliExpressProduct(
            product_id=str(product_id),
            title=title,
            price=Decimal("100"),
            currency="EUR",
            sales_count=10,
            evaluation_rate_percent=Decimal("98"),
            commission_rate=Decimal("5"),
            destination_country="PT",
        )

    def test_page_defaults_to_one_and_custom_page_reaches_client(self):
        for requested_page in (1, 2):
            with self.subTest(page=requested_page):
                client = Mock()
                client.search_products_diagnostic.return_value = AliExpressSearchResult(products=[])
                kwargs = {} if requested_page == 1 else {"page_no": requested_page}
                discover_family_candidates(self.family, "diode laser", client=client, **kwargs)
                self.assertEqual(
                    client.search_products_diagnostic.call_args.kwargs["page_no"], requested_page
                )

    def test_management_command_page_option_is_forwarded_and_reported(self):
        from apps.catalog.services.candidate_discovery import CandidateDiscoveryResult

        out = StringIO()
        with (
            patch("apps.catalog.management.commands.discover_family_candidates.AliExpressClient"),
            patch(
                "apps.catalog.management.commands.discover_family_candidates.discover_family_candidates",
                return_value=CandidateDiscoveryResult(),
            ) as mocked,
        ):
            call_command(
                "discover_family_candidates",
                family=self.family.slug,
                keyword="diode laser",
                page=2,
                stdout=out,
            )
        self.assertEqual(mocked.call_args.kwargs["page_no"], 2)
        self.assertIn("Page: 2", out.getvalue())

    def test_invalid_page_is_rejected(self):
        with self.assertRaisesMessage(ValueError, "page_no must be at least 1"):
            discover_family_candidates(self.family, "diode laser", page_no=0, client=Mock())

    def test_distinct_pages_create_distinct_candidates_and_repeated_ids_do_not_duplicate(self):
        client = Mock()
        one = self.product("p1")
        two = self.product("p2")
        client.search_products_diagnostic.side_effect = [
            AliExpressSearchResult(products=[one]),
            AliExpressSearchResult(products=[two, one]),
        ]
        client.get_product_detail.side_effect = [one, two]
        first = discover_family_candidates(self.family, "diode laser", page_no=1, client=client)
        second = discover_family_candidates(self.family, "diode laser", page_no=2, client=client)
        self.assertEqual(first.created, 1)
        self.assertEqual(second.created, 1)
        self.assertEqual(second.skipped_existing_candidate, 1)
        self.assertEqual(OfferCandidate.objects.count(), 2)

    def test_empty_page_stops_keyword(self):
        client = Mock()
        client.search_products_diagnostic.return_value = AliExpressSearchResult(products=[])
        result = discover_family_deep(self.family, ["diode laser"], client=client)
        self.assertEqual(result.search_operations, 1)
        self.assertEqual(result.pages[0].stop_reason, "EMPTY_PAGE")

    def test_page_without_new_ids_stops_keyword(self):
        client = Mock()
        product = self.product("same")
        client.search_products_diagnostic.side_effect = [
            AliExpressSearchResult(products=[product]),
            AliExpressSearchResult(products=[product]),
        ]
        client.get_product_detail.return_value = product
        result = discover_family_deep(self.family, ["diode laser"], max_details=1, client=client)
        self.assertEqual(result.search_operations, 2)
        self.assertEqual(result.pages[-1].stop_reason, "NO_NEW_IDS")
        self.assertEqual(OfferCandidate.objects.count(), 1)

    def test_max_pages_is_respected(self):
        client = Mock()
        pages = [self.product(f"p{i}") for i in range(1, 4)]
        client.search_products_diagnostic.side_effect = [
            AliExpressSearchResult(products=[product]) for product in pages
        ]
        client.get_product_detail.side_effect = pages
        result = discover_family_deep(
            self.family, ["diode laser"], max_pages=2, max_details=1, client=client
        )
        self.assertEqual(result.search_operations, 2)
        self.assertEqual(OfferCandidate.objects.count(), 2)

    def test_deep_discovery_can_create_more_than_twenty_pending_candidates(self):
        client = Mock()
        pages = []
        details = []
        for page in range(3):
            products = [self.product(f"p{page}-{i}") for i in range(8)]
            pages.append(AliExpressSearchResult(products=products))
            details.extend(products)
        client.search_products_diagnostic.side_effect = pages
        client.get_product_detail.side_effect = details
        result = discover_family_deep(
            self.family,
            ["diode laser"],
            max_pages=3,
            limit=15,
            max_details=8,
            client=client,
        )
        self.assertEqual(result.created, 24)
        self.assertEqual(
            OfferCandidate.objects.filter(status=OfferCandidate.Status.PENDING).count(), 24
        )

    def test_global_dedupe_skips_offer_rejected_other_family_and_existing_candidate(self):
        other = ProductFamily.objects.create(name="Other", slug="other")
        Offer.objects.create(source=Offer.Source.ALIEXPRESS, external_product_id="offer")
        OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="rejected",
            status=OfferCandidate.Status.REJECTED,
        )
        OfferCandidate.objects.create(
            product_family=other,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="other",
            status=OfferCandidate.Status.PENDING,
        )
        OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="existing",
            status=OfferCandidate.Status.PENDING,
        )
        client = Mock()
        client.search_products_diagnostic.return_value = AliExpressSearchResult(
            products=[self.product(value) for value in ("offer", "rejected", "other", "existing")]
        )
        result = discover_family_candidates(self.family, "diode laser", client=client)
        self.assertEqual(result.skipped_existing_offer, 1)
        self.assertEqual(result.skipped_previously_rejected, 1)
        self.assertEqual(result.skipped_known_other_family, 1)
        self.assertEqual(result.skipped_existing_candidate, 1)
        client.get_product_detail.assert_not_called()

    def test_laser_learning_labels_and_logistics_rejection_isolation(self):
        approved_titles = (
            "Professional picosecond laser tattoo removal machine",
            "Q-switched Nd:YAG tattoo removal machine",
            "Professional laser tattoo removal machine",
            "Diode laser picosecond tattoo removal machine",
        )
        for index, title in enumerate(approved_titles):
            OfferCandidate.objects.create(
                product_family=self.family,
                source=Offer.Source.ALIEXPRESS,
                external_product_id=f"approved-{index}",
                title=title,
                status=OfferCandidate.Status.APPROVED,
            )
        rejected = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="origin-only",
            title="Triple Wave diode laser hair removal machine",
            status=OfferCandidate.Status.REJECTED,
        )
        CandidateDecision.objects.create(
            candidate=rejected,
            decision=CandidateDecision.Decision.REJECT,
            reason=CandidateDecision.Reason.ORIGIN_NOT_ALLOWED,
            decided_by=self.user,
        )
        _, learned, negatives = _learning_inputs(self.family)
        for label in ("PICOSECOND", "Q-SWITCH ND:YAG", "TATTOO REMOVAL", "DIODE + PICO"):
            self.assertIn(label, learned)
        self.assertNotIn(rejected.title, negatives)
        self.assertGreaterEqual(len(LASER_TATTOO_PROFILE.search_keywords), 7)
