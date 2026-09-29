from pathlib import Path
from unittest.mock import Mock, patch

from django.test import TestCase

from apps.catalog.models import OfferCandidate, ProductFamily
from apps.catalog.services.deep_discovery import DeepDiscoveryResult
from apps.catalog.services.weekly_discovery import (
    PENDING_CAP_PER_FAMILY,
    WEEKLY_FAMILY_SLUGS,
    run_weekly_discovery,
)
from apps.integrations.aliexpress.exceptions import AliExpressRateLimitError


class WeeklyDiscoveryTests(TestCase):
    def setUp(self):
        self.families = {
            slug: ProductFamily.objects.create(
                name=slug,
                slug=slug,
                display_order=index,
            )
            for index, slug in enumerate(WEEKLY_FAMILY_SLUGS)
        }
        self.client = Mock()

    @patch("apps.catalog.services.weekly_discovery.discover_family_deep")
    def test_one_campaign_covers_all_five_families_sequentially(self, discover):
        order = []

        def fake(family, keywords, **kwargs):
            order.append((family.slug, kwargs["client"]))
            return DeepDiscoveryResult()

        discover.side_effect = fake

        report = run_weekly_discovery(client=self.client)

        self.assertEqual([item.family_slug for item in report.families], list(WEEKLY_FAMILY_SLUGS))
        self.assertEqual([slug for slug, _client in order], list(WEEKLY_FAMILY_SLUGS))
        self.assertTrue(all(client is self.client for _slug, client in order))
        self.assertEqual(discover.call_count, 5)

    @patch("apps.catalog.services.weekly_discovery.discover_family_deep")
    def test_pending_cap_skips_full_family_without_spending_api_budget(self, discover):
        diode = self.families["diodo-laser-remocao-tatuagens-pigmentacao"]
        for index in range(PENDING_CAP_PER_FAMILY):
            OfferCandidate.objects.create(
                product_family=diode,
                source="ALIEXPRESS",
                external_product_id=f"full-{index}",
            )
        called = []

        def fake(family, keywords, **kwargs):
            called.append(family.slug)
            return DeepDiscoveryResult()

        discover.side_effect = fake

        report = run_weekly_discovery(client=self.client)
        diode_result = next(
            item
            for item in report.families
            if item.family_slug == "diodo-laser-remocao-tatuagens-pigmentacao"
        )

        self.assertTrue(diode_result.queue_cap_hit)
        self.assertEqual(diode_result.pending_before, PENDING_CAP_PER_FAMILY)
        self.assertEqual(diode_result.pending_after, PENDING_CAP_PER_FAMILY)
        self.assertNotIn("diodo-laser-remocao-tatuagens-pigmentacao", called)
        self.assertEqual(len(called), 4)

    @patch("apps.catalog.services.weekly_discovery.discover_family_deep")
    def test_low_queues_are_processed_before_high_backlog(self, discover):
        hifu = self.families["hifu"]
        for index in range(5):
            OfferCandidate.objects.create(
                product_family=hifu,
                source="ALIEXPRESS",
                external_product_id=f"hifu-backlog-{index}",
            )
        order = []

        def fake(family, keywords, **kwargs):
            order.append(family.slug)
            return DeepDiscoveryResult()

        discover.side_effect = fake
        run_weekly_discovery(client=self.client)

        self.assertEqual(order[-1], "hifu")

    @patch("apps.catalog.services.weekly_discovery.discover_family_deep")
    def test_persistent_rate_limit_aborts_remaining_campaign(self, discover):
        calls = 0

        def fake(family, keywords, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                exc = AliExpressRateLimitError("persistent 429")
                exc.deep_discovery_result = DeepDiscoveryResult()
                raise exc
            return DeepDiscoveryResult()

        discover.side_effect = fake

        with self.assertRaises(AliExpressRateLimitError) as caught:
            run_weekly_discovery(client=self.client)

        self.assertEqual(discover.call_count, 2)
        self.assertTrue(hasattr(caught.exception, "weekly_discovery_report"))

    def test_systemd_timer_is_weekly_persistent_and_single_campaign(self):
        root = Path(__file__).resolve().parents[3]
        timer = (
            root / "deploy/systemd/lowcost-europa-weekly-discovery.timer"
        ).read_text()
        service = (
            root / "deploy/systemd/lowcost-europa-weekly-discovery.service"
        ).read_text()

        self.assertIn("OnCalendar=Mon *-*-* 23:40:00 UTC", timer)
        self.assertIn("Persistent=true", timer)
        self.assertIn("run_weekly_discovery", service)
        self.assertIn("User=le001_1789265592", service)
        self.assertNotIn("discover_family_deep --family", service)
