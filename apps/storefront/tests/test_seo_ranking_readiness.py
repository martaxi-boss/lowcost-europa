"""Ranking-readiness SEO: real links and market-scoped evidence, no invented offers."""

from datetime import timedelta
from decimal import Decimal
import json
import re

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.catalog.models import Offer, OfferFamilyPlacement, OfferObservation, ProductFamily

BASE = "https://www.example.test"
SLUGS = (
    "cavitacao-rf-vacuum-corpo",
    "hydrodermoabrasao-aqua-facial-multifuncoes",
    "pressoterapia-vacuum-drenagem",
    "hifu",
    "diodo-laser-remocao-tatuagens-pigmentacao",
)


@override_settings(
    PUBLIC_RECENT_PRICE_REQUIRED=True,
    LOCALE_SEO_ENABLED=True,
    GEO_LANGUAGE_ENABLED=False,
    PUBLIC_INDEXING_ENABLED=True,
    PUBLIC_SITE_URL=BASE,
    PUBLIC_OPERATOR={"name": "Operator", "address": "Example", "tax_id": "TEST"},
    ALLOWED_HOSTS=["www.example.test"],
)
class RankingReadinessPtEsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for position, slug in enumerate(SLUGS, start=1):
            ProductFamily.objects.create(
                name=slug, slug=slug, display_order=position
            )

    def get_public(self, path):
        return self.client.get(path, HTTP_HOST="www.example.test", secure=True)

    def make_offer(self):
        now = timezone.now()
        family = ProductFamily.objects.get(slug="hifu")
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="seo-ranking-ptes-001",
            title="HIFU example without stock proof",
            affiliate_url="https://s.click.aliexpress.com/e/_RankingTest",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=now,
            protocol_verified_at=now,
            is_active=True,
            owner_hidden=False,
        )
        OfferFamilyPlacement.objects.create(offer=offer, product_family=family)
        return offer

    def observe(self, offer, country, price, age_hours):
        return OfferObservation.objects.create(
            offer=offer,
            destination_country=country,
            currency="EUR",
            price=Decimal(price),
            observed_at=timezone.now() - timedelta(hours=age_hours),
        )

    def test_related_category_links_keep_locale_and_current_page_out(self):
        for locale in ("pt", "es"):
            for slug in SLUGS:
                with self.subTest(locale=locale, slug=slug):
                    path = f"/{locale}/products/{slug}/"
                    response = self.get_public(path)
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(
                        response, f'<link rel="canonical" href="{BASE}{path}">'
                    )
                    html = response.content.decode("utf-8")
                    nav = re.search(
                        r'<nav class="family-index related-families-nav"[^>]*>'
                        r'(.*?)</nav>', html, re.S
                    )
                    self.assertIsNotNone(nav)
                    urls = re.findall(r'href="([^"]+)"', nav.group(1))
                    self.assertEqual(len(urls), 4)
                    self.assertEqual(
                        set(urls),
                        {f"/{locale}/products/{s}/" for s in SLUGS if s != slug},
                    )
                    self.assertNotIn(f"/{locale}/products/{slug}/", urls)
                    self.assertNotIn(f"/{'pt' if locale == 'es' else 'es'}/products/",
                                     nav.group(1))
                    self.assertNotIn("https://s.click.aliexpress.com", nav.group(1))
                    trail = re.search(
                        r'<nav class="category-breadcrumb"[^>]*>(.*?)</nav>',
                        html, re.S,
                    )
                    self.assertIsNotNone(trail)
                    self.assertIn(f'href="/{locale}/"', trail.group(1))
                    self.assertIn('aria-current="page"', trail.group(1))

    def test_related_links_exclude_retired_and_do_not_change_sitemaps(self):
        ProductFamily.objects.filter(
            slug="pressoterapia-vacuum-drenagem"
        ).update(status=ProductFamily.Status.RETIRED)
        response = self.get_public("/es/products/hifu/")
        nav = re.search(
            r'<nav class="family-index related-families-nav"[^>]*>'
            r'(.*?)</nav>', response.content.decode(), re.S
        )
        self.assertIsNotNone(nav)
        self.assertEqual(nav.group(1).count('href="/es/products/'), 3)
        self.assertNotIn("/es/products/pressoterapia-vacuum-drenagem/", nav.group(1))
        self.assertEqual(self.get_public("/sitemap.xml").content.count(b"<loc>"), 20)

    def test_verified_es_price_appears_only_for_es_and_not_as_stock_proof(self):
        offer = self.make_offer()
        self.observe(offer, "PT", "120.00", 2)
        self.observe(offer, "ES", "145.00", 1)
        pt = self.get_public("/pt/products/hifu/")
        es = self.get_public("/es/products/hifu/")
        self.assertContains(pt, 'data-price="120.00" data-currency="EUR"')
        self.assertContains(es, 'data-price="145.00" data-currency="EUR"')
        self.assertNotContains(pt, 'data-price="145.00"')
        self.assertNotContains(es, 'data-price="120.00"')
        self.assertContains(es, "Precio en EUR observado para España")
        self.assertContains(es, "confirma existencias y entrega")
        self.assertNotContains(pt, "Precio en EUR observado para España")
        # No schema.org Product/Offer/InStock claims on affiliate category pages.
        markup = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>',
            es.content.decode(), re.S
        )
        for raw in markup:
            data = json.loads(raw)
            self.assertNotIn('"InStock"', json.dumps(data))
            self.assertNotIn('"Offer"', json.dumps(data))

    def test_es_price_old_or_missing_falls_back_to_labelled_pt_reference(self):
        offer = self.make_offer()
        self.observe(offer, "PT", "120.00", 2)
        self.observe(offer, "ES", "145.00", 31)
        es = self.get_public("/es/products/hifu/")
        self.assertContains(es, 'data-price="120.00" data-currency="EUR"')
        self.assertContains(es, "Datos de referencia para Portugal")
        self.assertNotContains(es, "Precio en EUR observado para España")

    def test_es_observation_cannot_bypass_pt_publication_gate_or_go_link(self):
        offer = self.make_offer()
        self.observe(offer, "PT", "120.00", 31)
        self.observe(offer, "ES", "145.00", 1)
        es = self.get_public("/es/products/hifu/")
        self.assertNotContains(es, 'data-offer-id="' + str(offer.pk) + '"')
        self.assertEqual(self.get_public(f"/go/{offer.pk}/").status_code, 404)
