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
        self.assertIn('[ -s "$latest_dump" ]', self.backup)
        self.assertIn("6-hour freshness window", self.backup)

    def test_retention_policy_is_743_and_scoped(self):
        self.assertIn("restic forget", self.backup)
        self.assertIn("--keep-daily 7", self.backup)
        self.assertIn("--keep-weekly 4", self.backup)
        self.assertIn("--keep-monthly 3", self.backup)
        self.assertIn("--group-by host,paths", self.backup)
        self.assertIn("--tag lowcost-europa", self.backup)
        self.assertIn("--tag offsite", self.backup)
        self.assertIn("restic prune --no-cache", self.backup)

    def test_backup_validation_retention_prune_and_marker_order(self):
        backup_at = self.backup.index("restic backup")
        validate_at = self.backup.index("restic check --no-cache", backup_at)
        forget_at = self.backup.index("restic forget", validate_at)
        prune_at = self.backup.index("restic prune --no-cache", forget_at)
        marker_at = self.backup.index('python3 - "$SUCCESS_MARKER"', prune_at)
        self.assertLess(backup_at, validate_at)
        self.assertLess(validate_at, forget_at)
        self.assertLess(forget_at, prune_at)
        self.assertLess(prune_at, marker_at)

    def test_success_marker_is_atomic_and_restrictive(self):
        self.assertIn("STATE_DIR=/var/lib/lowcost-europa", self.backup)
        self.assertIn("SUCCESS_MARKER=$STATE_DIR/offsite-backup.last-success", self.backup)
        self.assertIn("install -d -o root -g root -m 0700", self.backup)
        self.assertIn("os.fchmod(fd, 0o600)", self.backup)
        self.assertIn("os.fsync(handle.fileno())", self.backup)
        self.assertIn("os.replace(tmp, marker)", self.backup)

    def test_backup_scope_does_not_include_bootstrap_secrets(self):
        backup_command = self.backup.split("restic backup", 1)[1].split("snapshot_json=", 1)[0]
        self.assertIn('"$BACKUP_DIR"', backup_command)
        self.assertIn('"$APP_ENV"', backup_command)
        self.assertNotIn('"$PASSWORD_FILE"', backup_command)
        self.assertNotIn('"$R2_ENV"', backup_command)
        self.assertNotIn("restic init", self.backup)

    def test_health_requires_marker_snapshot_and_repository(self):
        self.assertIn("MAX_MARKER_AGE_SECONDS=129600", self.health)
        self.assertIn("MAX_SNAPSHOT_AGE_SECONDS=129600", self.health)
        self.assertIn("offsite-backup.last-success", self.health)
        self.assertIn("restic snapshots --json --latest 1", self.health)
        self.assertIn("restic check --no-cache", self.health)

    def test_health_timer_is_daily_after_backup_window(self):
        self.assertIn("OnCalendar=*-*-* 05:15:00 UTC", self.health_timer)
        self.assertIn("Persistent=true", self.health_timer)
        self.assertNotIn("OnCalendar=Sun", self.health_timer)

    def test_restore_drill_uses_real_temporary_postgres_database(self):
        self.assertIn("lowcost_europa_restic_restore_", self.restore)
        self.assertIn("createdb", self.restore)
        self.assertIn("runuser -u postgres -- pg_restore", self.restore)
        self.assertIn('--dbname="$temp_db"', self.restore)
        self.assertIn('dropdb --if-exists "$temp_db"', self.restore)
        self.assertIn('[ "$temp_db" != "$live_db" ]', self.restore)

    def test_restore_validates_migrations_and_core_catalog(self):
        self.assertIn("django_migrations", self.restore)
        self.assertIn("catalog_productfamily", self.restore)
        self.assertIn("catalog_offer", self.restore)
        self.assertIn("CORE CATALOG READ=PASS", self.restore)

    def test_restore_cleanup_is_fail_safe(self):
        self.assertIn("trap cleanup EXIT HUP INT TERM", self.restore)
        self.assertIn('rm -rf "$target"', self.restore)
        self.assertIn("TEMP DATABASE DROPPED=", self.restore)
        self.assertIn("RESTORE TEMP DIRECTORY REMOVED=", self.restore)

    def test_offsite_timer_runs_after_local_backup(self):
        self.assertIn("OnCalendar=*-*-* 03:45:00 UTC", self.timer)
        self.assertIn("Persistent=true", self.timer)
        self.assertIn("After=network-online.target lowcost-europa-backup.service", self.service)

    def test_no_restic_init_is_versioned(self):
        for script in (self.backup, self.health, self.restore):
            self.assertNotIn("restic init", script)
