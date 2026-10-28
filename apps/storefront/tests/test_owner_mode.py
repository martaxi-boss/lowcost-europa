from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import (
    CandidateDecision,
    Offer,
    OfferCandidate,
    OfferEditorialEvent,
    OfferFamilyPlacement,
    ProductFamily,
)


class StorefrontOwnerModeTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.staff = users.objects.create_user(
            username="store-owner", password="test-only", is_staff=True
        )
        self.nonstaff = users.objects.create_user(username="shop-user", password="test-only")
        self.family = ProductFamily.objects.create(name="HIFU", slug="owner-mode-hifu")
        self.target_family = ProductFamily.objects.create(name="RF", slug="owner-mode-rf")
        self.public_offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="owner-mode-public",
            title="Public HIFU machine",
            affiliate_url="https://affiliate.example/public",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=timezone.now(),
            ship_from_country="PL",
            ship_from_verified_at=timezone.now(),
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
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=timezone.now(),
            ship_from_country="PL",
            ship_from_verified_at=timezone.now(),
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
        self.rejected = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="owner-mode-rejected",
            title="Rejected candidate",
            status=OfferCandidate.Status.REJECTED,
        )
        self.url = reverse("storefront:product-family-detail", args=[self.family.slug])

    def assert_zero_private_management(self, response):
        self.assertContains(response, "Public HIFU machine")
        for private_text in (
            "Gestão ativa",
            "Gestão da família",
            "Private pending candidate",
            "Private hidden approved offer",
            "Rejected candidate",
            "RETIRAR DA MONTRA",
            "Confirmar rejeição",
        ):
            self.assertNotContains(response, private_text)
        self.assertNotContains(response, "/painel/familias/")

    def test_anonymous_and_nonstaff_get_public_only(self):
        self.assert_zero_private_management(self.client.get(self.url))
        self.client.force_login(self.nonstaff)
        self.assert_zero_private_management(self.client.get(self.url))

    def test_staff_default_is_same_storefront_plus_compact_management(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertContains(response, "Public HIFU machine")
        self.assertContains(response, "Gestão ativa")
        self.assertContains(response, "Resumo")
        self.assertContains(response, "Gestão da família")
        self.assertContains(response, "Montra")
        self.assertContains(response, "A rever")
        self.assertContains(response, "Retirados")
        self.assertContains(response, "Revalidação")
        self.assertContains(response, "Rejeitados")
        self.assertContains(response, "RETIRAR DA MONTRA")
        self.assertNotContains(response, "Private pending candidate")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")
        self.assertIn("Cookie", response.get("Vary", ""))

    def test_rever_tab_shows_pending_with_one_click_approve_and_reason_selector(self):
        self.client.force_login(self.staff)
        response = self.client.get(f"{self.url}?gestao=rever")
        self.assertContains(response, "Private pending candidate")
        self.assertNotContains(response, "Private hidden approved offer")
        self.assertNotContains(response, "Rejected candidate")
        self.assertContains(response, "APROVAR")
        self.assertContains(response, "MOTIVO DA REJEIÇÃO")
        self.assertNotContains(response, 'name="review_signals"')
        self.assertNotContains(response, 'name="ship_from_country"')
        self.assertContains(response, "Mudar família")
        self.assertContains(response, 'name="note"')

    def test_approved_hidden_is_distinct_from_editorially_retired(self):
        self.client.force_login(self.staff)
        approved = self.client.get(f"{self.url}?gestao=aprovados")
        self.assertContains(approved, "Private hidden approved offer")
        self.assertContains(approved, "Aprovado fora da montra")
        self.assertContains(approved, "Colocar na montra")
        retired = self.client.get(f"{self.url}?gestao=retirados")
        self.assertNotContains(retired, "Private hidden approved offer")

        OfferEditorialEvent.objects.create(
            offer=self.hidden_offer,
            action=OfferEditorialEvent.Action.HIDE,
            previous_owner_hidden=False,
            new_owner_hidden=True,
            acted_by=self.staff,
        )
        retired = self.client.get(f"{self.url}?gestao=retirados")
        self.assertContains(retired, "Private hidden approved offer")
        self.assertContains(retired, "Retirado da montra")

        self.hidden_offer.protocol_verified_at = None
        self.hidden_offer.save(update_fields=["protocol_verified_at"])
        revalidate = self.client.get(f"{self.url}?gestao=revalidar")
        self.assertContains(revalidate, "Private hidden approved offer")
        self.assertContains(revalidate, "Revalidar")
        self.hidden_offer.is_active = False
        self.hidden_offer.save(update_fields=["is_active"])
        inactive = self.client.get(f"{self.url}?gestao=retirados")
        self.assertContains(inactive, "Indisponível")

    def test_old_verified_offer_does_not_require_revalidation(self):
        self.hidden_offer.protocol_verified_at = timezone.now() - timedelta(days=30)
        self.hidden_offer.save(update_fields=["protocol_verified_at"])
        self.client.force_login(self.staff)

        approved = self.client.get(f"{self.url}?gestao=aprovados")
        revalidate = self.client.get(f"{self.url}?gestao=revalidar")

        self.assertContains(approved, "Private hidden approved offer")
        self.assertNotContains(revalidate, "Private hidden approved offer")

    def test_revalidation_and_rejected_tabs_are_inline(self):
        self.hidden_offer.protocol_verified_at = None
        self.hidden_offer.save(update_fields=["protocol_verified_at"])
        self.client.force_login(self.staff)
        revalidate = self.client.get(f"{self.url}?gestao=revalidar")
        self.assertContains(revalidate, "Private hidden approved offer")
        self.assertContains(revalidate, "Revalidar")
        rejected = self.client.get(f"{self.url}?gestao=rejeitados")
        self.assertContains(rejected, "Rejected candidate")
        self.assertNotContains(rejected, "Aprovar")
        self.assertNotContains(rejected, "Confirmar rejeição")

    def test_view_as_customer_hides_tools_but_keeps_session(self):
        self.client.force_login(self.staff)
        response = self.client.get(f"{self.url}?owner_preview=public")
        self.assertContains(response, "Public HIFU machine")
        self.assertContains(response, "A ver como cliente")
        self.assertContains(response, "Voltar à gestão")
        self.assertNotContains(response, "Gestão da família")
        self.assertNotContains(response, "RETIRAR DA MONTRA")
        self.assertNotContains(response, "Private pending candidate")
        self.assertIn("_auth_user_id", self.client.session)

    def test_contextual_hide_returns_to_same_family_retirados(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("owner-panel:offer-hide", args=[self.family.slug, self.public_offer.pk]),
            {"next": f"{self.url}?gestao=retirados#gestao-owner"},
        )
        self.assertRedirects(
            response, f"{self.url}?gestao=retirados#gestao-owner", fetch_redirect_response=False
        )
        self.public_offer.refresh_from_db()
        self.assertTrue(self.public_offer.owner_hidden)

    def test_inline_approve_returns_to_same_family_without_generating_link(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("owner-panel:candidate-approve", args=[self.family.slug, self.pending.pk]),
            {
                "next": f"{self.url}?gestao=rever#gestao-owner",
            },
        )
        self.assertRedirects(
            response, f"{self.url}?gestao=rever#gestao-owner", fetch_redirect_response=False
        )
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, OfferCandidate.Status.APPROVED)
        self.assertEqual(self.pending.approved_offer.affiliate_url, "")
        self.assertTrue(self.pending.approved_offer.owner_hidden)

    def test_inline_reject_and_move_reuse_services(self):
        self.client.force_login(self.staff)
        reject_candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="reject-inline",
            title="Reject inline",
        )
        response = self.client.post(
            reverse("owner-panel:candidate-reject", args=[self.family.slug, reject_candidate.pk]),
            {
                "reason": CandidateDecision.Reason.ORIGIN_NOT_ALLOWED,
                "next": f"{self.url}?gestao=rever#gestao-owner",
            },
        )
        self.assertEqual(response.status_code, 302)
        reject_candidate.refresh_from_db()
        self.assertEqual(reject_candidate.status, OfferCandidate.Status.REJECTED)
        decision = reject_candidate.decisions.get()
        self.assertEqual(decision.reason, CandidateDecision.Reason.ORIGIN_NOT_ALLOWED)
        self.assertEqual(decision.review_signals, [])
        move_candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="move-inline",
            title="Move inline",
        )
        before = OfferCandidate.objects.count()
        self.client.post(
            reverse("owner-panel:candidate-move", args=[self.family.slug, move_candidate.pk]),
            {
                "target_family": self.target_family.pk,
                "next": f"{self.url}?gestao=rever#gestao-owner",
            },
        )
        move_candidate.refresh_from_db()
        self.assertEqual(move_candidate.product_family, self.target_family)
        self.assertEqual(OfferCandidate.objects.count(), before)


class OwnerStorefrontNavigationTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            username="nav-owner", password="x", is_staff=True
        )
        self.family = ProductFamily.objects.create(name="Navigation HIFU", slug="navigation-hifu")

    def test_staff_home_keeps_public_home_and_adds_manage_link(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("storefront:home"))
        self.assertContains(
            response,
            "Equipamentos profissionais de estética, selecionados para uma compra informada.",
        )
        self.assertNotContains(response, "enviados da Europa, a preços mais acessíveis")
        self.assertContains(response, "Gestão ativa")
        self.assertContains(response, "Gerir")
        family_url = reverse("storefront:product-family-detail", args=[self.family.slug])
        self.assertContains(response, f"{family_url}?gestao=montra#gestao-owner")

    def test_panel_summary_links_to_real_storefront_family(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("owner-panel:dashboard"))
        self.assertContains(response, "VER LOJA")
        family_url = reverse("storefront:product-family-detail", args=[self.family.slug])
        self.assertContains(response, f"{family_url}?gestao=montra#gestao-owner")


class StorefrontOwnerModeMobileStructureTests(TestCase):
    def test_compact_toolbar_tabs_and_mobile_structure(self):
        from django.conf import settings

        base = (settings.BASE_DIR / "apps/storefront/templates/storefront/base.html").read_text()
        tools = (
            settings.BASE_DIR
            / "apps/storefront/templates/storefront/components/owner_family_tools.html"
        ).read_text()
        css = (settings.BASE_DIR / "apps/storefront/static/storefront/storefront.css").read_text()
        self.assertIn('class="owner-private-bar"', base)
        self.assertIn('class="owner-management-tabs"', tools)
        self.assertIn("overflow-x:auto", css.replace(" ", ""))
        self.assertIn("min-height:38px", css.replace(" ", ""))
        self.assertIn("@media(max-width:480px)", css.replace(" ", ""))
        for width in (360, 390, 430):
            with self.subTest(width=width):
                self.assertLessEqual(width, 480)
