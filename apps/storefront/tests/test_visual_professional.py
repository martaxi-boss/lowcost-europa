"""Presentation contracts for the editorial storefront."""

from django.conf import settings
from django.test import SimpleTestCase


class EditorialStorefrontTests(SimpleTestCase):
    def template(self, path):
        return (settings.BASE_DIR / "apps/storefront/templates/storefront" / path).read_text()

    def test_family_with_published_offer_is_not_labelled_preparing(self):
        for template in (
            self.template("components/product_family_card.html"),
            self.template("product_family_detail.html"),
        ):
            self.assertIn("{% if family.display_offer %}Seleção editorial", template)
            self.assertIn("{% else %}{{ family.public_status }}{% endif %}", template)

    def test_offer_information_is_clear_and_factual(self):
        card = self.template("components/offer_card.html")
        for text in (
            "Preço observado",
            "Logística observada",
            "Consultar avaliações e vendas indicadas",
            "VER PREÇO NO ALIEXPRESS",
            "Confirme a variante, o stock",
        ):
            self.assertIn(text, card)
        self.assertIn("{% url 'storefront:offer-go' offer.pk %}", card)
        self.assertNotIn("Entrega garantida", card)

    def test_missing_photo_does_not_claim_published_family_is_in_preparation(self):
        card = self.template("components/product_family_card.html")
        self.assertEqual(card.count("Imagem indisponível{% else %}Seleção em preparação"), 2)

    def test_mobile_comparison_is_keyboard_accessible(self):
        controls = self.template("components/catalog_explorer_controls.html")
        for text in ('data-compare-dock hidden', 'data-compare-show',
                     'data-compare-panel', 'data-compare-heading tabindex="-1"'):
            self.assertIn(text, controls)

    def test_no_external_frontend_framework_or_tracker_added(self):
        base = self.template("base.html")
        self.assertIn("storefront/catalog-explorer.js", base)
        self.assertNotIn('<script src="https://', base.lower())

    def test_static_css_and_explorer_script_are_versioned(self):
        base = self.template("base.html")
        self.assertIn("storefront.css' %}?v=ux-20261107", base)
        self.assertIn("catalog-explorer.js' %}?v=ux-20261107", base)
