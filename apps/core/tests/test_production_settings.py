import os
import subprocess
import sys

from django.test import SimpleTestCase


class ProductionSettingsTests(SimpleTestCase):
    def _run_settings_probe(self, script, **environment):
        env = os.environ.copy()
        env.update(environment)
        return subprocess.run(
            [sys.executable, "-c", script],
            cwd=os.getcwd(),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_production_security_defaults(self):
        script = """
from config.settings import production as settings
assert settings.DEBUG is False
assert settings.SECURE_SSL_REDIRECT is True
assert settings.SESSION_COOKIE_SECURE is True
assert settings.SESSION_COOKIE_HTTPONLY is True
assert settings.CSRF_COOKIE_SECURE is True
assert settings.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")
assert settings.SECURE_HSTS_SECONDS == 0
"""
        script += """
assert settings.SECURE_HSTS_INCLUDE_SUBDOMAINS is False
assert settings.SECURE_HSTS_PRELOAD is False
"""
        result = self._run_settings_probe(
            script,
            DJANGO_SECURE_SSL_REDIRECT="true",
            DJANGO_SECURE_HSTS_SECONDS="0",
            DJANGO_CSRF_TRUSTED_ORIGINS="",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_csrf_trusted_origins_are_loaded_from_environment(self):
        script = """
from config.settings import production as settings
assert settings.CSRF_TRUSTED_ORIGINS == [
    "https://shop.example.test",
    "https://admin.example.test",
]
"""
        result = self._run_settings_probe(
            script,
            DJANGO_CSRF_TRUSTED_ORIGINS=(
                "https://shop.example.test,https://admin.example.test"
            ),
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_hsts_is_environment_configurable(self):
        script = """
from config.settings import production as settings
assert settings.SECURE_HSTS_SECONDS == 3600
"""
        result = self._run_settings_probe(
            script,
            DJANGO_SECURE_HSTS_SECONDS="3600",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_hsts_value_fails_startup_clearly(self):
        script = "from config.settings import production"
        result = self._run_settings_probe(
            script,
            DJANGO_SECURE_HSTS_SECONDS="not-an-integer",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "DJANGO_SECURE_HSTS_SECONDS must be an integer",
            result.stderr,
        )

    def test_boolean_environment_values_are_strict(self):
        true_probe = self._run_settings_probe(
            "from config.settings.base import env_bool; assert env_bool('FLAG') is True",
            FLAG="  TrUe  ",
        )
        false_probe = self._run_settings_probe(
            "from config.settings.base import env_bool; assert env_bool('FLAG') is False",
            FLAG="false",
        )
        self.assertEqual(true_probe.returncode, 0, true_probe.stderr)
        self.assertEqual(false_probe.returncode, 0, false_probe.stderr)

    def test_invalid_secure_ssl_redirect_boolean_fails_startup(self):
        result = self._run_settings_probe(
            "from config.settings import production",
            DJANGO_SECURE_SSL_REDIRECT="not-a-boolean",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "DJANGO_SECURE_SSL_REDIRECT must be a boolean",
            result.stderr,
        )
