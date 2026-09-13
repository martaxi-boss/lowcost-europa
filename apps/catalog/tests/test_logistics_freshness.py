from datetime import datetime, timedelta, timezone

from django.test import TestCase

from apps.catalog.models import Offer, OfferObservation
from apps.catalog.services.logistics_evidence import assess_logistics_evidence
from apps.catalog.services.logistics_freshness import (
    LogisticsFreshnessState,
    assess_logistics_freshness,
    supports_current_5d_candidate,
)

UTC = timezone.utc
AS_OF = datetime(2026, 9, 13, 14, 0, tzinfo=UTC)
MAX_AGE = timedelta(hours=24)


class LogisticsFreshnessTests(TestCase):
    def assess(self, observed_at, *, as_of=AS_OF, max_age=MAX_AGE):
        return assess_logistics_freshness(
            observed_at=observed_at,
            as_of=as_of,
            max_age=max_age,
        )

    def test_age_zero_is_fresh(self):
        result = self.assess(AS_OF)
        self.assertEqual(result.state, LogisticsFreshnessState.FRESH)
        self.assertTrue(result.is_fresh)
        self.assertEqual(result.age, timedelta(0))

    def test_exact_max_age_is_fresh(self):
        result = self.assess(AS_OF - MAX_AGE)
        self.assertEqual(result.state, LogisticsFreshnessState.FRESH)
        self.assertTrue(result.is_fresh)
        self.assertEqual(result.age, MAX_AGE)

    def test_after_max_age_is_stale(self):
        result = self.assess(AS_OF - MAX_AGE - timedelta(seconds=1))
        self.assertEqual(result.state, LogisticsFreshnessState.STALE)
        self.assertFalse(result.is_fresh)

    def test_future_timestamp_is_not_clamped(self):
        result = self.assess(AS_OF + timedelta(seconds=1))
        self.assertEqual(result.state, LogisticsFreshnessState.FUTURE)
        self.assertFalse(result.is_fresh)
        self.assertEqual(result.age, timedelta(seconds=-1))

    def test_naive_observed_at_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "observed_at must be timezone-aware"):
            self.assess(datetime(2026, 9, 13, 14, 0))

    def test_naive_as_of_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "as_of must be timezone-aware"):
            self.assess(AS_OF, as_of=datetime(2026, 9, 13, 14, 0))

    def test_zero_and_negative_max_age_are_rejected(self):
        for max_age in (timedelta(0), timedelta(seconds=-1)):
            with self.assertRaisesRegex(ValueError, "max_age must be greater than zero"):
                self.assess(AS_OF, max_age=max_age)

    def test_composition_fresh_search_only_fast_is_true(self):
        evidence = assess_logistics_evidence(
            search_delivery_days=5,
            detail_delivery_days=None,
        )
        freshness = self.assess(AS_OF - timedelta(minutes=5))
        self.assertTrue(supports_current_5d_candidate(evidence=evidence, freshness=freshness))

    def test_composition_stale_search_only_fast_is_false(self):
        evidence = assess_logistics_evidence(
            search_delivery_days=5,
            detail_delivery_days=None,
        )
        freshness = self.assess(AS_OF - timedelta(days=2))
        self.assertFalse(supports_current_5d_candidate(evidence=evidence, freshness=freshness))

    def test_composition_fresh_conflict_and_unknown_are_false(self):
        freshness = self.assess(AS_OF - timedelta(minutes=5))
        conflict = assess_logistics_evidence(search_delivery_days=5, detail_delivery_days=7)
        unknown = assess_logistics_evidence(search_delivery_days=None, detail_delivery_days=None)
        self.assertFalse(supports_current_5d_candidate(evidence=conflict, freshness=freshness))
        self.assertFalse(supports_current_5d_candidate(evidence=unknown, freshness=freshness))

    def test_composition_future_is_false(self):
        evidence = assess_logistics_evidence(search_delivery_days=5, detail_delivery_days=None)
        freshness = self.assess(AS_OF + timedelta(seconds=1))
        self.assertFalse(supports_current_5d_candidate(evidence=evidence, freshness=freshness))

    def test_service_performs_zero_queries_or_writes(self):
        before = (Offer.objects.count(), OfferObservation.objects.count())
        with self.assertNumQueries(0):
            result = self.assess(AS_OF - timedelta(minutes=1))
        after = (Offer.objects.count(), OfferObservation.objects.count())
        self.assertEqual(before, after)
        self.assertEqual(result.state, LogisticsFreshnessState.FRESH)
