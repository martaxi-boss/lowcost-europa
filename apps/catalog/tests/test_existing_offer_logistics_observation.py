from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.utils import timezone

from apps.catalog.models import (
    CandidateDecision,
    Offer,
    OfferCandidate,
    OfferFamilyPlacement,
    OfferObservation,
    ProductFamily,
)
from apps.catalog.services.existing_offer_refresh import (
    ExistingOfferLogisticsObservationResult,
    observe_existing_offer_logistics,
)
from apps.catalog.services.logistics_evidence import assess_logistics_evidence
from apps.integrations.aliexpress.exceptions import (
    AliExpressAPIError,
    AliExpressRateLimitError,
    AliExpressResponseError,
    AliExpressTransportError,
)
from apps.integrations.aliexpress.types import AliExpressProduct, AliExpressSearchResult


def product(product_id="100", **overrides):
    values = {
        "product_id": product_id,
        "title": "Observed product",
        "image_url": "https://images.example/product.jpg",
        "product_url": "https://source.example/product",
        "price": Decimal("101.10"),
        "currency": "EUR",
        "original_price": Decimal("120.00"),
        "evaluation_rate_percent": Decimal("97.0"),
        "sales_count": 4,
        "commission_rate": Decimal("7.0"),
        "ship_to_days_raw": None,
        "delivery_days": None,
        "destination_country": "PT",
        "availability_raw": "available",
        "affiliate_url": "https://affiliate.example/generated-must-not-be-used",
    }
    values.update(overrides)
    return AliExpressProduct(**values)


class FakeSearchDetailClient:
    def __init__(
        self,
        *,
        search_products=None,
        detail_product=None,
        search_error=None,
        detail_error=None,
    ):
        self.search_products = search_products or []
        self.detail_product = detail_product
        self.search_error = search_error
        self.detail_error = detail_error
        self.search_calls = []
        self.detail_calls = []
        self.link_calls = []

    def search_products_diagnostic(self, keyword, **kwargs):
        self.search_calls.append((keyword, kwargs))
        if self.search_error:
            raise self.search_error
        return AliExpressSearchResult(products=self.search_products)

    def get_product_detail(self, product_id, country, currency):
        self.detail_calls.append((product_id, country, currency))
        if self.detail_error:
            raise self.detail_error
        return self.detail_product

    def generate_affiliate_link(self, source_url):
        self.link_calls.append(source_url)
        raise AssertionError("affiliate link generation must not be called")


class ExistingOfferLogisticsObservationTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.family = ProductFamily.objects.create(name="HIFU", slug="hifu")
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="100",
            product_family=self.family,
            title="Stored title",
            product_url="https://stored.example/product",
            image_url="https://stored.example/image.jpg",
            affiliate_url="https://stored.example/affiliate",
            ship_from_country="PL",
            ship_from_verified_at=timezone.now(),
            protocol_verified_at=timezone.now(),
            is_active=True,
            owner_hidden=True,
            is_primary=True,
            equipment_type=Offer.EquipmentType.DEDICATED,
        )
        self.placement = OfferFamilyPlacement.objects.create(
            offer=self.offer,
            product_family=self.family,
            selection_position=1,
            display_order=3,
            selection_reason="stored placement",
        )
        self.candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="100",
            status=OfferCandidate.Status.APPROVED,
            title="Stored candidate",
            approved_offer=self.offer,
        )
        self.user = get_user_model().objects.create_user(
            username="reviewer",
            password="unused-test-password",
            is_staff=True,
        )
        self.decision = CandidateDecision.objects.create(
            candidate=self.candidate,
            decision=CandidateDecision.Decision.APPROVE,
            ship_from_country="PL",
            review_signals=[CandidateDecision.ReviewSignal.DELIVERS_TO_PT_CONFIRMED],
            decided_by=self.user,
        )
        OfferObservation.objects.create(
            offer=self.offer,
            price=Decimal("99.00"),
            currency="EUR",
            availability=OfferObservation.Availability.UNKNOWN,
        )

    def _successful_client(self, *, detail=None, search=None):
        search = search or product(
            ship_to_days_raw="5",
            delivery_days=5,
            price=Decimal("88.88"),
        )
        detail = detail or product(
            ship_to_days_raw=None,
            delivery_days=None,
            price=Decimal("101.10"),
            original_price=Decimal("120.00"),
            evaluation_rate_percent=Decimal("97.0"),
            sales_count=4,
            commission_rate=Decimal("7.0"),
        )
        return FakeSearchDetailClient(
            search_products=[product("999"), search],
            detail_product=detail,
        )

    def _observe(self, client):
        return observe_existing_offer_logistics(
            self.offer,
            search_query="exact hifu product",
            client=client,
        )

    def test_exact_search_product_found_and_exact_detail_are_required(self):
        client = self._successful_client()
        result = self._observe(client)

        self.assertEqual(result.status, ExistingOfferLogisticsObservationResult.OBSERVED)
        self.assertEqual(result.search_product.product_id, "100")
        self.assertEqual(result.detail_product.product_id, "100")
        self.assertEqual(
            client.search_calls,
            [
                (
                    "exact hifu product",
                    {"country": "PT", "currency": "EUR", "delivery_days": 5},
                )
            ],
        )
        self.assertEqual(client.detail_calls, [("100", "PT", "EUR")])
        self.assertEqual(client.link_calls, [])

    def test_search_only_five_day_evidence_is_preserved_without_copying_to_detail(self):
        client = self._successful_client()
        result = self._observe(client)
        observation = result.observation

        self.assertEqual(observation.search_ship_to_days_raw, "5")
        self.assertEqual(observation.search_delivery_days, 5)
        self.assertIsNone(observation.ship_to_days_raw)
        self.assertIsNone(observation.delivery_days)

        evidence = assess_logistics_evidence(
            search_delivery_days=observation.search_delivery_days,
            detail_delivery_days=observation.delivery_days,
        )
        self.assertEqual(evidence.state.value, "SEARCH_ONLY")
        self.assertTrue(evidence.supports_within_5_days)

    def test_detail_commercial_fields_are_primary_and_availability_available(self):
        client = self._successful_client()
        observation = self._observe(client).observation

        self.assertEqual(observation.destination_country, "PT")
        self.assertEqual(observation.price, Decimal("101.10"))
        self.assertEqual(observation.original_price, Decimal("120.00"))
        self.assertEqual(observation.currency, "EUR")
        self.assertEqual(observation.evaluation_rate_percent, Decimal("97.0"))
        self.assertEqual(observation.sales_count, 4)
        self.assertEqual(observation.commission_rate, Decimal("7.0"))
        self.assertEqual(observation.availability, OfferObservation.Availability.AVAILABLE)

    def test_factually_unavailable_detail_persists_unavailable_without_deactivating_offer(self):
        client = self._successful_client(
            detail=product(availability_raw="unavailable")
        )
        observation = self._observe(client).observation

        self.assertEqual(
            observation.availability,
            OfferObservation.Availability.UNAVAILABLE,
        )
        self.offer.refresh_from_db()
        self.assertTrue(self.offer.is_active)

    def test_ambiguous_detail_persists_unknown(self):
        client = self._successful_client(
            detail=product(title=None, product_url=None, availability_raw=None)
        )
        observation = self._observe(client).observation
        self.assertEqual(observation.availability, OfferObservation.Availability.UNKNOWN)

    def test_exact_product_absent_returns_controlled_result_and_zero_observation(self):
        before = OfferObservation.objects.filter(offer=self.offer).count()
        client = FakeSearchDetailClient(
            search_products=[product("999")],
            detail_product=product(),
        )

        result = self._observe(client)

        self.assertEqual(
            result.status,
            ExistingOfferLogisticsObservationResult.EXACT_PRODUCT_NOT_FOUND,
        )
        self.assertIsNone(result.observation)
        self.assertEqual(client.detail_calls, [])
        self.assertEqual(OfferObservation.objects.filter(offer=self.offer).count(), before)

    def test_wrong_detail_product_id_creates_zero_observation(self):
        before = OfferObservation.objects.filter(offer=self.offer).count()
        client = self._successful_client(detail=product("WRONG"))

        with self.assertRaises(AliExpressResponseError):
            self._observe(client)

        self.assertEqual(OfferObservation.objects.filter(offer=self.offer).count(), before)

    def test_search_structural_error_propagates_and_creates_zero_observation(self):
        before = OfferObservation.objects.filter(offer=self.offer).count()
        client = FakeSearchDetailClient(
            search_error=AliExpressResponseError("sanitized structural failure")
        )

        with self.assertRaises(AliExpressResponseError):
            self._observe(client)

        self.assertEqual(client.detail_calls, [])
        self.assertEqual(OfferObservation.objects.filter(offer=self.offer).count(), before)

    def test_detail_structural_error_propagates_and_creates_zero_observation(self):
        before = OfferObservation.objects.filter(offer=self.offer).count()
        client = FakeSearchDetailClient(
            search_products=[product(ship_to_days_raw="5", delivery_days=5)],
            detail_error=AliExpressResponseError("sanitized detail failure"),
        )

        with self.assertRaises(AliExpressResponseError):
            self._observe(client)

        self.assertEqual(OfferObservation.objects.filter(offer=self.offer).count(), before)

    def test_rate_limit_error_propagates_and_creates_zero_observation(self):
        before = OfferObservation.objects.filter(offer=self.offer).count()
        client = FakeSearchDetailClient(
            search_error=AliExpressRateLimitError("rate limited")
        )

        with self.assertRaises(AliExpressRateLimitError):
            self._observe(client)

        self.assertEqual(OfferObservation.objects.filter(offer=self.offer).count(), before)

    def test_other_api_and_transport_errors_create_zero_observation(self):
        for error in (
            AliExpressAPIError("api"),
            AliExpressTransportError("transport"),
        ):
            before = OfferObservation.objects.filter(offer=self.offer).count()
            client = FakeSearchDetailClient(search_error=error)
            with self.assertRaises(type(error)):
                self._observe(client)
            self.assertEqual(
                OfferObservation.objects.filter(offer=self.offer).count(),
                before,
            )

    def test_offer_editorial_lifecycle_and_related_records_are_preserved(self):
        offer_before = {
            "owner_hidden": self.offer.owner_hidden,
            "protocol_verified_at": self.offer.protocol_verified_at,
            "product_family_id": self.offer.product_family_id,
            "affiliate_url": self.offer.affiliate_url,
            "external_product_id": self.offer.external_product_id,
            "source": self.offer.source,
            "ship_from_country": self.offer.ship_from_country,
            "ship_from_verified_at": self.offer.ship_from_verified_at,
            "is_primary": self.offer.is_primary,
            "is_active": self.offer.is_active,
            "title": self.offer.title,
            "product_url": self.offer.product_url,
            "image_url": self.offer.image_url,
            "last_seen_at": self.offer.last_seen_at,
            "updated_at": self.offer.updated_at,
        }
        placement_before = (
            self.placement.product_family_id,
            self.placement.selection_position,
            self.placement.display_order,
            self.placement.selection_reason,
        )
        candidate_before = (
            self.candidate.status,
            self.candidate.product_family_id,
            self.candidate.approved_offer_id,
            self.candidate.updated_at,
        )
        decision_before = (
            self.decision.decision,
            self.decision.ship_from_country,
            list(self.decision.review_signals),
            self.decision.decided_at,
        )

        result = self._observe(self._successful_client())
        self.assertIsNotNone(result.observation)

        self.offer.refresh_from_db()
        self.placement.refresh_from_db()
        self.candidate.refresh_from_db()
        self.decision.refresh_from_db()

        offer_after = {
            "owner_hidden": self.offer.owner_hidden,
            "protocol_verified_at": self.offer.protocol_verified_at,
            "product_family_id": self.offer.product_family_id,
            "affiliate_url": self.offer.affiliate_url,
            "external_product_id": self.offer.external_product_id,
            "source": self.offer.source,
            "ship_from_country": self.offer.ship_from_country,
            "ship_from_verified_at": self.offer.ship_from_verified_at,
            "is_primary": self.offer.is_primary,
            "is_active": self.offer.is_active,
            "title": self.offer.title,
            "product_url": self.offer.product_url,
            "image_url": self.offer.image_url,
            "last_seen_at": self.offer.last_seen_at,
            "updated_at": self.offer.updated_at,
        }
        self.assertEqual(offer_after, offer_before)
        self.assertEqual(
            (
                self.placement.product_family_id,
                self.placement.selection_position,
                self.placement.display_order,
                self.placement.selection_reason,
            ),
            placement_before,
        )
        self.assertEqual(
            (
                self.candidate.status,
                self.candidate.product_family_id,
                self.candidate.approved_offer_id,
                self.candidate.updated_at,
            ),
            candidate_before,
        )
        self.assertEqual(
            (
                self.decision.decision,
                self.decision.ship_from_country,
                list(self.decision.review_signals),
                self.decision.decided_at,
            ),
            decision_before,
        )

    def test_inactive_offer_is_not_reactivated(self):
        self.offer.is_active = False
        self.offer.is_primary = False
        self.offer.save(update_fields=["is_active", "is_primary", "updated_at"])

        self._observe(self._successful_client())

        self.offer.refresh_from_db()
        self.assertFalse(self.offer.is_active)
        self.assertFalse(self.offer.is_primary)
