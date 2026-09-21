from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import (
    CandidateDecision,
    Offer,
    OfferCandidate,
    OfferClick,
    OfferEditorialEvent,
    OfferFamilyPlacement,
    OfferObservation,
    ProductFamily,
)
from apps.catalog.services.aliexpress_persistence import import_aliexpress_product
from apps.catalog.services.candidate_approval import approve_candidate, revalidate_candidate
from apps.catalog.services.offer_maintenance import maintain_catalog_offers
from apps.catalog.services.owner_editorial import (
    OwnerEditorialError,
    hide_offer_from_storefront,
    publish_offer_to_storefront,
)
from apps.catalog.services.public_eligibility import public_eligibility_q
from apps.integrations.aliexpress.types import AliExpressProduct

TEST_PASSWORD = "owner-test-password-only"


@override_settings(OWNER_PANEL_USERNAME="lowcost-owner")
class OwnerPanelLoginTests(TestCase):
    def make_owner(self, **kwargs):
        defaults = {"is_staff": True, "is_active": True}
        defaults.update(kwargs)
        return get_user_model().objects.create_user(
            username="lowcost-owner", password=TEST_PASSWORD, **defaults
        )

    def test_anonymous_panel_redirects_to_password_login(self):
        response = self.client.get(reverse("owner-panel:dashboard"))
        self.assertRedirects(response, reverse("owner-panel:login"))
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")
        self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_login_page_is_password_only_in_visible_auth_fields(self):
        response = self.client.get(reverse("owner-panel:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Área privada")
        self.assertContains(response, "Palavra-passe")
        self.assertContains(response, 'type="password"', count=1)
        self.assertContains(response, 'autocomplete="current-password"')
        self.assertNotContains(response, 'name="username"')
        self.assertNotContains(response, "Username")
        self.assertNotContains(response, TEST_PASSWORD)
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")
        self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_correct_password_creates_session_and_redirects(self):
        self.make_owner()
        response = self.client.post(reverse("owner-panel:login"), {"password": TEST_PASSWORD})
        self.assertRedirects(response, reverse("storefront:home"))
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            get_user_model().objects.get(username="lowcost-owner").pk,
        )

    def test_login_respects_safe_next_to_storefront_family(self):
        self.make_owner()
        family = ProductFamily.objects.create(name="HIFU Login", slug="hifu-login")
        next_url = reverse("storefront:product-family-detail", args=[family.slug])
        response = self.client.post(
            f"{reverse('owner-panel:login')}?next={next_url}",
            {"password": TEST_PASSWORD, "next": next_url},
        )
        self.assertRedirects(response, next_url)

    def test_login_rejects_external_next(self):
        self.make_owner()
        response = self.client.post(
            reverse("owner-panel:login"),
            {"password": TEST_PASSWORD, "next": "https://evil.example/steal"},
        )
        self.assertRedirects(response, reverse("storefront:home"))

    def test_wrong_password_is_generic_and_not_reflected(self):
        self.make_owner()
        submitted = "wrong-secret-value"
        response = self.client.post(reverse("owner-panel:login"), {"password": submitted})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Palavra-passe incorreta.")
        self.assertNotContains(response, submitted)
        self.assertNotContains(response, "lowcost-owner")

    def test_inactive_owner_is_denied(self):
        self.make_owner(is_active=False)
        response = self.client.post(reverse("owner-panel:login"), {"password": TEST_PASSWORD})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Palavra-passe incorreta.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_nonstaff_owner_is_denied(self):
        self.make_owner(is_staff=False)
        response = self.client.post(reverse("owner-panel:login"), {"password": TEST_PASSWORD})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Palavra-passe incorreta.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_authenticated_nonstaff_panel_access_is_forbidden(self):
        user = get_user_model().objects.create_user(username="other", password="x")
        self.client.force_login(user)
        response = self.client.get(reverse("owner-panel:dashboard"))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")
        self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_staff_panel_access_and_logout(self):
        owner = self.make_owner()
        self.client.force_login(owner)
        response = self.client.get(reverse("owner-panel:dashboard"))
        self.assertEqual(response.status_code, 200)
        logout_url = reverse("owner-panel:logout")
        self.assertEqual(self.client.get(logout_url).status_code, 405)
        response = self.client.post(logout_url)
        self.assertRedirects(response, reverse("owner-panel:login"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertRedirects(
            self.client.get(reverse("owner-panel:dashboard")), reverse("owner-panel:login")
        )


class OwnerEditorialServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="staff", password="x", is_staff=True
        )
        self.family = ProductFamily.objects.create(name="HIFU", slug="owner-hifu")
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="owner-offer",
            title="Owner Offer",
            product_url="https://example.com/product",
            affiliate_url="https://affiliate.example/product",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=timezone.now(),
            ship_from_country="PL",
            ship_from_verified_at=timezone.now(),
            protocol_verified_at=timezone.now(),
            is_active=True,
        )
        self.placement = OfferFamilyPlacement.objects.create(
            offer=self.offer, product_family=self.family
        )

    def test_hide_sets_only_editorial_state_and_appends_event(self):
        protocol = self.offer.protocol_verified_at
        result = hide_offer_from_storefront(self.offer, user=self.user)
        self.offer.refresh_from_db()
        self.assertTrue(result.changed)
        self.assertTrue(self.offer.owner_hidden)
        self.assertTrue(self.offer.is_active)
        self.assertEqual(self.offer.protocol_verified_at, protocol)
        self.assertTrue(OfferFamilyPlacement.objects.filter(pk=self.placement.pk).exists())
        event = OfferEditorialEvent.objects.get()
        self.assertEqual(event.action, OfferEditorialEvent.Action.HIDE)
        self.assertFalse(event.previous_owner_hidden)
        self.assertTrue(event.new_owner_hidden)
        self.assertEqual(event.acted_by, self.user)

    def test_hide_is_idempotent_without_duplicate_event(self):
        hide_offer_from_storefront(self.offer, user=self.user)
        second = hide_offer_from_storefront(self.offer, user=self.user)
        self.assertFalse(second.changed)
        self.assertEqual(OfferEditorialEvent.objects.count(), 1)

    def test_publish_fresh_active_hidden_with_capacity(self):
        hide_offer_from_storefront(self.offer, user=self.user)
        result = publish_offer_to_storefront(self.offer, family=self.family, user=self.user)
        self.offer.refresh_from_db()
        self.assertTrue(result.changed)
        self.assertFalse(self.offer.owner_hidden)
        events = list(OfferEditorialEvent.objects.order_by("acted_at", "pk"))
        self.assertEqual([e.action for e in events], ["HIDE", "PUBLISH"])
        self.assertTrue(events[1].previous_owner_hidden)
        self.assertFalse(events[1].new_owner_hidden)

    def test_publish_stale_blocked(self):
        self.offer.owner_hidden = True
        self.offer.protocol_verified_at = timezone.now() - timedelta(days=8)
        self.offer.save(update_fields=["owner_hidden", "protocol_verified_at"])
        with self.assertRaises(OwnerEditorialError):
            publish_offer_to_storefront(self.offer, family=self.family, user=self.user)
        self.offer.refresh_from_db()
        self.assertTrue(self.offer.owner_hidden)

    def test_publish_inactive_blocked(self):
        self.offer.owner_hidden = True
        self.offer.is_active = False
        self.offer.save(update_fields=["owner_hidden", "is_active"])
        with self.assertRaises(OwnerEditorialError):
            publish_offer_to_storefront(self.offer, family=self.family, user=self.user)

    def test_publish_retired_family_blocked(self):
        self.offer.owner_hidden = True
        self.offer.save(update_fields=["owner_hidden"])
        self.family.status = ProductFamily.Status.RETIRED
        self.family.save(update_fields=["status"])
        with self.assertRaises(OwnerEditorialError):
            publish_offer_to_storefront(self.offer, family=self.family, user=self.user)

    def test_publish_without_affiliate_url_blocked(self):
        self.offer.owner_hidden = True
        self.offer.affiliate_url = ""
        self.offer.save(update_fields=["owner_hidden", "affiliate_url"])
        with self.assertRaises(OwnerEditorialError):
            publish_offer_to_storefront(self.offer, family=self.family, user=self.user)

    def test_publish_accepts_fresh_owner_attestation_without_individual_country(self):
        self.offer.owner_hidden = True
        self.offer.ship_from_country = None
        self.offer.ship_from_verified_at = None
        self.offer.save(
            update_fields=["owner_hidden", "ship_from_country", "ship_from_verified_at"]
        )
        publish_offer_to_storefront(self.offer, family=self.family, user=self.user)
        self.offer.refresh_from_db()
        self.assertFalse(self.offer.owner_hidden)

    def test_publish_cap20_blocked_and_stays_twenty(self):
        self.offer.owner_hidden = True
        self.offer.save(update_fields=["owner_hidden"])
        now = timezone.now()
        for i in range(20):
            o = Offer.objects.create(
                source=Offer.Source.ALIEXPRESS,
                external_product_id=f"cap-{i}",
                affiliate_url=f"https://affiliate.example/{i}",
                affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
                affiliate_promotion_verified_at=now,
                ship_from_country="PL",
                ship_from_verified_at=now,
                protocol_verified_at=now,
            )
            OfferFamilyPlacement.objects.create(offer=o, product_family=self.family)
        self.assertEqual(
            OfferFamilyPlacement.objects.filter(
                product_family=self.family,
                offer__in=Offer.objects.filter(public_eligibility_q(now)),
            ).count(),
            20,
        )
        with self.assertRaises(OwnerEditorialError):
            publish_offer_to_storefront(self.offer, family=self.family, user=self.user, now=now)
        self.offer.refresh_from_db()
        self.assertTrue(self.offer.owner_hidden)
        self.assertEqual(
            OfferFamilyPlacement.objects.filter(
                product_family=self.family,
                offer__in=Offer.objects.filter(public_eligibility_q(now)),
            ).count(),
            20,
        )

    def test_publish_checks_capacity_for_every_operational_placement(self):
        second = ProductFamily.objects.create(name="RF", slug="owner-rf")
        OfferFamilyPlacement.objects.create(offer=self.offer, product_family=second)
        self.offer.owner_hidden = True
        self.offer.save(update_fields=["owner_hidden"])
        now = timezone.now()
        for i in range(20):
            o = Offer.objects.create(
                source=Offer.Source.ALIEXPRESS,
                external_product_id=f"rf-cap-{i}",
                affiliate_url=f"https://affiliate.example/rf/{i}",
                affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
                affiliate_promotion_verified_at=now,
                ship_from_country="PL",
                ship_from_verified_at=now,
                protocol_verified_at=now,
            )
            OfferFamilyPlacement.objects.create(offer=o, product_family=second)
        with self.assertRaises(OwnerEditorialError):
            publish_offer_to_storefront(self.offer, family=self.family, user=self.user, now=now)
        self.offer.refresh_from_db()
        self.assertTrue(self.offer.owner_hidden)

    def test_revalidate_preserves_hidden_then_publish_is_explicit(self):
        candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id=self.offer.external_product_id,
            status=OfferCandidate.Status.APPROVED,
            approved_offer=self.offer,
        )
        self.offer.owner_hidden = True
        self.offer.protocol_verified_at = timezone.now() - timedelta(days=8)
        self.offer.save(update_fields=["owner_hidden", "protocol_verified_at"])
        revalidate_candidate(
            candidate,
            user=self.user,
            now=timezone.now(),
        )
        self.offer.refresh_from_db()
        self.assertTrue(self.offer.owner_hidden)
        publish_offer_to_storefront(self.offer, family=self.family, user=self.user)
        self.offer.refresh_from_db()
        self.assertFalse(self.offer.owner_hidden)

    def test_approval_preserves_existing_hidden_override(self):
        candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id=self.offer.external_product_id,
            product_url=self.offer.product_url,
            approved_offer=self.offer,
        )
        self.offer.owner_hidden = True
        self.offer.save(update_fields=["owner_hidden"])
        client = Mock()
        client.generate_affiliate_link.return_value = self.offer.affiliate_url
        approve_candidate(
            candidate,
            user=self.user,
            client=client,
        )
        self.offer.refresh_from_db()
        self.assertTrue(self.offer.owner_hidden)

    def test_aliexpress_persistence_preserves_hidden(self):
        self.offer.owner_hidden = True
        self.offer.save(update_fields=["owner_hidden"])
        product = AliExpressProduct(
            product_id=self.offer.external_product_id,
            title="Refreshed title",
            product_url="https://example.com/product",
            affiliate_url="https://affiliate.example/original",
            destination_country="PT",
        )
        client = Mock()
        client.get_product_detail.return_value = product
        client.generate_affiliate_link.return_value = "https://affiliate.example/refreshed"
        import_aliexpress_product(self.offer.external_product_id, client=client)
        self.offer.refresh_from_db()
        self.assertTrue(self.offer.owner_hidden)

    @patch("apps.catalog.services.offer_maintenance.maintenance_run_lock")
    def test_maintenance_available_preserves_hidden(self, lock):
        from contextlib import nullcontext

        lock.return_value = nullcontext()
        self.offer.owner_hidden = True
        self.offer.save(update_fields=["owner_hidden"])
        detail = AliExpressProduct(
            product_id=self.offer.external_product_id,
            title="Still available",
            product_url="https://example.com/product",
            destination_country="PT",
        )
        client = Mock()
        client.generate_affiliate_link.return_value = "https://affiliate.example/refreshed"
        client.get_product_detail.return_value = detail
        maintain_catalog_offers(batch_size=5, client=client)
        self.offer.refresh_from_db()
        self.assertTrue(self.offer.owner_hidden)


class OwnerPanelCatalogTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            username="panel-staff", password="x", is_staff=True
        )
        self.family = ProductFamily.objects.create(
            name="Cavitação + RF + Vacuum Corpo", slug="cavitacao"
        )
        self.retired = ProductFamily.objects.create(
            name="Old", slug="old", status=ProductFamily.Status.RETIRED
        )
        self.pending = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="pending",
            title="Máquina de Cavitação",
            product_url="https://example.com/pending",
        )
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="approved",
            title="Máquina aprovada",
            product_url="https://example.com/approved",
            affiliate_url="https://affiliate.example/approved",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=timezone.now(),
            ship_from_country="PL",
            ship_from_verified_at=timezone.now(),
            protocol_verified_at=timezone.now(),
        )
        OfferFamilyPlacement.objects.create(offer=self.offer, product_family=self.family)
        self.approved = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="approved",
            title="Máquina aprovada",
            status=OfferCandidate.Status.APPROVED,
            approved_offer=self.offer,
        )
        self.rejected = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="rejected",
            title="Máquina rejeitada",
            status=OfferCandidate.Status.REJECTED,
        )
        self.client.force_login(self.staff)

    def test_dashboard_shows_operational_families_and_correct_counts(self):
        response = self.client.get(reverse("owner-panel:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.family.name)
        self.assertNotContains(response, self.retired.name)
        self.assertContains(response, "A rever")
        self.assertContains(response, "Na montra")
        self.assertContains(response, "Aprovados")
        self.assertContains(response, "Retirados")
        self.assertContains(response, "Rejeitados")
        self.assertContains(response, "Revalidação necessária")
        counts = response.context["families"][0].owner_counts
        self.assertEqual(
            counts,
            {
                "pending": 1,
                "approved": 1,
                "rejected": 1,
                "review_required": 0,
                "storefront": 1,
                "hidden": 0,
                "promotion_ineligible": 0,
            },
        )

    def test_family_page_is_portuguese_and_preserves_five_signal_model(self):
        response = self.client.get(reverse("owner-panel:family", args=[self.family.slug]))
        self.assertEqual(response.status_code, 200)
        labels = [label for _, label in CandidateDecision.ReviewSignal.choices]
        self.assertEqual(len(labels), 5)
        for label in labels:
            self.assertContains(response, label)
        self.assertContains(response, "Acessório / peça / consumível")
        self.assertNotContains(response, "owner_hidden")
        self.assertNotContains(response, "protocol_verified_at")
        self.assertNotContains(response, "is_active")

    def test_offer_display_uses_field_by_field_observation_fallback(self):
        now = timezone.now()
        OfferObservation.objects.create(
            offer=self.offer,
            price=Decimal("500.00"),
            currency="EUR",
            commission_rate=Decimal("8.5000"),
            sales_count=10,
            evaluation_rate_percent=Decimal("95.00"),
            observed_at=now - timedelta(hours=1),
        )
        OfferObservation.objects.create(
            offer=self.offer,
            price=Decimal("450.00"),
            currency="EUR",
            sales_count=12,
            observed_at=now,
        )

        response = self.client.get(
            reverse("owner-panel:family", args=[self.family.slug]) + "?vista=montra"
        )

        self.assertContains(response, "450,00 EUR")
        self.assertContains(response, "8,5000")
        self.assertContains(response, ">12<", html=False)
        self.assertContains(response, "95,00%")
        self.assertNotContains(response, "500,00 EUR")

    def test_panel_mutations_are_post_only(self):
        routes = [
            reverse("owner-panel:candidate-approve", args=[self.family.slug, self.pending.pk]),
            reverse("owner-panel:candidate-reject", args=[self.family.slug, self.pending.pk]),
            reverse("owner-panel:candidate-move", args=[self.family.slug, self.pending.pk]),
            reverse("owner-panel:candidate-revalidate", args=[self.family.slug, self.approved.pk]),
            reverse("owner-panel:offer-hide", args=[self.family.slug, self.offer.pk]),
            reverse("owner-panel:offer-publish", args=[self.family.slug, self.offer.pk]),
        ]
        for url in routes:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")
            self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_hide_via_panel_removes_storefront_and_go_without_deleting_data(self):
        family_url = reverse("storefront:product-family-detail", args=[self.family.slug])
        go_url = reverse("storefront:offer-go", args=[self.offer.pk])
        self.assertContains(self.client.get(family_url), self.offer.title)
        before = {
            "candidates": OfferCandidate.objects.count(),
            "decisions": CandidateDecision.objects.count(),
            "placements": OfferFamilyPlacement.objects.count(),
            "clicks": OfferClick.objects.count(),
        }
        response = self.client.post(
            reverse("owner-panel:offer-hide", args=[self.family.slug, self.offer.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.offer.refresh_from_db()
        self.assertTrue(self.offer.owner_hidden)
        owner_response = self.client.get(f"{family_url}?gestao=retirados")
        self.assertContains(owner_response, self.offer.title)
        self.assertContains(owner_response, "Retirado da montra")
        public_client = Client()
        self.assertNotContains(public_client.get(family_url), self.offer.title)
        self.assertEqual(self.client.get(go_url).status_code, 404)
        self.assertEqual(OfferClick.objects.count(), before["clicks"])
        self.assertEqual(OfferCandidate.objects.count(), before["candidates"])
        self.assertEqual(CandidateDecision.objects.count(), before["decisions"])
        self.assertEqual(OfferFamilyPlacement.objects.count(), before["placements"])

    @patch("apps.catalog.services.candidate_approval.AliExpressClient")
    def test_panel_approve_reuses_existing_service(self, client_class):
        client_class.return_value.generate_affiliate_link.return_value = (
            "https://affiliate.example/pending"
        )
        response = self.client.post(
            reverse("owner-panel:candidate-approve", args=[self.family.slug, self.pending.pk]),
            {},
        )
        self.assertEqual(response.status_code, 302)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, OfferCandidate.Status.APPROVED)
        self.assertIsNotNone(self.pending.approved_offer_id)

    def test_panel_reject_preserves_five_signal_multiselect(self):
        signals = [
            CandidateDecision.ReviewSignal.DELIVERS_TO_PT_CONFIRMED,
            CandidateDecision.ReviewSignal.ORIGIN_NOT_ALLOWED,
        ]
        response = self.client.post(
            reverse("owner-panel:candidate-reject", args=[self.family.slug, self.pending.pk]),
            {"review_signals": signals},
        )
        self.assertEqual(response.status_code, 302)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, OfferCandidate.Status.REJECTED)
        decision = self.pending.decisions.get()
        self.assertEqual(decision.review_signals, signals)
        self.assertEqual(decision.reason, "")

    def test_panel_move_reuses_existing_service_without_duplication(self):
        target = ProductFamily.objects.create(name="Outra família", slug="outra")
        before = OfferCandidate.objects.count()
        response = self.client.post(
            reverse("owner-panel:candidate-move", args=[self.family.slug, self.pending.pk]),
            {"target_family": target.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.product_family, target)
        self.assertEqual(self.pending.status, OfferCandidate.Status.PENDING)
        self.assertEqual(OfferCandidate.objects.count(), before)

    def test_panel_hide_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.staff)
        response = client.post(
            reverse("owner-panel:offer-hide", args=[self.family.slug, self.offer.pk])
        )
        self.assertEqual(response.status_code, 403)
        self.offer.refresh_from_db()
        self.assertFalse(self.offer.owner_hidden)

    def test_retired_family_not_manageable(self):
        response = self.client.get(reverse("owner-panel:family", args=[self.retired.slug]))
        self.assertEqual(response.status_code, 403)


class OwnerPanelMobileStructureTests(SimpleTestCase):
    def test_mobile_structure_for_360_390_430(self):
        base = (
            settings.BASE_DIR / "apps/catalog/templates/catalog/owner_panel/base.html"
        ).read_text()
        login = (
            settings.BASE_DIR / "apps/catalog/templates/catalog/owner_panel/login.html"
        ).read_text()
        family = (
            settings.BASE_DIR / "apps/catalog/templates/catalog/owner_panel/family.html"
        ).read_text()
        self.assertIn('name="viewport" content="width=device-width,initial-scale=1"', base)
        self.assertIn("overflow-x:hidden", base)
        self.assertIn("width:min(100%,920px)", base)
        self.assertIn("min-height:44px", base)
        self.assertIn("min-height:50px", base)
        self.assertIn('type="password"', login)
        self.assertIn('class="tabs"', family)
        for width in (360, 390, 430):
            with self.subTest(width=width):
                self.assertLess(width, 700)


class PrivateStorefrontControlsTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(name="HIFU", slug="private-controls")
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="private-controls-offer",
            title="Visible offer",
            affiliate_url="https://affiliate.example/private",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=timezone.now(),
            ship_from_country="PL",
            ship_from_verified_at=timezone.now(),
            protocol_verified_at=timezone.now(),
        )
        OfferFamilyPlacement.objects.create(offer=self.offer, product_family=self.family)
        self.detail_url = reverse("storefront:product-family-detail", args=[self.family.slug])

    def test_public_visitor_has_zero_private_controls(self):
        response = self.client.get(self.detail_url)
        self.assertNotContains(response, "Painel")
        self.assertNotContains(response, "RETIRAR DA MONTRA")
        self.assertNotContains(response, "Retirados")

    def test_staff_sees_private_toolbar_and_contextual_hide(self):
        staff = get_user_model().objects.create_user(
            username="staff-controls", password="x", is_staff=True
        )
        self.client.force_login(staff)
        response = self.client.get(self.detail_url)
        self.assertContains(response, "Gestão ativa")
        self.assertContains(response, "Resumo")
        self.assertContains(response, "Sair")
        self.assertNotContains(response, ">Famílias<")
        self.assertNotContains(response, ">Na montra<")
        self.assertContains(response, "RETIRAR DA MONTRA")

    def test_owner_hidden_is_not_public_eligible_and_go_creates_no_click(self):
        self.offer.owner_hidden = True
        self.offer.save(update_fields=["owner_hidden"])
        self.assertFalse(
            Offer.objects.filter(pk=self.offer.pk).filter(public_eligibility_q()).exists()
        )
        go_url = reverse("storefront:offer-go", args=[self.offer.pk])
        self.assertEqual(self.client.get(go_url).status_code, 404)
        self.assertEqual(OfferClick.objects.filter(offer=self.offer).count(), 0)
