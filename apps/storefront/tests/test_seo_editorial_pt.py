"""Regression checks for the five Portuguese category SEO improvements.

The existing URLs, canonical/hreflang behavior and provider-controlled offer
facts must remain unchanged. SEO copy is not a source of live SKU evidence.
"""
from django.test import TestCase, override_settings

from apps.catalog.models import ProductFamily
from apps.storefront.seo_editorial import (
    ES_CATEGORY_GUIDES,
    PT_BUYING_QUESTIONS,
    PT_CATEGORY_GUIDES,
    buying_questions_for_category,
    guide_for_category,
)

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
        self.assertEqual(page.context["family_seo_guide"], ES_CATEGORY_GUIDES["hifu"])
        self.assertContains(page, "Guía de compra para España")
        self.assertNotContains(page, "Guia de compra para Portugal")
        self.assertContains(page, 'hreflang="pt-PT"')
        self.assertContains(page, 'hreflang="es-ES"')

    def test_no_guessed_guide_for_unknown_family_or_language(self):
        self.assertIsNone(guide_for_category("categoria-inexistente", "pt-pt"))
        self.assertEqual(guide_for_category("hifu", "es-ES"), ES_CATEGORY_GUIDES["hifu"])
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

    def test_spanish_guides_are_distinct_and_keep_market_and_url_boundaries(self):
        self.assertEqual(set(ES_CATEGORY_GUIDES), set(FAMILIES))
        self.assertEqual(len({g["title"] for g in ES_CATEGORY_GUIDES.values()}), 5)
        self.assertEqual(len({g["description"] for g in ES_CATEGORY_GUIDES.values()}), 5)
        for slug, guide in ES_CATEGORY_GUIDES.items():
            with self.subTest(slug=slug):
                page = self.get_page(f"/es/products/{slug}/")
                self.assertEqual(page.status_code, 200)
                self.assertEqual(page.context["page_title"], guide["title"])
                self.assertEqual(page.context["meta_description"], guide["description"])
                self.assertEqual(page.context["canonical_url"], f"{BASE}/es/products/{slug}/")
                self.assertContains(page, guide["heading"])
                self.assertContains(page, "Guía de compra para España")
                self.assertContains(page, "El precio, las existencias, la entrega")
                self.assertNotContains(page, "Guia de compra para Portugal")
                self.assertNotContains(page, "Antes de escolher uma oferta")
                for check in guide["checks"]:
                    self.assertContains(page, check)
                self.assertContains(page, 'hreflang="pt-PT"')
                self.assertContains(page, 'hreflang="es-ES"')
                self.assertContains(page, 'href="/es/#familias"')
                self.assertNotContains(page, 'itemtype="https://schema.org/Offer"')


    def test_portugal_purchase_questions_are_useful_and_do_not_touch_spain(self):
        self.assertEqual(set(PT_BUYING_QUESTIONS), set(FAMILIES))
        for slug, questions in PT_BUYING_QUESTIONS.items():
            with self.subTest(slug=slug):
                self.assertEqual(len(questions), 3)
                self.assertEqual(
                    buying_questions_for_category(slug, "pt-pt"), questions
                )
                self.assertEqual(
                    buying_questions_for_category(slug, "es"), ()
                )
                pt = self.get_page(f"/pt/products/{slug}/")
                es = self.get_page(f"/es/products/{slug}/")
                self.assertEqual(pt.status_code, 200)
                self.assertEqual(es.status_code, 200)
                self.assertEqual(pt.context["pt_buying_questions"], questions)
                self.assertEqual(es.context["pt_buying_questions"], ())
                self.assertContains(pt, "Dúvidas práticas antes de escolher")
                self.assertNotContains(es, "Dúvidas práticas antes de escolher")
                self.assertNotContains(es, "Informação para compradores em Portugal")
                for question, answer in questions:
                    self.assertContains(pt, question)
                    self.assertContains(pt, answer)
                    self.assertNotContains(es, question)
                self.assertContains(
                    pt, f'<link rel="canonical" href="{BASE}/pt/products/{slug}/">'
                )
                self.assertContains(
                    es, f'<link rel="canonical" href="{BASE}/es/products/{slug}/">'
                )
                self.assertContains(pt, 'hreflang="es-ES"')
                self.assertContains(es, 'hreflang="pt-PT"')
                self.assertNotContains(pt, '"@type":"FAQPage"')
                self.assertNotContains(es, '"@type":"FAQPage"')

    def test_hifu_ems_pt_seo_matches_public_category_without_misleading_product_claims(self):
        pt_category = self.get_page("/pt/products/hifu/")
        self.assertIn("HIFU e EMS", pt_category.context["page_title"])
        self.assertIn("EMS", pt_category.context["meta_description"])
        self.assertContains(pt_category, "HIFU e EMS: como comparar tecnologias diferentes")
        questions = PT_BUYING_QUESTIONS["hifu"]
        self.assertEqual(len(questions), 3)
        self.assertIn("HIFU", questions[0][0])
        self.assertIn("EMS", questions[0][0])
        self.assertIn("tecnologias diferentes", questions[0][1])
        self.assertContains(
            pt_category,
            '<link rel="canonical" href="https://www.example.test/pt/products/hifu/">'
        )

        pt_home = self.get_page("/pt/")
        self.assertIn("HIFU/EMS", pt_home.context["meta_description"])
        self.assertIn("pressoterapia/Tecar", pt_home.context["meta_description"])
        es_home = self.get_page("/es/")
        self.assertNotIn("HIFU/EMS", es_home.context["meta_description"])
        es_category = self.get_page("/es/products/hifu/")
        self.assertEqual(es_category.context["page_title"], ES_CATEGORY_GUIDES["hifu"]["title"])

    def test_portugal_home_metadata_changes_without_changing_spanish_home(self):
        pt = self.get_page("/pt/")
        es = self.get_page("/es/")
        root = self.get_page("/")
        self.assertEqual(pt.status_code, 200)
        self.assertEqual(es.status_code, 200)
        self.assertEqual(root.status_code, 200)
        self.assertEqual(
            pt.context["page_title"],
            "Equipamentos de Estética Profissional em Portugal | Lowcost Europa",
        )
        self.assertIn("em Portugal", pt.context["meta_description"])
        self.assertContains(
            pt, '<link rel="canonical" href="https://www.example.test/pt/">'
        )
        self.assertNotIn("em Portugal", es.context["page_title"])
        self.assertNotIn("em Portugal", es.context["meta_description"])
        self.assertEqual(
            es.context["canonical_url"], "https://www.example.test/es/"
        )
        self.assertEqual(
            self.get_page("/sitemap.xml").content.count(b"<loc>"), 23
        )
