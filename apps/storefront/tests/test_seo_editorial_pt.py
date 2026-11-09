"""Regression checks for the five Portuguese category SEO improvements.

The existing URLs, canonical/hreflang behavior and provider-controlled offer
facts must remain unchanged. SEO copy is not a source of live SKU evidence.
"""
from django.test import TestCase, override_settings

from apps.catalog.models import ProductFamily
from apps.storefront.seo_editorial import PT_CATEGORY_GUIDES, guide_for_category

BASE = "https://www.example.test"
FAMILIES = {
    "cavitacao-rf-vacuum-corpo": "Cavitação + RF + Vacuum",
    "hydrodermoabrasao-aqua-facial-multifuncoes": "Hidrodermoabrasão e Aqua Facial",
    "pressoterapia-vacuum-drenagem": "Pressoterapia / RF Tecar",
    "hifu": "HIFU",
    "diodo-laser-remocao-tatuagens-pigmentacao": "Laser díodo / pigmentação",
}


@override_settings(
    LOCALE_SEO_ENABLED=True,
    GEO_LANGUAGE_ENABLED=False,
    PUBLIC_INDEXING_ENABLED=True,
    PUBLIC_SITE_URL=BASE,
    PUBLIC_OPERATOR={"name": "Test operator", "address": "Test address", "tax_id": "TEST"},
    ALLOWED_HOSTS=["www.example.test"],
)
class PortugueseSeoGuideTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for order, (slug, name) in enumerate(FAMILIES.items(), start=1):
            ProductFamily.objects.create(slug=slug, name=name, display_order=order)

    def get_page(self, path):
        return self.client.get(path, HTTP_HOST="www.example.test", secure=True)

    def test_all_five_categories_show_distinct_pt_guides_and_meta(self):
        self.assertEqual(set(PT_CATEGORY_GUIDES), set(FAMILIES))
        titles = set()
        descriptions = set()
        for slug, guide in PT_CATEGORY_GUIDES.items():
            with self.subTest(slug=slug):
                page = self.get_page(f"/pt/products/{slug}/")
                self.assertEqual(page.status_code, 200)
                self.assertEqual(page.context["page_title"], guide["title"])
                self.assertEqual(page.context["meta_description"], guide["description"])
                self.assertEqual(page.context["family_seo_guide"], guide)
                self.assertEqual(page.context["canonical_url"], f"{BASE}/pt/products/{slug}/")
                self.assertContains(page, guide["heading"])
                self.assertContains(page, "Guia de compra para Portugal")
                self.assertEqual(len(guide["checks"]), 3)
                for check in guide["checks"]:
                    self.assertContains(page, check)
                titles.add(guide["title"])
                descriptions.add(guide["description"])
        self.assertEqual(len(titles), 5)
        self.assertEqual(len(descriptions), 5)

    def test_spanish_page_has_no_untranslated_portuguese_guide(self):
        page = self.get_page("/es/products/hifu/")
        self.assertEqual(page.status_code, 200)
        self.assertIsNone(page.context["family_seo_guide"])
        self.assertNotContains(page, "Guia de compra para Portugal")
        self.assertContains(page, 'hreflang="pt-PT"')
        self.assertContains(page, 'hreflang="es-ES"')

    def test_no_guessed_guide_for_unknown_family_or_language(self):
        self.assertIsNone(guide_for_category("categoria-inexistente", "pt-pt"))
        self.assertIsNone(guide_for_category("hifu", "es"))
        self.assertIsNone(guide_for_category("hifu", "en"))
        self.assertEqual(guide_for_category("hifu", "pt-PT"), PT_CATEGORY_GUIDES["hifu"])

    def test_existing_indexed_urls_and_sitemap_not_expanded(self):
        sitemap = self.get_page("/sitemap.xml")
        self.assertEqual(sitemap.status_code, 200)
        self.assertEqual(sitemap.content.count(b"<loc>"), 23)
        page = self.get_page("/products/hifu/")
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.context["canonical_url"], BASE + "/products/hifu/")
        self.assertIn("HIFU", page.context["page_title"])
