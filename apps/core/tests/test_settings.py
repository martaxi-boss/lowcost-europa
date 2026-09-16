from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase

from config.settings.base import env_int_range


class SettingsTests(SimpleTestCase):
    def test_postgresql_backend_is_configured(self):
        self.assertEqual(settings.DATABASES["default"]["ENGINE"], "django.db.backends.postgresql")

    def test_secret_key_is_loaded(self):
        self.assertTrue(settings.SECRET_KEY)

    def test_production_style_defaults_are_safe(self):
        self.assertFalse(settings.DEBUG)

    def test_portugal_locale_and_timezone(self):
        self.assertEqual(settings.LANGUAGE_CODE, "pt-pt")
        self.assertEqual(settings.TIME_ZONE, "Europe/Lisbon")


class CatalogConfigTests(SimpleTestCase):
    def test_catalog_defaults_are_current_operational_values(self):
        self.assertEqual(settings.CATALOG_PROTOCOL_FRESHNESS_DAYS, 7)
        self.assertEqual(settings.CATALOG_MAINTENANCE_BATCH_SIZE, 5)

    def test_env_int_range_override_and_default(self):
        with patch.dict("os.environ", {}, clear=False):
            import os

            os.environ.pop("TEST_CATALOG_INTEGER", None)
            self.assertEqual(env_int_range("TEST_CATALOG_INTEGER", 7, minimum=1, maximum=20), 7)
            os.environ["TEST_CATALOG_INTEGER"] = "12"
            self.assertEqual(env_int_range("TEST_CATALOG_INTEGER", 7, minimum=1, maximum=20), 12)

    def test_env_int_range_rejects_invalid_values(self):
        for value in ("0", "-1", "21", "not-an-int"):
            with patch.dict("os.environ", {"TEST_CATALOG_INTEGER": value}):
                with self.assertRaises(RuntimeError):
                    env_int_range("TEST_CATALOG_INTEGER", 7, minimum=1, maximum=20)
