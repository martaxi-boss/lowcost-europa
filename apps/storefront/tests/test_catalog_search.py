"""Public search/compare must never widen catalog visibility or touch affiliate links."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import (
    Offer,
    OfferClick,
    OfferFamilyPlacement,
    OfferObservation,
    ProductFamily,
)


class CatalogSearchTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.family = ProductFamily.objects.create(
            name="HIFU e estética profissional", slug="hifu-profissional", display_order=1
        )
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="search-hifu-one",
            title="Equipamento HIFU 7D Profissional",
            affiliate_url="https://affiliate.example.test/hifu",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=now,
            protocol_verified_at=now,
            ship_from_country="PL",
            ship_from_verified_at=now,
            is_active=True,
            owner_hidden=False,
        )
        OfferFamilyPlacement.objects.create(
            offer=self.offer, product_family=self.family, selection_position=1
        )
        OfferObservation.objects.create(
            offer=self.offer, price=Decimal("399.90"), currency="EUR",
            observed_at=now - timedelta(minutes=10),
        )
        self.hidden = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="search-private",
            title="HIFU oferta nao publicada",
            affiliate_url="https://affiliate.example.test/hidden",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=now,
            protocol_verified_at=now,
            owner_hidden=True,
        )
        OfferFamilyPlacement.objects.create(offer=self.hidden, product_family=self.family)
        self.retired = ProductFamily.objects.create(
            name="Equipamentos retirados", slug="equipamentos-retirados",
            status=ProductFamily.Status.RETIRED,
        )
        old = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="search-retired",
            title="HIFU descontinuado",
            affiliate_url="https://affiliate.example.test/retired",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=now,
            protocol_verified_at=now,
            is_active=True,
        )
        OfferFamilyPlacement.objects.create(offer=old, product_family=self.retired)

    def test_accent_insensitive_search_only_returns_eligible_placements(self):
        r = self.client.get(reverse("storefront:search"), {"q": "hífu"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Equipamento HIFU 7D Profissional")
        self.assertContains(r, "399,90 EUR")
        self.assertNotContains(r, self.hidden.title)
        self.assertNotContains(r, "HIFU descontinuado")
        self.assertContains(r, 'data-catalog-explorer')
        self.assertContains(r, 'data-compare-toggle')
        self.assertContains(r, 'data-price="399.90"')
        self.assertContains(r, reverse("storefront:offer-go", kwargs={"offer_id": self.offer.pk}))
        self.assertEqual(OfferClick.objects.count(), 0)

    def test_multiple_words_and_nonmatching_input(self):
        ok = self.client.get(reverse("storefront:search"), {"q": "HIFU 7D"})
        self.assertEqual(ok.context["result_count"], 1)
        no = self.client.get(reverse("storefront:search"), {"q": "laser 7d"})
        self.assertEqual(no.context["result_count"], 0)
        self.assertContains(no, "Não encontramos ofertas")
        self.assertEqual(OfferClick.objects.count(), 0)

    def test_unfiltered_search_explains_how_to_start(self):
        r = self.client.get(reverse("storefront:search"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Procure um equipamento ou escolha uma especialidade")
        self.assertNotContains(r, self.offer.title)

    @override_settings(PUBLIC_INDEXING_ENABLED=True, PUBLIC_SITE_URL="https://example.test")
    def test_search_is_noindex_even_if_global_indexing_enabled(self):
        r = self.client.get(reverse("storefront:search"), {"q": "HIFU"})
        self.assertEqual(r["X-Robots-Tag"], "noindex, nofollow")
        self.assertContains(r, 'content="noindex, nofollow"')
        self.assertNotContains(r, '<link rel="canonical"')
        self.assertEqual(OfferClick.objects.count(), 0)

    def test_xss_search_query_is_escaped(self):
        r = self.client.get(reverse("storefront:search"), {"q": '<script>boom</script>'})
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "<script>boom</script>")
        self.assertContains(r, "&lt;script&gt;boom&lt;/script&gt;")

    def test_category_has_progressive_filter_controls_without_changing_offer_order(self):
        r = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": self.family.slug})
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Encontre o equipamento certo")
        self.assertContains(r, 'data-explorer-sort')
        self.assertContains(r, 'data-explorer-type')
        self.assertContains(r, 'data-compare-panel')
        self.assertContains(r, self.offer.title)
        self.assertNotContains(r, self.hidden.title)
        self.assertEqual(OfferClick.objects.count(), 0)

    def test_home_mobile_search_is_same_origin_and_does_not_modify_categories(self):
        r = self.client.get(reverse("storefront:home"))
        self.assertContains(r, 'action="/pesquisar/"')
        self.assertContains(r, 'name="q"')
        self.assertContains(r, 'id="familias"')
        self.assertContains(r, self.family.name)
        self.assertNotContains(r, self.hidden.title)
