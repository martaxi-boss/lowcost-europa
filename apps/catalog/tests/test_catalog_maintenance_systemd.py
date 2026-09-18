from pathlib import Path

from django.test import SimpleTestCase


class CatalogMaintenanceSystemdPolicyTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = Path(__file__).resolve().parents[3]
        cls.timer = (root / "deploy/systemd/lowcost-europa-catalog-maintenance.timer").read_text()
        cls.service = (
            root / "deploy/systemd/lowcost-europa-catalog-maintenance.service"
        ).read_text()

    def test_hourly_timer_policy_is_versioned(self):
        self.assertIn("OnBootSec=15min", self.timer)
        self.assertIn("OnUnitActiveSec=1h", self.timer)
        self.assertIn("Persistent=true", self.timer)

    def test_batch_ten_service_policy_is_versioned(self):
        self.assertIn(
            "manage.py maintain_catalog_offers --batch-size 10",
            self.service,
        )
