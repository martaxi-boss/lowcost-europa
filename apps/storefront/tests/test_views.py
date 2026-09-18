from datetime import timedelta
from decimal import Decimal

from django.db.models.signals import post_save
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Offer, OfferFamilyPlacement, OfferObservation, ProductFamily


class StorefrontViewTests(TestCase):
    def setUp(self):
        def add_legacy_equivalent_placement(sender, instance, created, **kwargs):
            if created:
                verified_at = timezone.now()
                affiliate_url = instance.affiliate_url or f"https://affiliate.example/{instance.pk}"
                Offer.objects.filter(pk=instance.pk).update(
                    affiliate_url=affiliate_url,
                    ship_from_country="PL",
                    ship_from_verified_at=verified_at,
                    protocol_verified_at=verified_at
                )
                instance.affiliate_url = affiliate_url
                instance.ship_from_country = "PL"
                instance.ship_from_verified_at = verified_at
                instance.protocol_verified_at = verified_at
            if created and instance.product_family_id:
                OfferFamilyPlacement.objects.create(
                    offer=instance,
                    product_family_id=instance.product_family_id,
                    selection_position=1 if instance.is_primary else None,
                )

        self._placement_receiver = add_legacy_equivalent_placement
        post_save.connect(self._placement_receiver, sender=Offer, weak=False)

    def tearDown(self):
        post_save.disconnect(self._placement_receiver, sender=Offer)
        super().tearDown()

    def test_homepage_returns_200_with_empty_state(self):
        response = self.client.get(reverse("storefront:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A seleção pública está a ser preparada")

    def test_missing_product_family_returns_404(self):
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": "missing"})
        )
        self.assertEqual(response.status_code, 404)

    def test_detail_renders_family_and_active_offer(self):
        family = ProductFamily.objects.create(
            name="HIFU Professional",
            slug="hifu-professional",
            status=ProductFamily.Status.TESTING,
        )
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="123",
            product_family=family,
            title="7D HIFU Professional Machine",
        )
        OfferObservation.objects.create(
            offer=offer,
            price=Decimal("199.90"),
            currency="EUR",
            sales_count=12,
            search_delivery_days=5,
            delivery_days=None,
        )
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "HIFU Professional")
        self.assertContains(response, "7D HIFU Professional Machine")
        self.assertContains(response, "199,90 EUR")
        self.assertContains(response, "Estimativa indicada pela pesquisa: 5 dias")

    def test_null_fields_do_not_render_false_zero_values(self):
        family = ProductFamily.objects.create(name="Test Family", slug="test-family")
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="nulls",
            product_family=family,
            title="Offer with unknown values",
        )
        OfferObservation.objects.create(
            offer=offer,
            price=None,
            evaluation_rate_percent=None,
            sales_count=None,
            search_delivery_days=None,
            delivery_days=None,
        )
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        self.assertContains(response, "Não disponível")
        self.assertNotContains(response, "0 EUR")
        self.assertNotContains(response, "0 estrelas")
        self.assertNotContains(response, "0 dias")

    def test_strong_internal_statuses_are_not_promoted_publicly(self):
        for status in (
            ProductFamily.Status.VERIFIED,
            ProductFamily.Status.PROVEN,
            ProductFamily.Status.WINNER,
        ):
            family = ProductFamily.objects.create(
                name=f"Family {status}",
                slug=f"family-{status.lower()}",
                status=status,
            )
            response = self.client.get(
                reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
            )
            self.assertContains(response, "Em avaliação")
            self.assertNotContains(response, f">{status}<")

    def test_templates_do_not_make_guaranteed_delivery_claims(self):
        family = ProductFamily.objects.create(name="Logistics", slug="logistics")
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="delivery",
            product_family=family,
        )
        OfferObservation.objects.create(offer=offer, search_delivery_days=5)
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        content = response.content.decode().lower()
        self.assertNotIn("entrega garantida", content)
        self.assertNotIn("guaranteed", content)
        self.assertIn("estimativa indicada pela pesquisa", content)

    def test_family_without_offers_has_safe_empty_state(self):
        family = ProductFamily.objects.create(name="Empty Family", slug="empty-family")
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        self.assertContains(response, "Seleção em preparação")

    def test_latest_observation_is_used_for_display(self):
        family = ProductFamily.objects.create(name="Latest", slug="latest")
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="latest-offer",
            product_family=family,
        )
        now = timezone.now()
        OfferObservation.objects.create(
            offer=offer,
            price=Decimal("100.00"),
            currency="EUR",
            observed_at=now - timedelta(days=1),
        )
        OfferObservation.objects.create(
            offer=offer, price=Decimal("150.00"), currency="EUR", observed_at=now
        )
        response = self.client.get(reverse("storefront:home"))
        self.assertContains(response, "150,00 EUR")
        self.assertNotContains(response, "100,00 EUR")

    def test_retired_family_hidden_from_home_but_detail_remains_accessible(self):
        family = ProductFamily.objects.create(
            name="Retired Family", slug="retired-family", status=ProductFamily.Status.RETIRED
        )
        home = self.client.get(reverse("storefront:home"))
        detail = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        self.assertNotContains(home, "Retired Family")
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Retired Family")

    def test_inactive_offer_is_not_rendered_publicly(self):
        family = ProductFamily.objects.create(name="Inactive Test", slug="inactive-test")
        Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="inactive-offer",
            product_family=family,
            title="Hidden inactive offer",
            is_active=False,
        )
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        self.assertNotContains(response, "Hidden inactive offer")
        self.assertContains(response, "Seleção em preparação")

    def test_conflicting_logistics_are_presented_neutrally(self):
        family = ProductFamily.objects.create(name="Conflict", slug="conflict")
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="conflict-offer",
            product_family=family,
        )
        OfferObservation.objects.create(offer=offer, search_delivery_days=3, delivery_days=5)
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        content = response.content.decode()
        self.assertIn("As fontes apresentam estimativas diferentes", content)
        self.assertNotIn("Entrega garantida", content)
        self.assertNotIn("Estimativa indicada pela pesquisa: 3 dias", content)
        self.assertNotIn("Estimativa indicada no detalhe: 5 dias", content)

    def test_editorial_primary_is_display_offer_even_when_older(self):
        family = ProductFamily.objects.create(name="Primary Display", slug="primary-display")
        now = timezone.now()
        primary = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="primary-display-offer",
            product_family=family,
            title="Editorial Primary",
            is_primary=True,
            first_seen_at=now - timedelta(days=2),
            last_seen_at=now - timedelta(days=1),
        )
        newer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="newer-display-offer",
            product_family=family,
            title="Newer Fallback",
            first_seen_at=now - timedelta(days=1),
            last_seen_at=now,
        )
        OfferObservation.objects.create(offer=primary, price=Decimal("111.00"), currency="EUR")
        OfferObservation.objects.create(offer=newer, price=Decimal("222.00"), currency="EUR")
        response = self.client.get(reverse("storefront:home"))
        self.assertContains(response, "111,00 EUR")
        self.assertNotContains(response, "222,00 EUR")

    def test_editorial_primary_appears_first_on_detail(self):
        family = ProductFamily.objects.create(name="Primary Order", slug="primary-order")
        now = timezone.now()
        primary = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="primary-order-offer",
            product_family=family,
            title="Editorial Primary First",
            is_primary=True,
            first_seen_at=now - timedelta(days=2),
            last_seen_at=now - timedelta(days=1),
        )
        Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="other-order-offer",
            product_family=family,
            title="Other Offer Second",
            first_seen_at=now - timedelta(days=1),
            last_seen_at=now,
        )
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        content = response.content.decode()
        self.assertLess(content.index(primary.title), content.index("Other Offer Second"))

    def test_no_primary_keeps_deterministic_latest_offer_fallback(self):
        family = ProductFamily.objects.create(name="Fallback Order", slug="fallback-order")
        now = timezone.now()
        older = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="older-fallback",
            product_family=family,
            title="Older Fallback",
            first_seen_at=now - timedelta(days=2),
            last_seen_at=now - timedelta(days=1),
        )
        newer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="newer-fallback",
            product_family=family,
            title="Newer Fallback",
            first_seen_at=now - timedelta(days=1),
            last_seen_at=now,
        )
        OfferObservation.objects.create(offer=older, price=Decimal("111.00"), currency="EUR")
        OfferObservation.objects.create(offer=newer, price=Decimal("222.00"), currency="EUR")
        response = self.client.get(reverse("storefront:home"))
        self.assertContains(response, "222,00 EUR")
        self.assertNotContains(response, "111,00 EUR")

    def test_inactive_offer_is_never_used_as_primary(self):
        family = ProductFamily.objects.create(
            name="Inactive Primary Family", slug="inactive-primary"
        )
        active = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="active-fallback",
            product_family=family,
            title="Active Fallback",
        )
        inactive = Offer(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="inactive-primary-invalid",
            product_family=family,
            title="Hidden Inactive Offer",
            is_active=False,
            is_primary=False,
        )
        inactive.save()
        OfferObservation.objects.create(offer=active, price=Decimal("333.00"), currency="EUR")
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        self.assertContains(response, "Active Fallback")
        self.assertNotContains(response, "Hidden Inactive Offer")

    def test_primary_selection_adds_no_promotional_language(self):
        family = ProductFamily.objects.create(name="Neutral Primary", slug="neutral-primary")
        Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="neutral-primary-offer",
            product_family=family,
            title="Neutral Offer",
            is_primary=True,
        )
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        content = response.content.decode().lower()
        for phrase in ("winner", "recomendado", "melhor oferta", "escolha nº 1"):
            self.assertNotIn(phrase, content)

    def test_homepage_renders_display_offer_image(self):
        family = ProductFamily.objects.create(name="Image Family", slug="image-family")
        primary = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="image-primary",
            product_family=family,
            title="Primary image offer",
            image_url="https://images.example.test/primary.jpg",
            is_primary=True,
        )
        Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="image-other",
            product_family=family,
            title="Other image offer",
            image_url="https://images.example.test/other.jpg",
        )
        response = self.client.get(reverse("storefront:home"))
        self.assertContains(response, primary.image_url)
        self.assertContains(response, 'alt="Primary image offer"')
        self.assertNotContains(response, "https://images.example.test/other.jpg")

    def test_detail_renders_each_offers_own_image(self):
        family = ProductFamily.objects.create(name="Detail Images", slug="detail-images")
        first = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="detail-image-one",
            product_family=family,
            title="First image offer",
            image_url="https://images.example.test/one.jpg",
        )
        second = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="detail-image-two",
            product_family=family,
            title="Second image offer",
            image_url="http://images.example.test/two.jpg",
        )
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        self.assertContains(response, first.image_url)
        self.assertContains(response, second.image_url)
        self.assertContains(response, 'alt="First image offer"')
        self.assertContains(response, 'alt="Second image offer"')
        self.assertContains(response, 'loading="lazy"', count=2)

    def test_missing_or_invalid_image_url_keeps_placeholder(self):
        family = ProductFamily.objects.create(name="Image Fallback", slug="image-fallback")
        Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="missing-image",
            product_family=family,
            title="Missing image offer",
            image_url="",
        )
        Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="invalid-image",
            product_family=family,
            title="Invalid image offer",
            image_url="javascript:broken",
        )
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        content = response.content.decode()
        self.assertEqual(content.count("offer-card__media--placeholder"), 2)
        self.assertNotIn("javascript:broken", content)

    def test_product_images_do_not_expose_affiliate_url(self):
        family = ProductFamily.objects.create(name="Safe Image", slug="safe-image")
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="safe-image-offer",
            product_family=family,
            title="Safe image offer",
            image_url="https://images.example.test/safe.jpg",
            affiliate_url="https://affiliate.example.test/private-destination",
        )
        response = self.client.get(reverse("storefront:home"))
        self.assertContains(response, offer.image_url)
        self.assertNotContains(response, offer.affiliate_url)

    def test_homepage_has_commercial_readiness_sections_and_navigation(self):
        family = ProductFamily.objects.create(name="Visual Family", slug="visual-family")
        response = self.client.get(reverse("storefront:home"))
        self.assertContains(response, "Selecionamos. Organizamos. Comparamos.")
        self.assertContains(response, "5 categorias")
        self.assertContains(response, "Produtos em destaque")
        self.assertContains(response, "Como ajudamos")
        self.assertContains(response, "Como funciona")
        self.assertContains(response, "Transparência comercial")
        self.assertContains(response, family.name)
        self.assertContains(response, 'aria-label="Navegação principal"')
        self.assertContains(response, reverse("storefront:contacto"))

    def test_external_offer_cta_is_explicit_without_live_click(self):
        family = ProductFamily.objects.create(name="CTA Family", slug="cta-family")
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="cta-offer",
            product_family=family,
            title="CTA Product",
            affiliate_url="https://affiliate.example.test/destination",
        )
        OfferObservation.objects.create(
            offer=offer, price=Decimal("499.00"), currency="EUR", search_delivery_days=5
        )
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        self.assertContains(response, "Preço observado")
        self.assertContains(response, "Ver oferta no parceiro")
        self.assertContains(response, reverse("storefront:offer-go", kwargs={"offer_id": offer.pk}))
        self.assertNotContains(response, "Comprar agora")
        self.assertNotContains(response, offer.affiliate_url)

    def test_homepage_does_not_present_editorial_selection_as_ranking(self):
        family = ProductFamily.objects.create(name="Editorial Family", slug="editorial-family")
        Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="editorial-offer",
            product_family=family,
            title="Editorial Product",
            is_primary=True,
        )
        response = self.client.get(reverse("storefront:home"))
        content = response.content.decode().lower()
        self.assertIn("seleção editorial", content)
        self.assertIn("sem transformar a escolha editorial num ranking", content)
        for phrase in ("melhor produto", "mais vendido", "ranking automático", "winner"):
            self.assertNotIn(phrase, content)
        self.assertNotIn('class="badge">winner', content)
        self.assertNotIn('class="badge">proven', content)

    def test_family_page_explains_external_purchase_and_editorial_ordering(self):
        family = ProductFamily.objects.create(name="Clear Family", slug="clear-family")
        Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="clear-offer",
            product_family=family,
            title="Clear Product",
        )
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        self.assertContains(response, "não representa um ranking objetivo")
        self.assertContains(response, "A compra acontece fora do Lowcost Europa")
        self.assertNotContains(response, "melhor oferta")


class InstitutionalTransparencyTests(TestCase):
    def test_institutional_pages_return_200_and_footer_links_are_present(self):
        names = ("como-funciona", "afiliados", "privacidade", "termos", "contacto")
        for name in names:
            response = self.client.get(reverse(f"storefront:{name}"))
            self.assertEqual(response.status_code, 200)
            for footer_name in names:
                self.assertContains(response, reverse(f"storefront:{footer_name}"))

    def test_contact_page_uses_only_authorized_public_channels(self):
        response = self.client.get(reverse("storefront:contacto"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "help.onlinefuture@gmail.com")
        self.assertContains(response, "mailto:help.onlinefuture@gmail.com")
        self.assertContains(response, "+351 961 726 755")
        self.assertContains(response, "https://wa.me/351961726755")
        self.assertContains(response, reverse("storefront:contacto"))
        self.assertContains(response, '<meta name="robots" content="noindex, nofollow">', html=True)

    def test_privacy_and_affiliates_link_to_contact(self):
        for name in ("privacidade", "afiliados"):
            response = self.client.get(reverse(f"storefront:{name}"))
            self.assertContains(response, reverse("storefront:contacto"))
        privacy = self.client.get(reverse("storefront:privacidade"))
        self.assertContains(privacy, "help.onlinefuture@gmail.com")

    def test_sitemap_has_eleven_urls_for_five_active_families(self):
        for index in range(5):
            ProductFamily.objects.create(name=f"Family {index}", slug=f"family-{index}")
        response = self.client.get(reverse("storefront:sitemap"))
        content = response.content.decode()
        self.assertEqual(content.count("<url>"), 11)
        self.assertIn(reverse("storefront:contacto"), content)

    def test_affiliate_disclosure_is_explicit_and_not_guaranteed(self):
        response = self.client.get(reverse("storefront:afiliados"))
        content = response.content.decode().lower()
        self.assertIn("links de afiliado", content)
        self.assertIn("pode receber uma comissão", content)
        self.assertIn("não é garantida", content)

    def test_privacy_page_describes_public_forwarding_and_technical_logs(self):
        response = self.client.get(reverse("storefront:privacidade"))
        content = response.content.decode().lower()
        self.assertIn("encaminhamento", content)
        self.assertIn("oferta", content)
        self.assertIn("data/hora", content)
        self.assertIn("clique", content)
        self.assertIn("não guarda endereço ip", content)
        self.assertIn("não significa utilizador único, compra, conversão ou comissão", content)
        self.assertIn("logs técnicos", content)
        self.assertIn("endereço ip", content)
        self.assertIn("help.onlinefuture@gmail.com", content)
        self.assertNotIn("offerclick", content)
        self.assertNotIn("server-rendered", content)
        self.assertNotIn("set-cookie", content)
        self.assertNotIn("middleware django", content)
        self.assertNotIn("csrf", content)
        self.assertNotIn("nenhum ip é processado", content)

    def test_privacy_metadata_is_public_and_factual(self):
        response = self.client.get(reverse("storefront:privacidade"))
        self.assertContains(response, "Privacidade | Lowcost Europa")
        self.assertContains(
            response,
            "Informação sobre registos de encaminhamento e logs técnicos no Lowcost Europa.",
        )
        content = response.content.decode().lower()
        self.assertNotIn("tracking", content)
        self.assertNotIn("cookies", content)

    def test_terms_present_public_external_purchase_and_affiliate_information(self):
        response = self.client.get(reverse("storefront:termos"))
        content = response.content.decode().lower()
        self.assertContains(response, "Termos de Utilização")
        self.assertIn("vendedor ou plataforma externa", content)
        self.assertIn("preços e a disponibilidade", content)
        self.assertIn("podem alterar-se", content)
        self.assertIn("links de afiliado", content)
        self.assertIn("pode receber uma comissão", content)
        for name in ("privacidade", "afiliados", "contacto"):
            self.assertContains(response, reverse(f"storefront:{name}"))
        for phrase in (
            "pre-launch",
            "not public ready",
            "pending owner input",
            "pré-lançamento",
            "owner input",
            "nif/vat",
        ):
            self.assertNotIn(phrase, content)

    def test_terms_metadata_is_public_and_factual(self):
        response = self.client.get(reverse("storefront:termos"))
        self.assertContains(response, "Termos de Utilização | Lowcost Europa")
        self.assertContains(
            response,
            "Informação sobre a utilização do Lowcost Europa, "
            "encaminhamento para vendedores externos e relação de afiliado.",
        )

    def test_public_institutional_pages_do_not_expose_internal_project_copy(self):
        forbidden = (
            "pre-launch",
            "not public ready",
            "pending owner input",
            "pré-lançamento",
            "owner input",
            "builder",
            "supervisor",
            "staging",
        )
        for name in ("termos", "privacidade", "afiliados", "contacto"):
            response = self.client.get(reverse(f"storefront:{name}"))
            self.assertEqual(response.status_code, 200)
            content = response.content.decode().lower()
            for phrase in forbidden:
                self.assertNotIn(phrase, content)

    def test_default_seo_is_noindex_and_staging_has_no_canonical(self):
        response = self.client.get(reverse("storefront:home"))
        self.assertContains(response, '<meta name="robots" content="noindex, nofollow">', html=True)
        self.assertNotContains(response, 'rel="canonical"')

    @override_settings(
        PUBLIC_SITE_URL="https://lowcost-europa.duckdns.org",
        PUBLIC_INDEXING_ENABLED=False,
    )
    def test_public_site_url_without_indexing_stays_fail_closed(self):
        home = self.client.get(reverse("storefront:home"))
        robots = self.client.get(reverse("storefront:robots"))
        sitemap = self.client.get(reverse("storefront:sitemap"))

        self.assertContains(home, '<meta name="robots" content="noindex, nofollow">', html=True)
        self.assertNotContains(home, 'rel="canonical"')
        self.assertContains(robots, "Disallow: /")
        self.assertNotContains(robots, "Allow: /")
        self.assertNotContains(robots, "Sitemap:")
        self.assertContains(sitemap, "https://lowcost-europa.duckdns.org/")
        self.assertContains(
            sitemap,
            "https://lowcost-europa.duckdns.org/contacto/",
        )
        self.assertNotContains(sitemap, "http://testserver")

    @override_settings(PUBLIC_SITE_URL="", PUBLIC_INDEXING_ENABLED=True)
    def test_indexing_flag_without_public_site_url_fails_closed(self):
        home = self.client.get(reverse("storefront:home"))
        robots = self.client.get(reverse("storefront:robots"))
        self.assertContains(home, '<meta name="robots" content="noindex, nofollow">', html=True)
        self.assertNotContains(home, 'rel="canonical"')
        self.assertContains(robots, "Disallow: /")
        self.assertNotContains(robots, "Allow: /")
        self.assertNotContains(robots, "Sitemap:")

    @override_settings(PUBLIC_SITE_URL="https://example.test", PUBLIC_INDEXING_ENABLED=True)
    def test_canonical_and_indexing_can_be_enabled_with_explicit_public_site_url(self):
        home = self.client.get(reverse("storefront:home"))
        robots = self.client.get(reverse("storefront:robots"))
        self.assertContains(home, '<link rel="canonical" href="https://example.test/">', html=True)
        self.assertContains(home, '<meta name="robots" content="index, follow">', html=True)
        self.assertContains(
            home, '<meta property="og:url" content="https://example.test/">', html=True
        )
        self.assertContains(robots, "Allow: /")
        self.assertContains(robots, "Sitemap: https://example.test/sitemap.xml")
        self.assertNotContains(robots, "Disallow: /")

    def test_robots_disallows_indexing_by_default(self):
        response = self.client.get(reverse("storefront:robots"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertContains(response, "User-agent: *")
        self.assertContains(response, "Disallow: /")

    def test_sitemap_lists_public_pages_and_non_retired_families(self):
        active = ProductFamily.objects.create(name="Active", slug="active-family")
        ProductFamily.objects.create(
            name="Retired", slug="retired-family-sitemap", status=ProductFamily.Status.RETIRED
        )
        response = self.client.get(reverse("storefront:sitemap"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        self.assertContains(response, reverse("storefront:home"))
        self.assertContains(response, reverse("storefront:como-funciona"))
        self.assertContains(response, reverse("storefront:afiliados"))
        self.assertContains(response, reverse("storefront:privacidade"))
        self.assertContains(response, reverse("storefront:termos"))
        self.assertContains(response, reverse("storefront:contacto"))
        self.assertContains(
            response,
            reverse("storefront:product-family-detail", kwargs={"slug": active.slug}),
        )
        self.assertNotContains(response, "retired-family-sitemap")
