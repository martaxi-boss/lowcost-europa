from unittest.mock import patch

from django.test import TestCase

from apps.catalog.models import Offer, OfferObservation
from apps.catalog.services.logistics_evidence import (
    LogisticsEvidenceState,
    assess_logistics_evidence,
)


class LogisticsEvidenceTests(TestCase):
    def assertAssessment(self, search, detail, state, supports):
        assessment = assess_logistics_evidence(
            search_delivery_days=search,
            detail_delivery_days=detail,
        )
        self.assertEqual(assessment.state, state)
        self.assertEqual(assessment.search_delivery_days, search)
        self.assertEqual(assessment.detail_delivery_days, detail)
        self.assertIs(assessment.supports_within_5_days, supports)
        self.assertFalse(hasattr(assessment, "score"))
        self.assertFalse(hasattr(assessment, "confidence_score"))
        self.assertFalse(hasattr(assessment, "effective_delivery_days"))

    def test_unknown(self):
        self.assertAssessment(None, None, LogisticsEvidenceState.UNKNOWN, False)

    def test_search_only_fast(self):
        self.assertAssessment(5, None, LogisticsEvidenceState.SEARCH_ONLY, True)

    def test_search_only_slow(self):
        self.assertAssessment(7, None, LogisticsEvidenceState.SEARCH_ONLY, False)

    def test_detail_only_fast(self):
        self.assertAssessment(None, 3, LogisticsEvidenceState.DETAIL_ONLY, True)

    def test_detail_only_slow(self):
        self.assertAssessment(None, 7, LogisticsEvidenceState.DETAIL_ONLY, False)

    def test_consistent_fast(self):
        self.assertAssessment(5, 5, LogisticsEvidenceState.CONSISTENT, True)

    def test_consistent_slow(self):
        self.assertAssessment(7, 7, LogisticsEvidenceState.CONSISTENT, False)

    def test_conflict_fast_slow(self):
        self.assertAssessment(5, 7, LogisticsEvidenceState.CONFLICT, False)

    def test_conflict_slow_fast(self):
        self.assertAssessment(7, 5, LogisticsEvidenceState.CONFLICT, False)

    def test_conflict_both_within_five_still_does_not_support(self):
        self.assertAssessment(3, 5, LogisticsEvidenceState.CONFLICT, False)

    def test_assessment_of_observation_values_has_zero_writes(self):
        offer = Offer.objects.create(source=Offer.Source.ALIEXPRESS, external_product_id="42")
        observation = OfferObservation.objects.create(
            offer=offer,
            search_delivery_days=5,
            delivery_days=None,
        )
        before = {
            "offers": Offer.objects.count(),
            "observations": OfferObservation.objects.count(),
            "observed_at": observation.observed_at,
            "search": observation.search_delivery_days,
            "detail": observation.delivery_days,
        }
        with patch.object(OfferObservation, "save", side_effect=AssertionError("save called")):
            assessment = assess_logistics_evidence(
                search_delivery_days=observation.search_delivery_days,
                detail_delivery_days=observation.delivery_days,
            )
        observation.refresh_from_db()
        self.assertEqual(assessment.state, LogisticsEvidenceState.SEARCH_ONLY)
        self.assertTrue(assessment.supports_within_5_days)
        self.assertEqual(Offer.objects.count(), before["offers"])
        self.assertEqual(OfferObservation.objects.count(), before["observations"])
        self.assertEqual(observation.observed_at, before["observed_at"])
        self.assertEqual(observation.search_delivery_days, before["search"])
        self.assertEqual(observation.delivery_days, before["detail"])
