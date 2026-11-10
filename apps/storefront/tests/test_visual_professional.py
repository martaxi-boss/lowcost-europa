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
            self.assertIn('{% if family.display_offer %}{{ "Seleção editorial"|ui_t }}', template)
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
        self.assertEqual(
            card.count(
                '{{ "Imagem indisponível"|ui_t }}{% else %}{{ "Seleção em preparação"|ui_t }}'
            ),
            2,
        )

    def test_mobile_categories_have_real_scrollable_region(self):
        home = self.template("home.html")
        self.assertIn('class="card-grid" role="region"', home)
        self.assertIn("Deslize os cartões", home)

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
        self.assertIn("storefront.css' %}?v=owner-share-20261110", base)
        self.assertIn("catalog-explorer.js' %}?v=owner-share-20261110", base)



class PublicLaunchIdentityTests(SimpleTestCase):
    """Guard the new public contact identity and SSL-gated canonical domain."""

    def template(self, name):
        return (settings.BASE_DIR / "apps/storefront/templates/storefront" / name).read_text()

    def test_official_contact_replaces_testing_gmail_on_all_public_pages(self):
        for name in ("contacto.html", "privacidade.html"):
            with self.subTest(template=name):
                content = self.template(name)
                self.assertIn('mailto:geral@lowcost-europa.eu', content)
                self.assertNotIn("@gmail.com", content)

    def test_www_is_canonical_and_apex_redirects_only_after_tls(self):
        root = settings.BASE_DIR
        nginx = (root / "deploy/nginx/lowcost-europa.eu.conf").read_text()
        env_example = (root / ".env.example").read_text()
        self.assertIn("server_name www.lowcost-europa.eu;", nginx)
        self.assertIn("server_name lowcost-europa.eu;", nginx)
        self.assertEqual(
            nginx.count("return 301 https://www.lowcost-europa.eu$request_uri;"),
            2,
        )
        self.assertIn(
            "ssl_certificate /etc/letsencrypt/live/lowcost-europa.eu/fullchain.pem;",
            nginx,
        )
        self.assertIn("location = /aliexpress/callback {", nginx)
        self.assertEqual(nginx.count('add_header X-Robots-Tag "noindex, nofollow" always;'), 4)
        self.assertIn(
            "# DJANGO_PUBLIC_SITE_URL=https://www.lowcost-europa.eu",
            env_example,
        )
        self.assertIn("# DJANGO_PUBLIC_INDEXING_ENABLED=false", env_example)
        # No sensitive Gmail destination must be present in the public templates.
        self.assertNotIn("@gmail.com", self.template("contacto.html"))
