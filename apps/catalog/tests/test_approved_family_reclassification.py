from datetime import timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import (
    CandidateDecision,
    CandidateFamilyMoveEvent,
    Offer,
    OfferCandidate,
    OfferClick,
    OfferEditorialEvent,
    OfferFamilyPlacement,
    OfferObservation,
    ProductFamily,
)
from apps.catalog.services.candidate_learning import family_learning_snapshot
from apps.catalog.services.candidate_move import CandidateMoveError, move_candidate_to_family
from apps.catalog.services.owner_editorial import OwnerEditorialError, publish_offer_to_storefront


class ApprovedFamilyReclassificationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="move-owner", password="x", is_staff=True
        )
        self.nonstaff = get_user_model().objects.create_user(username="plain", password="x")
        self.source = ProductFamily.objects.create(name="Source", slug="move-source")
        self.target = ProductFamily.objects.create(name="Target", slug="move-target")
        self.retired = ProductFamily.objects.create(
            name="Retired", slug="move-retired", status=ProductFamily.Status.RETIRED
        )
        self.verified_at = timezone.now() - timedelta(days=2)
        self.ship_verified_at = timezone.now() - timedelta(days=3)
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="approved-move",
            product_family=self.source,
            title="Approved move machine",
            product_url="https://example.com/product",
            image_url="https://example.com/image.jpg",
            affiliate_url="https://affiliate.example/product",
            ship_from_country="ES",
            ship_from_verified_at=self.ship_verified_at,
            protocol_verified_at=self.verified_at,
            is_active=True,
            owner_hidden=False,
            is_primary=True,
        )
        self.placement = OfferFamilyPlacement.objects.create(
            offer=self.offer,
            product_family=self.source,
            selection_position=1,
            display_order=7,
            selection_reason="Historic editorial selection",
        )
        self.candidate = OfferCandidate.objects.create(
            product_family=self.source,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="approved-move",
            status=OfferCandidate.Status.APPROVED,
            title="Approved move machine",
            approved_offer=self.offer,
        )
        self.approve_decision = CandidateDecision.objects.create(
            candidate=self.candidate,
            decision=CandidateDecision.Decision.APPROVE,
            review_signals=[CandidateDecision.ReviewSignal.DELIVERS_TO_PT_CONFIRMED],
            decided_by=self.user,
        )
        self.observation = OfferObservation.objects.create(
            offer=self.offer,
            destination_country="PT",
            availability=OfferObservation.Availability.UNKNOWN,
        )
        self.click = OfferClick.objects.create(offer=self.offer)
        self.editorial = OfferEditorialEvent.objects.create(
            offer=self.offer,
            action=OfferEditorialEvent.Action.PUBLISH,
            previous_owner_hidden=True,
            new_owner_hidden=False,
            acted_by=self.user,
        )

    def test_approved_move_preserves_offer_approval_protocol_logistics_and_history(self):
        before_decisions = list(self.candidate.decisions.values_list("pk", flat=True))
        before_editorial = list(self.offer.editorial_events.values_list("pk", flat=True))
        moved, changed = move_candidate_to_family(
            self.candidate, target_family=self.target, user=self.user
        )
        moved.refresh_from_db()
        self.offer.refresh_from_db()
        self.assertTrue(changed)
        self.assertEqual(moved.status, OfferCandidate.Status.APPROVED)
        self.assertEqual(moved.product_family, self.target)
        self.assertEqual(moved.approved_offer_id, self.offer.pk)
        self.assertEqual(self.offer.pk, moved.approved_offer.pk)
        self.assertEqual(self.offer.affiliate_url, "https://affiliate.example/product")
        self.assertEqual(self.offer.protocol_verified_at, self.verified_at)
        self.assertEqual(self.offer.ship_from_country, "ES")
        self.assertEqual(self.offer.ship_from_verified_at, self.ship_verified_at)
        self.assertTrue(self.offer.owner_hidden)
        self.assertTrue(self.offer.is_active)
        self.assertEqual(self.offer.product_family, self.target)
        self.assertEqual(list(moved.decisions.values_list("pk", flat=True)), before_decisions)
        self.assertFalse(
            moved.decisions.filter(decision=CandidateDecision.Decision.REJECT).exists()
        )
        self.assertEqual(
            list(self.offer.editorial_events.values_list("pk", flat=True)), before_editorial
        )
        self.assertTrue(OfferObservation.objects.filter(pk=self.observation.pk).exists())
        self.assertTrue(OfferClick.objects.filter(pk=self.click.pk).exists())

    def test_move_event_and_learning_are_classification_only(self):
        move_candidate_to_family(self.candidate, target_family=self.target, user=self.user)
        event = CandidateFamilyMoveEvent.objects.get(candidate=self.candidate)
        self.assertEqual(event.from_family, self.source)
        self.assertEqual(event.to_family, self.target)
        self.assertEqual(event.title_snapshot, self.candidate.title)
        self.assertEqual(event.acted_by, self.user)
        source_learning = family_learning_snapshot(self.source)
        target_learning = family_learning_snapshot(self.target)
        self.assertIn(self.candidate.title, source_learning.classification_negative_titles)
        self.assertIn(self.candidate.title, target_learning.classification_positive_titles)
        self.assertNotIn(self.candidate.title, source_learning.semantic_negative_titles)
        self.assertNotIn(self.candidate.title, source_learning.logistics_negative_titles)

    def test_placement_moves_to_target_once_and_existing_target_is_not_duplicated(self):
        existing = OfferFamilyPlacement.objects.create(
            offer=self.offer, product_family=self.target, selection_position=None, display_order=3
        )
        move_candidate_to_family(self.candidate, target_family=self.target, user=self.user)
        self.assertFalse(
            OfferFamilyPlacement.objects.filter(
                offer=self.offer, product_family=self.source
            ).exists()
        )
        targets = OfferFamilyPlacement.objects.filter(offer=self.offer, product_family=self.target)
        self.assertEqual(targets.count(), 1)
        self.assertEqual(targets.get().pk, existing.pk)

    def test_public_offer_is_hidden_and_not_public_in_source_or_target(self):
        move_candidate_to_family(self.candidate, target_family=self.target, user=self.user)
        self.offer.refresh_from_db()
        self.candidate.refresh_from_db()
        self.assertTrue(self.offer.owner_hidden)
        self.assertEqual(self.candidate.status, OfferCandidate.Status.APPROVED)
        self.assertFalse(
            OfferFamilyPlacement.objects.filter(
                offer=self.offer, product_family=self.source
            ).exists()
        )
        self.assertTrue(
            OfferFamilyPlacement.objects.filter(
                offer=self.offer, product_family=self.target
            ).exists()
        )

    def test_cap20_does_not_block_move_but_publish_still_enforces_cap(self):
        for index in range(20):
            other = Offer.objects.create(
                source=Offer.Source.ALIEXPRESS,
                external_product_id=f"cap-{index}",
                affiliate_url=f"https://affiliate.example/{index}",
                protocol_verified_at=timezone.now(),
                is_active=True,
                owner_hidden=False,
            )
            OfferFamilyPlacement.objects.create(offer=other, product_family=self.target)
        move_candidate_to_family(self.candidate, target_family=self.target, user=self.user)
        self.offer.refresh_from_db()
        self.assertTrue(self.offer.owner_hidden)
        with self.assertRaises(OwnerEditorialError):
            publish_offer_to_storefront(self.offer, family=self.target, user=self.user)
        self.offer.refresh_from_db()
        self.assertTrue(self.offer.owner_hidden)

    def test_inactive_and_stale_are_preserved_without_revalidation(self):
        stale = timezone.now() - timedelta(days=30)
        self.offer.is_primary = False
        self.offer.is_active = False
        self.offer.owner_hidden = True
        self.offer.protocol_verified_at = stale
        self.offer.save(
            update_fields=["is_primary", "is_active", "owner_hidden", "protocol_verified_at"]
        )
        move_candidate_to_family(self.candidate, target_family=self.target, user=self.user)
        self.offer.refresh_from_db()
        self.assertFalse(self.offer.is_active)
        self.assertTrue(self.offer.owner_hidden)
        self.assertEqual(self.offer.protocol_verified_at, stale)

    def test_pending_move_preserves_pending_and_creates_no_decision(self):
        pending = OfferCandidate.objects.create(
            product_family=self.source,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="pending-move",
            title="Pending move",
        )
        moved, _ = move_candidate_to_family(pending, target_family=self.target, user=self.user)
        moved.refresh_from_db()
        self.assertEqual(moved.status, OfferCandidate.Status.PENDING)
        self.assertIsNone(moved.approved_offer_id)
        self.assertEqual(moved.product_family, self.target)
        self.assertFalse(moved.decisions.exists())
        self.assertTrue(CandidateFamilyMoveEvent.objects.filter(candidate=moved).exists())

    def test_invalid_destinations_and_nonstaff_do_not_mutate(self):
        missing = ProductFamily(pk=999999, name="Missing", slug="missing")
        cases = (
            (self.source, self.user),
            (self.retired, self.user),
            (missing, self.user),
            (self.target, self.nonstaff),
        )
        for target, user in cases:
            with self.subTest(target=target.slug, user=user.username):
                before_events = CandidateFamilyMoveEvent.objects.count()
                with self.assertRaises(CandidateMoveError):
                    move_candidate_to_family(self.candidate, target_family=target, user=user)
                self.candidate.refresh_from_db()
                self.offer.refresh_from_db()
                self.assertEqual(self.candidate.product_family, self.source)
                self.assertEqual(self.candidate.status, OfferCandidate.Status.APPROVED)
                self.assertEqual(self.candidate.approved_offer_id, self.offer.pk)
                self.assertFalse(self.offer.owner_hidden)
                self.assertEqual(CandidateFamilyMoveEvent.objects.count(), before_events)


class ApprovedFamilyMoveUITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="move-ui-owner", password="x", is_staff=True
        )
        self.source = ProductFamily.objects.create(name="UI Source", slug="move-ui-source")
        self.target = ProductFamily.objects.create(name="UI Target", slug="move-ui-target")
        self.retired = ProductFamily.objects.create(
            name="UI Retired", slug="move-ui-retired", status=ProductFamily.Status.RETIRED
        )
        now = timezone.now()
        self.pending = OfferCandidate.objects.create(
            product_family=self.source,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="ui-pending",
            title="UI Pending",
        )

        def approved(external_id, *, hidden, verified_at, active=True, hide_event=False):
            offer = Offer.objects.create(
                source=Offer.Source.ALIEXPRESS,
                external_product_id=external_id,
                title=external_id,
                affiliate_url=f"https://affiliate.example/{external_id}",
                protocol_verified_at=verified_at,
                is_active=active,
                owner_hidden=hidden,
            )
            OfferFamilyPlacement.objects.create(offer=offer, product_family=self.source)
            candidate = OfferCandidate.objects.create(
                product_family=self.source,
                source=Offer.Source.ALIEXPRESS,
                external_product_id=external_id,
                title=external_id,
                status=OfferCandidate.Status.APPROVED,
                approved_offer=offer,
            )
            if hide_event:
                OfferEditorialEvent.objects.create(
                    offer=offer,
                    action=OfferEditorialEvent.Action.HIDE,
                    previous_owner_hidden=False,
                    new_owner_hidden=True,
                    acted_by=self.user,
                )
            return candidate, offer

        self.approved, self.approved_offer = approved("ui-approved", hidden=True, verified_at=now)
        self.stale, self.stale_offer = approved(
            "ui-stale", hidden=True, verified_at=now - timedelta(days=30)
        )
        self.retired_candidate, self.retired_offer = approved(
            "ui-retired-offer", hidden=True, verified_at=now, hide_event=True
        )
        self.public_candidate, self.public_offer = approved(
            "ui-public", hidden=False, verified_at=now
        )
        self.client.force_login(self.user)
        self.panel_url = reverse("owner-panel:family", args=[self.source.slug])
        self.storefront_url = reverse("storefront:product-family-detail", args=[self.source.slug])

    def _assert_move_control(self, response, candidate):
        self.assertContains(response, "MUDAR FAMÍLIA")
        self.assertContains(
            response,
            reverse("owner-panel:candidate-move", args=[self.source.slug, candidate.pk]),
        )
        self.assertContains(response, f'value="{self.target.pk}"')
        self.assertNotContains(response, f'value="{self.source.pk}"')
        self.assertNotContains(response, f'value="{self.retired.pk}"')

    def test_owner_panel_move_control_in_rever_aprovados_revalidacao_retirados_montra(self):
        cases = (
            ("rever", self.pending),
            ("aprovados", self.approved),
            ("revalidar", self.stale),
            ("retirados", self.retired_candidate),
            ("montra", self.public_candidate),
        )
        for view, candidate in cases:
            with self.subTest(view=view):
                response = self.client.get(f"{self.panel_url}?vista={view}")
                self._assert_move_control(response, candidate)

    def test_storefront_owner_mode_move_control_in_work_tabs_and_montra(self):
        cases = (
            ("rever", self.pending),
            ("aprovados", self.approved),
            ("revalidar", self.stale),
            ("retirados", self.retired_candidate),
            ("montra", self.public_candidate),
        )
        for tab, candidate in cases:
            with self.subTest(tab=tab):
                response = self.client.get(f"{self.storefront_url}?gestao={tab}")
                self._assert_move_control(response, candidate)

    def test_move_is_post_only_csrf_protected_and_external_next_is_ignored(self):
        url = reverse("owner-panel:candidate-move", args=[self.source.slug, self.pending.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        csrf_client = self.client_class(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        self.assertEqual(
            csrf_client.post(url, {"target_family": self.target.pk}).status_code,
            403,
        )
        response = self.client.post(
            url,
            {"target_family": self.target.pk, "next": "//evil.example/steal"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            f"/painel/familias/{self.target.slug}/?vista=rever",
        )

    def test_valid_next_is_preserved(self):
        url = reverse("owner-panel:candidate-move", args=[self.source.slug, self.pending.pk])
        safe_next = f"{self.storefront_url}?gestao=rever#gestao-owner"
        response = self.client.post(
            url,
            {"target_family": self.target.pk, "next": safe_next},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], safe_next)

    def test_mobile_move_markup_has_responsive_select_and_no_javascript_dependency(self):
        base = (
            Path(__file__).resolve().parents[1] / "templates/catalog/owner_panel/base.html"
        ).read_text()
        storefront_css = (
            Path(__file__).resolve().parents[2] / "storefront/static/storefront/storefront.css"
        ).read_text()
        owner_tools = (
            Path(__file__).resolve().parents[2]
            / "storefront/templates/storefront/components/owner_family_tools.html"
        ).read_text()
        self.assertIn(".move-family-form select", base)
        self.assertIn("max-width:100%", base)
        self.assertIn(".owner-context-move select", storefront_css)
        self.assertIn("max-width:100%", storefront_css)
        self.assertNotIn("<script", owner_tools.lower())
