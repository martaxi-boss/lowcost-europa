import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from django.test import SimpleTestCase


class OffsiteBackupHealthSizeTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.root = Path(__file__).resolve().parents[3]
        cls.health_script = cls.root / "deploy/scripts/check-offsite-backup-health.sh"

    def _run_health(self, stats_mode):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bin_dir = tmp_path / "bin"
            bin_dir.mkdir()
            r2_env = tmp_path / "r2.env"
            password = tmp_path / "restic-password"
            marker = tmp_path / "offsite-backup.last-success"
            lock_file = tmp_path / "restic.lock"
            fake_restic = bin_dir / "fake-restic"
            fake_stat = bin_dir / "stat"

            r2_env.write_text(
                "AWS_ACCESS_KEY_ID=test-key\n"
                "AWS_SECRET_ACCESS_KEY=test-secret\n"
                "RESTIC_REPOSITORY=test-repository\n"
            )
            password.write_text("test-password\n")
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            marker.write_text(f"timestamp={timestamp}\nsnapshot=test1234\n")
            for path in (r2_env, password, marker):
                path.chmod(0o600)

            fake_stat.write_text(
                "#!/bin/sh\n"
                "if [ \"$1\" = \"-c\" ] && [ \"$2\" = \"%U:%G:%a\" ]; then\n"
                "  echo root:root:600\n"
                "  exit 0\n"
                "fi\n"
                "exec /usr/bin/stat \"$@\"\n"
            )
            fake_stat.chmod(0o755)

            fake_restic.write_text(
                "#!/bin/sh\n"
                "case \"$1\" in\n"
                "  snapshots)\n"
                "    printf '%s\\n' \"[{\\\"time\\\":\\\"$FAKE_TIMESTAMP\\\","
                "\\\"short_id\\\":\\\"test1234\\\"}]\"\n"
                "    ;;\n"
                "  check) exit 0 ;;\n"
                "  stats)\n"
                "    case \" $* \" in *\" --tag \"*|*\" --host \"*) exit 45 ;; esac\n"
                "    case \"$FAKE_STATS_MODE\" in\n"
                "      below) echo '{\"total_size\":7999999999}' ;;\n"
                "      equal) echo '{\"total_size\":8000000000}' ;;\n"
                "      above) echo '{\"total_size\":8000000001}' ;;\n"
                "      fail) exit 42 ;;\n"
                "      invalid-json) echo 'not-json' ;;\n"
                "      missing) echo '{\"snapshots_count\":3}' ;;\n"
                "      string) echo '{\"total_size\":\"8000000000\"}' ;;\n"
                "      negative) echo '{\"total_size\":-1}' ;;\n"
                "      *) exit 43 ;;\n"
                "    esac\n"
                "    ;;\n"
                "  *) exit 44 ;;\n"
                "esac\n"
            )
            fake_restic.chmod(0o755)

            env = os.environ.copy()
            env.update(
                {
                    "R2_ENV": str(r2_env),
                    "PASSWORD_FILE": str(password),
                    "LOCK_FILE": str(lock_file),
                    "SUCCESS_MARKER": str(marker),
                    "RESTIC_BIN": str(fake_restic),
                    "FAKE_STATS_MODE": stats_mode,
                    "FAKE_TIMESTAMP": timestamp,
                    "PATH": f"{bin_dir}:{env['PATH']}",
                }
            )
            return subprocess.run(
                [str(self.health_script)],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

    def test_repository_size_just_below_threshold_passes(self):
        result = self._run_health("below")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "REPOSITORY SIZE: OK observed=7999999999 threshold=8000000000",
            result.stdout,
        )
        self.assertNotIn("WARNING:", result.stdout + result.stderr)

    def test_repository_size_at_threshold_warns_and_fails(self):
        result = self._run_health("equal")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "WARNING: Restic repository reached or exceeded the 8 GB operational "
            "warning threshold. observed=8000000000 threshold=8000000000",
            result.stderr,
        )

    def test_repository_size_above_threshold_warns_and_fails(self):
        result = self._run_health("above")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("observed=8000000001 threshold=8000000000", result.stderr)

    def test_stats_command_failure_fails_closed(self):
        result = self._run_health("fail")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("REPOSITORY SIZE: OK", result.stdout + result.stderr)

    def test_invalid_stats_json_fails_closed(self):
        result = self._run_health("invalid-json")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("REPOSITORY SIZE: OK", result.stdout + result.stderr)

    def test_missing_total_size_fails_closed(self):
        result = self._run_health("missing")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing total_size", result.stderr)
        self.assertNotIn("REPOSITORY SIZE: OK", result.stdout + result.stderr)

    def test_non_integer_total_size_fails_closed(self):
        result = self._run_health("string")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not an integer", result.stderr)

    def test_negative_total_size_fails_closed(self):
        result = self._run_health("negative")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("is negative", result.stderr)
