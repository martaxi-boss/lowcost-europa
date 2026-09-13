from datetime import timedelta
from io import StringIO
from types import SimpleNamespace

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TransactionTestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.catalog.models import Offer, OfferObservation
from apps.catalog.services.logistics_evidence import LogisticsEvidenceState
from apps.catalog.services.logistics_freshness import LogisticsFreshnessState
from apps.catalog.services.logistics_history import (
    assess_logistics_history,
    assess_offer_logistics_history,
)

MAX_AGE = timedelta(hours=24)


def observation(observed_at, search=None, detail=None, pk=None):
    return SimpleNamespace(
        pk=pk,
        observed_at=observed_at,
        search_delivery_days=search,
        delivery_days=detail,
    )


class LogisticsHistoryPureTests(TransactionTestCase):
    def setUp(self):
        self.as_of = timezone.now()

    def test_empty_history(self):
        result = assess_logistics_history(observations=[], as_of=self.as_of, max_age=MAX_AGE)
        self.assertEqual(result.observation_count, 0)
        self.assertIsNone(result.first_observed_at)
        self.assertIsNone(result.last_observed_at)
        self.assertIsNone(result.observation_span)
        self.assertIsNone(result.latest)

    def test_single_history(self):
        obs = observation(self.as_of - timedelta(hours=1), search=5)
        result = assess_logistics_history(observations=[obs], as_of=self.as_of, max_age=MAX_AGE)
        self.assertEqual(result.observation_count, 1)
        self.assertEqual(result.observation_span, timedelta(0))
        self.assertEqual(result.evidence_state_counts[LogisticsEvidenceState.SEARCH_ONLY], 1)
        self.assertEqual(result.freshness_state_counts[LogisticsFreshnessState.FRESH], 1)
        self.assertEqual(result.supports_5d_count, 1)
        self.assertEqual(result.supports_current_5d_count, 1)

    def test_mixed_history_counts_and_conflict(self):
        observations = [
            observation(self.as_of - timedelta(days=2), search=5),
            observation(self.as_of - timedelta(hours=2), search=5, detail=7),
            observation(self.as_of - timedelta(hours=1), search=5),
        ]
        result = assess_logistics_history(
            observations=observations, as_of=self.as_of, max_age=MAX_AGE
        )
        self.assertEqual(result.observation_count, 3)
        self.assertEqual(result.supports_5d_count, 2)
        self.assertEqual(result.supports_current_5d_count, 1)
        self.assertTrue(result.has_conflict)

    def test_future_and_ordering(self):
        old = observation(self.as_of - timedelta(hours=3), search=5, pk=1)
        future = observation(self.as_of + timedelta(seconds=1), search=5, pk=2)
        middle = observation(self.as_of - timedelta(hours=1), search=None, detail=5, pk=3)
        result = assess_logistics_history(
            observations=[future, old, middle],
            as_of=self.as_of,
            max_age=MAX_AGE,
        )
        self.assertTrue(result.has_future)
        self.assertEqual(result.supports_current_5d_count, 2)
        self.assertEqual(result.latest.observation_pk, 2)
        self.assertEqual(result.latest.freshness_state, LogisticsFreshnessState.FUTURE)
        self.assertFalse(result.latest.supports_current_5d)

    def test_equal_timestamp_latest_uses_pk(self):
        stamp = self.as_of - timedelta(hours=1)
        first = observation(stamp, search=5, pk=2)
        second = observation(stamp, detail=5, pk=9)
        result = assess_logistics_history(
            observations=[second, first], as_of=self.as_of, max_age=MAX_AGE
        )
        self.assertEqual(result.latest.observation_pk, 9)

    def test_multiple_all_positive_is_only_counts(self):
        observations = [
            observation(self.as_of - timedelta(hours=3), search=5),
            observation(self.as_of - timedelta(hours=2), detail=3),
            observation(self.as_of - timedelta(hours=1), search=5, detail=5),
        ]
        result = assess_logistics_history(
            observations=observations, as_of=self.as_of, max_age=MAX_AGE
        )
        self.assertEqual(result.supports_current_5d_count, 3)
        self.assertFalse(hasattr(result, "stable"))
        self.assertFalse(hasattr(result, "commercially_usable"))


class LogisticsHistoryOrmTests(TransactionTestCase):
    def setUp(self):
        self.as_of = timezone.now()
        self.offer_a = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="A",
        )
        self.offer_b = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="B",
        )

    def _create_obs(self, offer, *, hours_ago, search=None, detail=None):
        return OfferObservation.objects.create(
            offer=offer,
            observed_at=self.as_of - timedelta(hours=hours_ago),
            search_delivery_days=search,
            delivery_days=detail,
        )

    def test_one_offer_only_one_select_and_zero_writes(self):
        self._create_obs(self.offer_a, hours_ago=2, search=5)
        self._create_obs(self.offer_a, hours_ago=1, search=5)
        self._create_obs(self.offer_b, hours_ago=1, search=7)
        with CaptureQueriesContext(connection) as queries:
            result = assess_offer_logistics_history(
                offer=self.offer_a, as_of=self.as_of, max_age=MAX_AGE
            )
        self.assertEqual(result.observation_count, 2)
        statements = [q["sql"].lstrip().upper() for q in queries.captured_queries]
        self.assertEqual(len(statements), 1)
        self.assertTrue(statements[0].startswith("SELECT"))

    def test_command_offer_not_found(self):
        with self.assertRaisesRegex(CommandError, "Offer not found"):
            call_command("aliexpress_logistics_history", product_id="missing")

    def test_command_empty_history(self):
        out = StringIO()
        call_command("aliexpress_logistics_history", product_id="A", stdout=out)
        text = out.getvalue()
        self.assertIn("Observations: 0", text)
        self.assertIn("No logistics history available", text)

    def test_command_history_summary(self):
        self._create_obs(self.offer_a, hours_ago=2, search=5)
        self._create_obs(self.offer_a, hours_ago=1, search=5, detail=7)
        out = StringIO()
        call_command("aliexpress_logistics_history", product_id="A", stdout=out)
        text = out.getvalue()
        self.assertIn("Observations: 2", text)
        self.assertIn("SEARCH_ONLY: 1", text)
        self.assertIn("CONFLICT: 1", text)
        self.assertIn("Has conflict: yes", text)
        self.assertIn("Latest:", text)
        self.assertNotIn("http", text.lower())
