"""Multilingual public storefront contract; no changes to editorial product data."""

from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import ProductFamily
from apps.storefront.ui_translations import translate_ui


class PublicLanguageTests(TestCase):
    def test_browser_language_selection_and_portuguese_fallback(self):
        variants = (
            ("pt-PT,pt;q=0.9", "pt-pt", "Escolhas mais claras."),
            ("es-ES,es;q=0.9", "es", "Decisiones más claras."),
            ("en-GB,en;q=0.9", "en", "Clearer choices."),
            ("fr-FR,fr;q=0.9", "fr", "Des choix plus clairs."),
            ("de-DE,de;q=0.9", "de", "Klarere Entscheidungen."),
            ("it-IT,it;q=0.9", "pt-pt", "Escolhas mais claras."),
        )
        for accept_language, code, heading in variants:
            with self.subTest(accept_language=accept_language):
                response = self.client.get(
                    reverse("storefront:home"),
                    HTTP_ACCEPT_LANGUAGE=accept_language,
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, heading)
                self.assertContains(response, f'<html lang="{code}">')
                # The category navigation is shown when families are present.
                self.assertContains(response, 'id="familias"')
                self.assertContains(response, 'name="language"')
                self.assertNotContains(response, "atelier-specialties")
                self.assertEqual(
                    response["X-Frame-Options"], "DENY"
                )
                self.assertIn("Accept-Language", response.get("Vary", ""))

    def test_explicit_cookie_overrides_other_browser_languages(self):
        response = self.client.post(
            reverse("set_language"),
            {"language": "es", "next": reverse("storefront:home")},
            HTTP_ACCEPT_LANGUAGE="de-DE,de;q=0.9",
            secure=True,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("storefront:home"))
        self.assertEqual(response.cookies["lowcost_language"].value, "es")
        self.assertTrue(response.cookies["lowcost_language"]["secure"])
        spanish = self.client.get(
            reverse("storefront:home"),
            HTTP_ACCEPT_LANGUAGE="fr-FR,fr;q=0.9",
            secure=True,
        )
        self.assertContains(spanish, "Decisiones más claras.")
        self.assertContains(spanish, '<html lang="es">')

    def test_known_five_families_keep_all_original_routes(self):
        slugs = (
            "cavitacao-rf-vacuum-corpo",
            "hydrodermoabrasao-aqua-facial-multifuncoes",
            "pressoterapia-vacuum-drenagem",
            "hifu",
            "diodo-laser-remocao-tatuagens-pigmentacao",
        )
        names = (
            "Cavitação + RF + Vacuum (corpo)",
            "Hydrodermoabrasão / Aqua Facial / Multifunções faciais",
            "Pressoterapia / Vacuum / Drenagem",
            "HIFU profissional",
            "Diodo Laser / Remoção de Tatuagens / Pigmentação",
        )
        for index, (slug, name) in enumerate(zip(slugs, names), start=1):
            ProductFamily.objects.create(
                name=name, slug=slug, display_order=index
            )
        response = self.client.get("/", HTTP_ACCEPT_LANGUAGE="es")
        self.assertContains(response, "Cavitación + RF + vacío (cuerpo)")
        for slug in slugs:
            self.assertContains(
                response,
                reverse("storefront:product-family-detail", args=[slug]),
            )
        self.assertContains(response, 'class="card-grid" role="region"')
        self.assertEqual(response.content.count(b'<article class="product-card'), 5)

    def test_institutional_page_keeps_url_and_renders_language(self):
        response = self.client.get("/como-funciona/", HTTP_ACCEPT_LANGUAGE="fr")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Comment ça marche")
        self.assertContains(response, '<html lang="fr">')


    def test_contact_email_privacy_notice_is_localised_in_all_five_languages(self):
        label = "Mensagens de contacto"
        variants = {
            "pt-pt": label,
            "es": "Mensajes de contacto",
            "en": "Contact messages",
            "fr": "Messages de contact",
            "de": "Kontaktanfragen",
        }
        for language, expected in variants.items():
            with self.subTest(language=language):
                self.assertEqual(translate_ui(label, language), expected)

    def test_unknown_text_and_external_supplier_data_are_not_guessed(self):
        self.assertEqual(translate_ui("Unknown offer data", "es"), "Unknown offer data")
        self.assertEqual(
            translate_ui("VER PREÇO NO ALIEXPRESS", "de"),
            "PREIS AUF ALIEXPRESS ANSEHEN",
        )
        self.assertEqual(translate_ui("Preço observado", "pt-pt"), "Preço observado")

    def test_language_switch_rejects_external_redirect(self):
        response = self.client.post(
            reverse("set_language"),
            {"language": "fr", "next": "https://attacker.invalid/outside"},
            secure=True,
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("attacker.invalid", response["Location"])
