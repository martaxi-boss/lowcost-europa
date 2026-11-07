"""Country-from-public-IP locale contract for the Europe-focused storefront."""

import ipaddress
from unittest.mock import patch

from django.conf import settings
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from apps.storefront.geo_locale import (
    COUNTRY_LANGUAGES,
    is_public_storefront_page,
    lookup_country,
    public_client_ip,
)


class CountryLocaleSecurityTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_country_database_path_is_private_to_project_not_restricted_data_dir(self):
        self.assertEqual(
            settings.GEO_LANGUAGE_COUNTRY_DB,
            settings.BASE_DIR / ".geoip" / "dbip-country-lite.mmdb",
        )

    def test_direct_public_ip_ignores_untrusted_x_real_ip(self):
        request = self.factory.get(
            "/", REMOTE_ADDR="1.1.1.1", HTTP_X_REAL_IP="8.8.8.8"
        )
        self.assertEqual(public_client_ip(request), ipaddress.ip_address("1.1.1.1"))

    def test_only_loopback_proxy_may_supply_x_real_ip(self):
        request = self.factory.get(
            "/", REMOTE_ADDR="127.0.0.1", HTTP_X_REAL_IP="8.8.8.8"
        )
        self.assertEqual(public_client_ip(request), ipaddress.ip_address("8.8.8.8"))
        request = self.factory.get(
            "/", REMOTE_ADDR="127.0.0.1", HTTP_X_REAL_IP="192.168.0.5"
        )
        self.assertIsNone(public_client_ip(request))

    def test_private_and_unknown_ip_cannot_be_geolocated(self):
        for ip in ("127.0.0.1", "192.168.10.4", "10.1.1.7", "not-an-ip"):
            with self.subTest(ip=ip):
                self.assertIsNone(public_client_ip(self.factory.get("/", REMOTE_ADDR=ip)))

    def test_only_public_storefront_routes_receive_ip_selection(self):
        self.assertTrue(is_public_storefront_page("/"))
        self.assertTrue(is_public_storefront_page("/products/hifu/"))
        for path in ("/painel/", "/admin/", "/ops/", "/i18n/setlang/", "/go/1/"):
            self.assertFalse(is_public_storefront_page(path))

    def test_missing_country_db_returns_unknown_without_network_or_exception(self):
        with override_settings(GEO_LANGUAGE_COUNTRY_DB="/does-not-exist/db.mmdb"):
            self.assertIsNone(lookup_country(ipaddress.ip_address("8.8.8.8")))


@override_settings(GEO_LANGUAGE_ENABLED=True)
class PublicCountryLanguageTests(TestCase):
    def test_five_named_countries_and_all_others_follow_ip_not_browser(self):
        cases = (
            ("PT", "pt-pt", "Escolhas mais claras."),
            ("ES", "es", "Decisiones más claras."),
            ("FR", "fr", "Des choix plus clairs."),
            ("DE", "de", "Klarere Entscheidungen."),
            ("GB", "en", "Clearer choices."),
            ("IT", "en", "Clearer choices."),
            ("NL", "en", "Clearer choices."),
            ("PL", "en", "Clearer choices."),
            ("HU", "en", "Clearer choices."),
            ("BR", "en", "Clearer choices."),
            ("AO", "en", "Clearer choices."),
            (None, "en", "Clearer choices."),
        )
        for country, language, text in cases:
            with self.subTest(country=country), patch(
                "apps.storefront.geo_locale.lookup_country", return_value=country
            ) as resolve:
                response = self.client.get(
                    reverse("storefront:home"),
                    REMOTE_ADDR="127.0.0.1",
                    HTTP_X_REAL_IP="8.8.8.8",
                    HTTP_ACCEPT_LANGUAGE="ja-JP,ja;q=0.9",
                )
                self.assertContains(response, text)
                self.assertContains(response, f'<html lang="{language}">')
                self.assertEqual(response["Content-Language"], language)
                self.assertEqual(response["Cache-Control"], "private, no-store")
                self.assertIn("Cookie", response["Vary"])
                self.assertNotContains(response, 'class="locale-switch"')
                self.assertContains(response, "IP Geolocation by DB-IP")
                resolve.assert_called_once_with(ipaddress.ip_address("8.8.8.8"))

    def test_old_cookie_and_browser_do_not_override_vpn_ip(self):
        self.client.cookies["lowcost_language"] = "de"
        with patch("apps.storefront.geo_locale.lookup_country", return_value="ES"):
            response = self.client.get(
                reverse("storefront:home"),
                REMOTE_ADDR="127.0.0.1",
                HTTP_X_REAL_IP="8.8.8.8",
                HTTP_ACCEPT_LANGUAGE="fr-FR",
            )
        self.assertContains(response, "Decisiones más claras.")
        self.assertContains(response, '<html lang="es">')

    def test_nonpublic_routes_are_not_geoip_resolved(self):
        with patch("apps.storefront.geo_locale.lookup_country") as lookup:
            self.client.get(
                "/painel/",
                REMOTE_ADDR="127.0.0.1",
                HTTP_X_REAL_IP="8.8.8.8",
                HTTP_ACCEPT_LANGUAGE="fr",
            )
            lookup.assert_not_called()

    def test_country_mapping_is_exact_and_does_not_group_overseas_markets(self):
        self.assertEqual(
            COUNTRY_LANGUAGES,
            {"PT": "pt-pt", "ES": "es", "FR": "fr", "DE": "de", "GB": "en"},
        )
