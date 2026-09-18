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
        cls.web_service = (root / "deploy/systemd/lowcost-europa.service").read_text()
        cls.tmpfiles = (root / "deploy/tmpfiles.d/lowcost-europa.conf").read_text()

    def test_hourly_timer_policy_is_versioned(self):
        self.assertIn("OnBootSec=15min", self.timer)
        self.assertIn("OnUnitActiveSec=1h", self.timer)
        self.assertIn("Persistent=true", self.timer)

    def test_batch_ten_service_policy_is_versioned(self):
        self.assertIn(
            "manage.py maintain_catalog_offers --batch-size 10",
            self.service,
        )

    def test_shared_runtime_directory_policy_is_versioned(self):
        self.assertIn(
            "d /run/lowcost-europa 0750 le001_1789265592 le001_1789265592 -",
            self.tmpfiles,
        )

    def test_private_tmp_is_preserved_for_web_and_maintenance(self):
        self.assertIn("PrivateTmp=true", self.web_service)
        self.assertIn("PrivateTmp=true", self.service)
