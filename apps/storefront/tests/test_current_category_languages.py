"""Public labels follow the page language without renaming the manual catalogue."""

import json
import re

from django.test import TestCase, override_settings

from apps.catalog.models import ProductFamily
from apps.storefront.ui_translations import translate_ui


CATEGORIES = (
    ("cavitacao-rf-vacuum-corpo", "Cavitação + RF + Vacuum", "Cavitación + RF + vacío"),
    (
        "hydrodermoabrasao-aqua-facial-multifuncoes",
        "Microdermoabrasão / Hidrodermoabrasão / Multifunções faciais",
        "Microdermoabrasión / Hidrodermoabrasión / Multifunción facial",
    ),
    ("pressoterapia-vacuum-drenagem", "Pressoterapia / RF Tecar", "Presoterapia / RF Tecar"),
    (
        "diodo-laser-remocao-tatuagens-pigmentacao",
        "Diodo Laser / Remoção de tatuagens / Pigmentação",
        "Láser de diodo / Eliminación de tatuajes / Pigmentación",
    ),
)
BASE = "https://www.example.test"


@override_settings(
    LOCALE_SEO_ENABLED=True,
    PUBLIC_SITE_URL=BASE,
    PUBLIC_INDEXING_ENABLED=True,
    PUBLIC_OPERATOR={"name": "Example", "address": "Test address", "tax_id": "TEST"},
    ALLOWED_HOSTS=["www.example.test"],
)
class CurrentCategoryLanguageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for order, (slug, source, _) in enumerate(CATEGORIES, start=1):
            ProductFamily.objects.create(name=source, slug=slug, display_order=order)

    def test_spanish_heading_navigation_and_schema_use_the_current_category_names(self):
        home = self.client.get("/es/", HTTP_HOST="www.example.test", secure=True)
        for slug, source, spanish in CATEGORIES:
            with self.subTest(slug=slug):
                path = f"/es/products/{slug}/"
                response = self.client.get(path, HTTP_HOST="www.example.test", secure=True)
                self.assertContains(response, f"<h1>{spanish}</h1>", html=True)
                self.assertContains(home, spanish)
                self.assertNotContains(response, f"<h1>{source}</h1>", html=True)
                self.assertContains(response, f'<link rel="canonical" href="{BASE}{path}">')
                self.assertContains(response, 'hreflang="pt-PT"')
                payload = re.search(
                    r'<script type="application/ld\+json">(.*?)</script>',
                    response.content.decode(),
                )
                self.assertIsNotNone(payload)
                schema = json.loads(payload.group(1))
                self.assertEqual(schema["itemListElement"][1]["name"], spanish)
                self.assertEqual(ProductFamily.objects.get(slug=slug).name, source)

    def test_portuguese_and_unknown_owner_names_remain_unchanged(self):
        for slug, source, _ in CATEGORIES:
            with self.subTest(slug=slug):
                response = self.client.get(
                    f"/pt/products/{slug}/", HTTP_HOST="www.example.test", secure=True
                )
                self.assertContains(response, f"<h1>{source}</h1>", html=True)
                self.assertEqual(translate_ui(source, "pt-pt"), source)
        self.assertEqual(translate_ui("Categoria manual personalizada", "es"),
                         "Categoria manual personalizada")
        self.assertEqual(translate_ui("HIFU / EMS", "es"), "HIFU / EMS")
