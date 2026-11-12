from pathlib import Path
from unittest.mock import Mock, patch

from django.test import TestCase

from apps.catalog.models import OfferCandidate, ProductFamily
from apps.catalog.services.weekly_discovery import (
    PENDING_CAP_PER_FAMILY,
    WEEKLY_FAMILY_SLUGS,
    run_weekly_discovery,
)


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
    @patch("apps.catalog.services.weekly_discovery.AliExpressClient")
    def test_all_five_manual_queues_skip_discovery_without_api(self, client_factory, discover):
        report = run_weekly_discovery()
        self.assertEqual(
            [entry.family_slug for entry in report.families],
            list(WEEKLY_FAMILY_SLUGS),
        )
        self.assertTrue(all(entry.search_operations == 0 for entry in report.families))
        self.assertTrue(all(entry.new_candidates == 0 for entry in report.families))
        discover.assert_not_called()
        client_factory.assert_not_called()

    @patch("apps.catalog.services.weekly_discovery.discover_family_deep")
    def test_legacy_backlog_is_preserved_but_not_replenished(self, discover):
        diode = self.families["diodo-laser-remocao-tatuagens-pigmentacao"]
        hifu = self.families["hifu"]
        for family, count in ((diode, PENDING_CAP_PER_FAMILY), (hifu, 5)):
            for index in range(count):
                OfferCandidate.objects.create(
                    product_family=family,
                    source="ALIEXPRESS",
                    external_product_id=f"{family.slug}-{index}",
                )
        report = run_weekly_discovery(client=self.client)
        by_slug = {entry.family_slug: entry for entry in report.families}
        self.assertEqual(by_slug[diode.slug].pending_before, PENDING_CAP_PER_FAMILY)
        self.assertEqual(by_slug[diode.slug].pending_after, PENDING_CAP_PER_FAMILY)
        self.assertEqual(by_slug[hifu.slug].pending_before, 5)
        self.assertEqual(by_slug[hifu.slug].pending_after, 5)
        self.assertEqual(OfferCandidate.objects.count(), PENDING_CAP_PER_FAMILY + 5)
        discover.assert_not_called()

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
