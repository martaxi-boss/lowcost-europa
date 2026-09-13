from django.conf import settings
from django.test import SimpleTestCase


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

