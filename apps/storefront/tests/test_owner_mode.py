from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Offer, OfferCandidate, OfferFamilyPlacement, ProductFamily


class StorefrontOwnerModeTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.staff = users.objects.create_user(
            username="store-owner", password="test-only", is_staff=True
        )
        self.nonstaff = users.objects.create_user(
            username="shop-user", password="test-only", is_staff=False
        )
        self.family = ProductFamily.objects.create(name="HIFU", slug="owner-mode-hifu")
        self.target_family = ProductFamily.objects.create(name="RF", slug="owner-mode-rf")
        self.public_offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="owner-mode-public",
            title="Public HIFU machine",
            affiliate_url="https://affiliate.example/public",
            protocol_verified_at=timezone.now(),
            is_active=True,
        )
        OfferFamilyPlacement.objects.create(offer=self.public_offer, product_family=self.family)
        self.pending = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="owner-mode-pending",
            title="Private pending candidate",
            product_url="https://example.com/pending",
        )
        self.hidden_offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="owner-mode-hidden",
            title="Private hidden approved offer",
            product_url="https://example.com/hidden",
            affiliate_url="https://affiliate.example/hidden",
            protocol_verified_at=timezone.now(),
            is_active=True,
            owner_hidden=True,
        )
        OfferFamilyPlacement.objects.create(offer=self.hidden_offer, product_family=self.family)
        self.hidden_candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="owner-mode-hidden",
            title=self.hidden_offer.title,
            status=OfferCandidate.Status.APPROVED,
            approved_offer=self.hidden_offer,
        )
        self.url = reverse("storefront:product-family-detail", args=[self.family.slug])

    def assert_zero_private_management(self, response):
        self.assertContains(response, "Public HIFU machine")
        self.assertNotContains(response, "Modo proprietário")
        self.assertNotContains(response, "Gestão desta família")
        self.assertNotContains(response, "Private pending candidate")
        self.assertNotContains(response, "Private hidden approved offer")
        self.assertNotContains(response, "RETIRAR DA MONTRA")
        self.assertNotContains(response, "Aprovar")
        self.assertNotContains(response, "Confirmar rejeição")
        self.assertNotContains(response, "/painel/familias/")

    def test_anonymous_gets_normal_storefront_with_zero_private_management(self):
        self.assert_zero_private_management(self.client.get(self.url))

    def test_nonstaff_gets_normal_storefront_with_zero_private_management(self):
        self.client.force_login(self.nonstaff)
        self.assert_zero_private_management(self.client.get(self.url))

    def test_staff_gets_same_storefront_plus_integrated_management(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public HIFU machine")
        self.assertContains(response, "Modo proprietário")
        self.assertContains(response, "Gestão desta família")
        self.assertContains(response, "Private pending candidate")
        self.assertContains(response, "Private hidden approved offer")
        self.assertContains(response, "RETIRAR DA MONTRA")
        self.assertContains(response, "Aprovar")
        self.assertContains(response, "Confirmar rejeição")
        self.assertContains(response, "Mudar família")
        self.assertContains(response, self.target_family.name)
        self.assertContains(response, "Voltar a publicar")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_staff_toolbar_is_compact_and_storefront_first(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertContains(response, "Loja")
        self.assertContains(response, "Gerir família")
        self.assertContains(response, "Painel")
        self.assertContains(response, "Sair")
        self.assertNotContains(response, ">Famílias<")
        self.assertNotContains(response, ">Na montra<")
        self.assertNotContains(response, ">Retirados<")

    def test_hidden_stale_offer_shows_revalidate_not_publish(self):
        self.hidden_offer.protocol_verified_at = timezone.now() - timedelta(days=8)
        self.hidden_offer.save(update_fields=["protocol_verified_at"])
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertContains(response, "Revalidação necessária")
        self.assertContains(response, "Revalidar")
        self.assertNotContains(response, "Voltar a publicar")

    def test_contextual_hide_returns_to_same_storefront_family(self):
        self.client.force_login(self.staff)
        hide_url = reverse("owner-panel:offer-hide", args=[self.family.slug, self.public_offer.pk])
        response = self.client.post(
            hide_url,
            {"next": f"{self.url}#gestao-owner"},
        )
        self.assertRedirects(
            response,
            f"{self.url}#gestao-owner",
            fetch_redirect_response=False,
        )
        self.public_offer.refresh_from_db()
        self.assertTrue(self.public_offer.owner_hidden)

    def test_storefront_owner_mode_does_not_duplicate_public_offer_in_private_queue(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        private = response.context["owner_private_approved"]
        self.assertEqual([c.pk for c in private], [self.hidden_candidate.pk])
        self.assertNotIn(self.public_offer.pk, [c.approved_offer_id for c in private])

    def test_owner_mode_uses_exact_five_rejection_signals(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertContains(response, 'name="review_signals"', count=5)
        self.assertContains(response, "Sim, entrega em Portugal")
        self.assertContains(response, "Não entrega em Portugal")
        self.assertContains(response, "Não envia para Portugal")
        self.assertContains(response, "País de envio fora dos cinco permitidos")
        self.assertContains(response, "Anúncio indisponível")


class StorefrontOwnerModeMobileStructureTests(TestCase):
    def test_compact_toolbar_and_mobile_management_structure(self):
        from django.conf import settings

        base = (settings.BASE_DIR / "apps/storefront/templates/storefront/base.html").read_text()
        tools = (
            settings.BASE_DIR
            / "apps/storefront/templates/storefront/components/owner_family_tools.html"
        ).read_text()
        css = (settings.BASE_DIR / "apps/storefront/static/storefront/storefront.css").read_text()
        self.assertIn('name="viewport" content="width=device-width, initial-scale=1"', base)
        self.assertIn('class="owner-private-bar"', base)
        self.assertIn('id="gestao-owner"', tools)
        self.assertIn("overflow-x: auto", css)
        self.assertIn("min-height: 38px", css)
        self.assertIn("@media (max-width: 480px)", css)
        self.assertIn("grid-template-columns: repeat(2, minmax(0,1fr))", css)
        for width in (360, 390, 430):
            with self.subTest(width=width):
                self.assertLessEqual(width, 480)
