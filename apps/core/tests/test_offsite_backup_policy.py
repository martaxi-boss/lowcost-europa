from pathlib import Path

from django.test import SimpleTestCase


class OffsiteBackupPolicyTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = Path(__file__).resolve().parents[3]
        cls.backup = (root / "deploy/scripts/offsite-backup.sh").read_text()
        cls.health = (root / "deploy/scripts/check-offsite-backup-health.sh").read_text()
        cls.restore = (root / "deploy/scripts/offsite-restore-drill.sh").read_text()
        cls.service = (
            root / "deploy/systemd/lowcost-europa-offsite-backup.service"
        ).read_text()
        cls.timer = (
            root / "deploy/systemd/lowcost-europa-offsite-backup.timer"
        ).read_text()
        cls.health_timer = (
            root / "deploy/systemd/lowcost-europa-offsite-backup-health.timer"
        ).read_text()

    def test_backup_is_fail_closed_and_uses_dedicated_lock(self):
        self.assertIn("set -eu", self.backup)
        self.assertIn("umask 077", self.backup)
        self.assertIn("/run/lock/lowcost-europa-restic.lock", self.backup)
        self.assertIn("flock -n", self.backup)
        self.assertIn("root:root:600", self.backup)

    def test_backup_validates_local_dump_before_restic(self):
        self.assertIn("MAX_DUMP_AGE_SECONDS=21600", self.backup)
        self.assertIn("sha256sum -c", self.backup)
        self.assertIn("[ -s \"$latest_dump\" ]", self.backup)
        self.assertIn("6-hour freshness window", self.backup)

    def test_backup_scope_and_tags_are_explicit(self):
        self.assertIn('"$BACKUP_DIR"', self.backup)
        self.assertIn('"$APP_ENV"', self.backup)
        self.assertIn("--tag lowcost-europa", self.backup)
        self.assertIn("--tag offsite", self.backup)
        self.assertIn("--tag disaster-recovery", self.backup)
        self.assertNotIn("restic init", self.backup)

    def test_restic_bootstrap_secrets_are_not_backup_targets(self):
        backup_command = self.backup.split("restic backup", 1)[1]
        self.assertNotIn('"$PASSWORD_FILE"', backup_command)
        self.assertNotIn('"$R2_ENV"', backup_command)

    def test_restore_drill_isolated_and_non_database_mutating(self):
        self.assertIn("mktemp -d", self.restore)
        self.assertIn("restic restore latest", self.restore)
        self.assertIn("sha256sum -c", self.restore)
        self.assertIn("pg_restore --list", self.restore)
        self.assertNotIn("createdb", self.restore)
        self.assertNotIn("pg_restore --dbname", self.restore)

    def test_offsite_timer_runs_after_local_backup(self):
        self.assertIn("OnCalendar=*-*-* 03:45:00 UTC", self.timer)
        self.assertIn("Persistent=true", self.timer)
        self.assertIn("After=network-online.target lowcost-europa-backup.service", self.service)

    def test_health_policy_requires_recent_snapshot_and_repository_check(self):
        self.assertIn("MAX_SNAPSHOT_AGE_SECONDS=129600", self.health)
        self.assertIn("restic snapshots --json --latest 1", self.health)
        self.assertIn("restic check --no-cache", self.health)
        self.assertIn("OnCalendar=Sun *-*-* 05:15:00 UTC", self.health_timer)

    def test_units_preserve_restrictive_runtime_policy(self):
        for unit in (self.service,):
            self.assertIn("UMask=0077", unit)
            self.assertIn("NoNewPrivileges=true", unit)
            self.assertIn("PrivateTmp=true", unit)
            self.assertIn("ProtectSystem=full", unit)
            self.assertIn("ProtectHome=true", unit)
