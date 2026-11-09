"""Regression gates for PT/ES SEO before enabling it in production.

The existing eleven canonical routes are deliberately never redirected.
"""
import json
import re
from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.catalog.models import ProductFamily

BASE = "https://www.example.test"
OPERATOR = {"name": "Example", "address": "Test address", "tax_id": "TEST"}
SLUGS = (
    "cavitacao-rf-vacuum-corpo",
    "hydrodermoabrasao-aqua-facial-multifuncoes",
    "pressoterapia-vacuum-drenagem",
    "hifu",
    "diodo-laser-remocao-tatuagens-pigmentacao",
)


@override_settings(
    LOCALE_SEO_ENABLED=True,
    PUBLIC_SITE_URL=BASE,
    PUBLIC_INDEXING_ENABLED=True,
    PUBLIC_OPERATOR=OPERATOR,
    ALLOWED_HOSTS=["www.example.test", "other.example.test"],
)
class SeoLocaleCoreTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for index, slug in enumerate(SLUGS, start=1):
            ProductFamily.objects.create(name=slug, slug=slug, display_order=index)

    def get_public(self, path):
        return self.client.get(path, HTTP_HOST="www.example.test", secure=True)

    def test_home_and_categories_keep_original_canonicals_and_add_reciprocal_hreflang(self):
        paths = ("/", "/pt/", "/es/", "/products/hifu/",
                 "/pt/products/hifu/", "/es/products/hifu/")
        for path in paths:
            with self.subTest(path=path):
                response = self.get_public(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, f'<link rel="canonical" href="{BASE}{path}">')
                family = "/products/hifu/" if "/products/" in path else "/"
                self.assertContains(
                    response, f'hreflang="pt-PT" href="{BASE}/pt'
                    + (family if family != "/" else "/") + '"'
                )
                self.assertContains(
                    response, f'hreflang="es-ES" href="{BASE}/es'
                    + (family if family != "/" else "/") + '"'
                )
                self.assertContains(response, f'hreflang="x-default" href="{BASE}{family}"')
                self.assertNotContains(response, "noindex, nofollow")

    def test_explicit_locale_ignores_geoip_and_browser_and_keeps_navigation(self):
        with override_settings(GEO_LANGUAGE_ENABLED=True), patch(
            "apps.storefront.geo_locale.lookup_country", return_value="DE"
        ) as lookup:
            response = self.client.get("/es/", HTTP_HOST="www.example.test",
                                       HTTP_ACCEPT_LANGUAGE="fr", secure=True)
            self.assertContains(response, '<html lang="es">')
            self.assertContains(response, "Decisiones más claras.")
            self.assertContains(response, 'href="/es/products/hifu/"')
            self.assertNotContains(response, 'class="locale-switch"')
            lookup.assert_not_called()

    def test_pt_locale_and_category_backlink(self):
        response = self.get_public("/pt/products/hifu/")
        self.assertContains(response, '<html lang="pt-pt">')
        self.assertContains(response, 'href="/pt/#familias"')

    def test_unchanged_base_11_sitemap_and_opt_in_23_sitemap(self):
        response = self.get_public("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        urls = re.findall(r"<loc>([^<]+)</loc>", response.content.decode())
        self.assertEqual(len(urls), 23)
        self.assertEqual(len(set(urls)), 23)
        self.assertIn(BASE + "/products/hifu/", urls)
        self.assertIn(BASE + "/es/products/hifu/", urls)
        self.assertIn(BASE + "/pt/products/hifu/", urls)
        self.assertNotIn(BASE + "/es/pesquisar/", urls)
        with override_settings(LOCALE_SEO_ENABLED=False):
            old_sitemap = self.get_public("/sitemap.xml")
            self.assertEqual(old_sitemap.content.count(b"<loc>"), 11)
            self.assertEqual(self.get_public("/es/").status_code, 404)
            self.assertEqual(self.get_public("/pt/products/hifu/").status_code, 404)

    def test_indexnow_scope_and_private_endpoints_unchanged(self):
        from apps.storefront.management.commands.notify_indexnow import valid_url

        self.assertTrue(valid_url(BASE + "/es/products/hifu/", BASE))
        self.assertTrue(valid_url(BASE + "/pt/", BASE))
        for path in ("/es/painel/", "/es/go/5/", "/es/pesquisar/", "/go/5/"):
            self.assertFalse(valid_url(BASE + path, BASE))
        for path in ("/painel/", "/admin/"):
            response = self.get_public(path)
            self.assertEqual(response.status_code, 302)
            self.assertIn("noindex", response["X-Robots-Tag"].lower())

    def test_safe_schema_only_for_public_indexable_pages(self):
        response = self.get_public("/es/")
        raw = response.content.decode()
        payload = re.search(r'<script type="application/ld\+json">(.*?)</script>', raw)
        self.assertIsNotNone(payload)
        data = json.loads(payload.group(1))
        self.assertEqual(data["@context"], "https://schema.org")
        self.assertEqual({item["@type"] for item in data["@graph"]},
                         {"WebSite", "Organization"})
        product = self.get_public("/es/products/hifu/").content.decode()
        category_data = json.loads(
            re.search(r'<script type="application/ld\+json">(.*?)</script>', product).group(1)
        )
        self.assertEqual(category_data["@type"], "BreadcrumbList")
        self.assertEqual(category_data["itemListElement"][1]["item"],
                         BASE + "/es/products/hifu/")
        with override_settings(PUBLIC_INDEXING_ENABLED=False):
            response = self.get_public("/es/")
            self.assertNotContains(response, "application/ld+json")
            self.assertContains(response, "noindex, nofollow")
            self.assertNotContains(response, 'hreflang="es-ES"')

    def test_ineligible_host_does_not_advertise_alternates(self):
        response = self.client.get("/es/", HTTP_HOST="other.example.test", secure=True)
        self.assertContains(response, "noindex, nofollow")
        self.assertNotContains(response, 'rel="canonical"')

    def test_retired_categories_are_not_in_sitemap_or_hreflang(self):
        ProductFamily.objects.filter(slug="hifu").update(
            status=ProductFamily.Status.RETIRED
        )
        response = self.get_public("/es/products/hifu/")
        self.assertContains(response, "noindex, nofollow")
        self.assertNotContains(response, 'hreflang="es-ES"')
        self.assertNotContains(response, 'application/ld+json')
        self.assertNotContains(self.get_public("/sitemap.xml"), "/es/products/hifu/")

    def test_text_sitemap_matches_xml_and_omits_retired_and_private_urls(self):
        ProductFamily.objects.filter(slug="hifu").update(status=ProductFamily.Status.RETIRED)
        xml_urls = re.findall(r"<loc>([^<]+)</loc>",
                              self.get_public("/sitemap.xml").content.decode())
        response = self.get_public("/sitemap.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        urls = response.content.decode("utf-8").splitlines()
        self.assertEqual(urls, xml_urls)
        self.assertEqual(len(urls), 20)
        self.assertEqual(len(set(urls)), len(urls))
        self.assertNotIn("noindex", response.get("X-Robots-Tag", ""))
        self.assertTrue(all(url.startswith(BASE + "/") for url in urls))
        self.assertTrue(all("/hifu/" not in url and "/painel/" not in url for url in urls))
        head = self.client.head("/sitemap.txt", HTTP_HOST="www.example.test", secure=True)
        self.assertEqual(head.status_code, 200)
        self.assertEqual(head.content, b"")
        self.assertEqual(self.client.post("/sitemap.txt", HTTP_HOST="www.example.test",
                                         secure=True).status_code, 405)

    def test_text_sitemap_keeps_indexing_and_locale_gates(self):
        with override_settings(LOCALE_SEO_ENABLED=False):
            self.assertEqual(len(self.get_public("/sitemap.txt").content.splitlines()), 11)
        with override_settings(PUBLIC_INDEXING_ENABLED=False):
            response = self.get_public("/sitemap.txt")
            self.assertIn("noindex", response["X-Robots-Tag"])
            self.assertNotIn(b"/pt/", response.content)
            self.assertNotIn(b"/es/", response.content)
        response = self.client.get("/sitemap.txt", HTTP_HOST="other.example.test", secure=True)
        self.assertIn("noindex", response["X-Robots-Tag"])

    def test_robots_advertises_both_sitemaps_only_on_public_indexable_host(self):
        response = self.get_public("/robots.txt")
        self.assertContains(response, f"Sitemap: {BASE}/sitemap.xml\n")
        self.assertContains(response, f"Sitemap: {BASE}/sitemap.txt\n")
        self.assertContains(response, "Disallow: /painel/")
        with override_settings(PUBLIC_INDEXING_ENABLED=False):
            blocked = self.get_public("/robots.txt")
            self.assertContains(blocked, "Disallow: /")
            self.assertNotContains(blocked, "Sitemap:")
        other = self.client.get("/robots.txt", HTTP_HOST="other.example.test", secure=True)
        self.assertNotContains(other, "Sitemap:")
