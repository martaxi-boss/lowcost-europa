from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import (
    Offer,
    OfferClick,
    OfferFamilyPlacement,
    ProductFamily,
)


class StorefrontConversionMarkupTests(SimpleTestCase):
    def test_homepage_primary_cta_targets_family_selector(self):
        home = (
            settings.BASE_DIR
            / "apps/storefront/templates/storefront/home.html"
        ).read_text()
        self.assertIn("VER EQUIPAMENTOS E PREÇOS", home)
        self.assertIn('href="#familias"', home)
        self.assertIn('id="familias"', home)

    def test_offer_cta_keeps_go_route_and_external_purchase_disclosure(self):
        offer_card = (
            settings.BASE_DIR
            / "apps/storefront/templates/storefront/components/offer_card.html"
        ).read_text()
        self.assertIn("VER PREÇO E COMPRAR NO ALIEXPRESS", offer_card)
        self.assertIn("{% url 'storefront:offer-go' offer.pk %}", offer_card)
        self.assertIn("Compra externa.", offer_card)
        self.assertIn("alguns links podem gerar comissão afiliada", offer_card)

    def test_whatsapp_templates_use_internal_route_and_no_third_party_js(self):
        files = [
            settings.BASE_DIR / "apps/storefront/templates/storefront/home.html",
            settings.BASE_DIR / "apps/storefront/templates/storefront/base.html",
            settings.BASE_DIR / "apps/storefront/templates/storefront/contacto.html",
            settings.BASE_DIR
            / "apps/storefront/templates/storefront/components/offer_card.html",
        ]
        combined = "\n".join(path.read_text() for path in files)
        self.assertIn("storefront:whatsapp-contact", combined)
        self.assertNotIn("351961726755", combined)
        self.assertNotIn("+351 961 726 755", combined)
        self.assertIn("storefront/product-images.js", combined)
        self.assertNotIn('<script src="https://', combined.lower())


class StorefrontConversionBehaviorTests(TestCase):
    FAMILY_SLUGS = (
        "cavitacao-rf-vacuum-corpo",
        "hydrodermoabrasao-aqua-facial-multifuncoes",
        "pressoterapia-vacuum-drenagem",
        "hifu",
        "diodo-laser-remocao-tatuagens-pigmentacao",
    )

    def test_five_family_navigation_remains_primary_public_navigation(self):
        for index, slug in enumerate(self.FAMILY_SLUGS, start=1):
            ProductFamily.objects.create(
                name=f"Família pública {index}",
                slug=slug,
                display_order=index,
            )

        response = self.client.get(reverse("storefront:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "VER EQUIPAMENTOS E PREÇOS")
        self.assertContains(response, 'href="#familias"')
        self.assertContains(response, 'class="family-index family-index--compact"')
        for slug in self.FAMILY_SLUGS:
            self.assertContains(
                response,
                reverse("storefront:product-family-detail", kwargs={"slug": slug}),
            )
        for owner_text in ("Gestão ativa", "APROVAR", "REJEITAR", "A rever"):
            self.assertNotContains(response, owner_text)

    def test_offer_cta_routes_through_existing_go_behavior(self):
        family = ProductFamily.objects.create(
            name="CTA Family",
            slug="cta-family",
            display_order=1,
        )
        now = timezone.now()
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="cta-conversion-offer",
            title="CTA conversion product",
            affiliate_url="https://affiliate.example.test/destination",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=now,
            protocol_verified_at=now,
            is_active=True,
            owner_hidden=False,
        )
        OfferFamilyPlacement.objects.create(
            offer=offer,
            product_family=family,
            selection_position=1,
        )

        detail = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        go_url = reverse("storefront:offer-go", kwargs={"offer_id": offer.pk})
        self.assertContains(detail, "VER PREÇO E COMPRAR NO ALIEXPRESS")
        self.assertContains(detail, go_url)
        self.assertContains(detail, "Compra externa.")
        self.assertNotContains(detail, offer.affiliate_url)

        redirect_response = self.client.get(go_url)
        self.assertEqual(redirect_response.status_code, 302)
        self.assertEqual(
            redirect_response["Location"],
            "https://affiliate.example.test/destination",
        )
        self.assertEqual(OfferClick.objects.filter(offer=offer).count(), 1)

    def test_whatsapp_internal_route_redirects_to_authorized_number(self):
        response = self.client.get(reverse("storefront:whatsapp-contact"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            "https://wa.me/351965471236"
            "?text=Ol%C3%A1%2C%20vi%20um%20equipamento%20no%20Lowcost%20Europa%20"
            "e%20gostava%20de%20esclarecer%20uma%20d%C3%BAvida.",
        )

        home = self.client.get(reverse("storefront:home"))
        contact = self.client.get(reverse("storefront:contacto"))
        self.assertContains(home, reverse("storefront:whatsapp-contact"))
        self.assertContains(contact, reverse("storefront:whatsapp-contact"))
        self.assertContains(contact, "+351 965 471 236")
        combined = home.content.decode() + contact.content.decode()
        self.assertNotIn("351961726755", combined)
        self.assertNotIn("+351 961 726 755", combined)
