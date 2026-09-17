from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import (
    CandidateDecision,
    CandidateFamilyMoveEvent,
    Offer,
    OfferCandidate,
    ProductFamily,
)
from apps.catalog.services.candidate_approval import approve_candidate, reject_candidate
from apps.catalog.services.candidate_move import move_candidate_to_family


class CandidateQueueFilteringTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(name="HIFU", slug="hifu")
        self.staff = get_user_model().objects.create_user(
            username="staff", password="x", is_staff=True
        )
        self.client.force_login(self.staff)
        self.url = reverse("catalog:candidate-queue", kwargs={"family_slug": "hifu"})
        self.pending = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="pending-id",
            title="Pending HIFU",
            product_url="https://example.com/pending",
        )
        self.rejected = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="rejected-id",
            title="Rejected HIFU",
            status=OfferCandidate.Status.REJECTED,
        )
        fresh_offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="fresh-offer",
            ship_from_country="PL",
            ship_from_verified_at=timezone.now(),
            protocol_verified_at=timezone.now(),
        )
        self.fresh_approved = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="fresh-approved",
            title="Fresh approved HIFU",
            status=OfferCandidate.Status.APPROVED,
            approved_offer=fresh_offer,
        )
        stale_now = timezone.now() - timedelta(days=8)
        stale_offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="stale-offer",
            ship_from_country="PL",
            ship_from_verified_at=stale_now,
            protocol_verified_at=stale_now,
        )
        self.review_required = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="review-required",
            title="Review required HIFU",
            status=OfferCandidate.Status.APPROVED,
            approved_offer=stale_offer,
        )

    def test_default_queue_is_work_only(self):
        response = self.client.get(self.url)
        self.assertContains(response, "pending-id")
        self.assertContains(response, "review-required")
        self.assertNotContains(response, "rejected-id")
        self.assertNotContains(response, "fresh-approved")
        self.assertContains(response, "Rejeitados 1")
        self.assertContains(response, "Revalidação necessária 1")

    def test_approval_ui_is_fixed_attestation_without_shipping_fields(self):
        response = self.client.get(self.url)
        self.assertContains(response, ">APROVAR<", html=False)
        self.assertContains(response, ">REVALIDAR<", html=False)
        self.assertNotContains(response, 'name="delivers_to_pt_confirmed"', html=False)
        self.assertNotContains(response, 'name="ship_from_country"', html=False)

    def test_rejected_approved_and_all_tabs(self):
        rejected = self.client.get(self.url + "?view=rejected")
        approved = self.client.get(self.url + "?view=approved")
        all_items = self.client.get(self.url + "?view=all")
        self.assertContains(rejected, "rejected-id")
        self.assertContains(approved, "fresh-approved")
        self.assertContains(approved, "review-required")
        for external_id in (
            "pending-id",
            "rejected-id",
            "fresh-approved",
            "review-required",
        ):
            self.assertContains(all_items, external_id)

    def test_reject_redirects_to_default_and_candidate_disappears(self):
        url = reverse(
            "catalog:candidate-reject",
            kwargs={"family_slug": "hifu", "candidate_id": self.pending.pk},
        )
        response = self.client.post(
            url,
            {"review_signals": CandidateDecision.ReviewSignal.LISTING_UNAVAILABLE},
        )
        self.assertRedirects(response, self.url)
        self.assertNotContains(self.client.get(self.url), "pending-id")
        self.assertContains(self.client.get(self.url + "?view=rejected"), "pending-id")

    def test_approve_post_needs_no_shipping_fields(self):
        api = __import__("unittest.mock").mock.Mock()
        api.generate_affiliate_link.return_value = "https://affiliate.example/pending"
        result = approve_candidate(self.pending, user=self.staff, client=api)
        result.offer.refresh_from_db()
        self.assertIsNone(result.offer.ship_from_country)
        self.assertIsNone(result.offer.ship_from_verified_at)
        self.assertIsNotNone(result.offer.protocol_verified_at)
        self.assertTrue(result.offer.owner_hidden)


class CandidateMoveTests(TestCase):
    def setUp(self):
        self.hifu = ProductFamily.objects.create(name="HIFU", slug="hifu")
        self.target = ProductFamily.objects.create(name="RF", slug="radiofrequencia-facial")
        self.staff = get_user_model().objects.create_user(
            username="staff", password="x", is_staff=True
        )

    def test_move_preserves_same_candidate_history_and_enters_target_pending(self):
        candidate = OfferCandidate.objects.create(
            product_family=self.hifu,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="move-me",
            status=OfferCandidate.Status.REJECTED,
        )
        reject_candidate(
            candidate,
            user=self.staff,
            reason=CandidateDecision.Reason.WRONG_FAMILY,
        )
        decision_id = candidate.decisions.get().pk
        original_pk = candidate.pk
        moved, changed_family = move_candidate_to_family(
            candidate, target_family=self.target, user=self.staff
        )
        moved.refresh_from_db()
        self.assertTrue(changed_family)
        self.assertEqual(moved.pk, original_pk)
        self.assertEqual(moved.product_family, self.target)
        self.assertEqual(moved.status, OfferCandidate.Status.PENDING)
        self.assertIsNone(moved.approved_offer_id)
        self.assertTrue(moved.decisions.filter(pk=decision_id).exists())
        event = CandidateFamilyMoveEvent.objects.get(candidate=moved)
        self.assertEqual(event.from_family, self.hifu)
        self.assertEqual(event.to_family, self.target)
        self.assertEqual(event.acted_by, self.staff)
        self.assertEqual(event.title_snapshot, candidate.title)

    def test_global_duplicate_candidate_in_other_family_is_blocked(self):
        OfferCandidate.objects.create(
            product_family=self.hifu,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="global-id",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OfferCandidate.objects.create(
                    product_family=self.target,
                    source=Offer.Source.ALIEXPRESS,
                    external_product_id="global-id",
                )

    def test_move_endpoint_is_post_only_and_csrf_protected(self):
        candidate = OfferCandidate.objects.create(
            product_family=self.hifu,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="move-http",
        )
        url = reverse(
            "catalog:candidate-move",
            kwargs={"family_slug": "hifu", "candidate_id": candidate.pk},
        )
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(url).status_code, 405)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.staff)
        self.assertEqual(
            csrf_client.post(url, {"target_family": self.target.pk}).status_code,
            403,
        )


class CandidateRejectionUITests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(name="HIFU UI", slug="hifu-ui")
        self.staff = get_user_model().objects.create_user(
            username="ui-staff", password="x", is_staff=True
        )
        self.candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="ui-reject",
            title="Professional HIFU UI",
            product_url="https://example.com/ui-reject",
        )
        self.client.force_login(self.staff)
        self.queue_url = reverse(
            "catalog:candidate-queue", kwargs={"family_slug": self.family.slug}
        )
        self.reject_url = reverse(
            "catalog:candidate-reject",
            kwargs={"family_slug": self.family.slug, "candidate_id": self.candidate.pk},
        )

    def test_rejection_ui_has_exact_five_portuguese_checkboxes_and_no_legacy_fields(self):
        content = self.client.get(self.queue_url).content.decode()
        labels = [label for _, label in CandidateDecision.ReviewSignal.choices]
        self.assertEqual(content.count('name="review_signals"'), 5)
        reject_panel = content.split('class="panel reject-panel"', 1)[1].split("</form>", 1)[0]
        self.assertEqual(reject_panel.count('type="checkbox"'), 5)
        self.assertNotIn('type="radio"', content)
        for label in labels:
            self.assertIn(label, content)
        self.assertIn('name="note"', content)
        self.assertIn('name="reason"', content)
        self.assertNotIn('name="evidence_url"', content)

    def test_reject_panel_has_one_submit_button_and_mobile_checkbox_css(self):
        content = self.client.get(self.queue_url).content.decode()
        panel = content.split('class="panel reject-panel"', 1)[1].split("</form>", 1)[0]
        self.assertEqual(panel.count('type="submit"'), 1)
        self.assertIn('reject-choice input[type="checkbox"]', content)
        self.assertIn('width:22px', content)
        self.assertIn('min-height:52px', content)
        self.assertIn(':has(input:checked)', content)
        self.assertIn('overflow-x:hidden', content)

    def test_ops_status_text_is_portuguese(self):
        content = self.client.get(self.queue_url).content.decode()
        for translated in ("A rever", "Revalidação necessária", "Aprovados", "Rejeitados"):
            self.assertIn(translated, content)
        for english in ("Pending ", "Review required", "Approved/fresh", "Rejected "):
            self.assertNotIn(english, content)

    def test_multi_select_http_submission_persists_one_decision(self):
        signals = [
            CandidateDecision.ReviewSignal.DELIVERS_TO_PT_CONFIRMED,
            CandidateDecision.ReviewSignal.ORIGIN_NOT_ALLOWED,
        ]
        response = self.client.post(
            self.reject_url,
            {"review_signals": signals, "note": "não encontro envio europeu"},
        )
        self.assertRedirects(response, self.queue_url)
        self.candidate.refresh_from_db()
        decision = self.candidate.decisions.get()
        self.assertEqual(self.candidate.status, OfferCandidate.Status.REJECTED)
        self.assertEqual(decision.review_signals, signals)
        self.assertEqual(decision.reason, "")
        self.assertEqual(decision.note, "não encontro envio europeu")

    def test_semantic_reason_and_note_are_persisted_without_logistics_signal(self):
        response = self.client.post(
            self.reject_url,
            {
                "reason": CandidateDecision.Reason.ACCESSORY_OR_PART,
                "note": "é só a peça da pega",
            },
        )
        self.assertRedirects(response, self.queue_url)
        decision = self.candidate.decisions.get()
        self.assertEqual(decision.reason, CandidateDecision.Reason.ACCESSORY_OR_PART)
        self.assertEqual(decision.note, "é só a peça da pega")
        self.assertEqual(decision.review_signals, [])

    def test_zero_http_signals_shows_simple_error_and_does_not_reject(self):
        response = self.client.post(self.reject_url, {})
        self.assertRedirects(response, self.queue_url, fetch_redirect_response=False)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.status, OfferCandidate.Status.PENDING)
        page = self.client.get(self.queue_url)
        self.assertContains(page, "Selecione pelo menos um sinal ou motivo para rejeitar")

    def test_new_signal_history_is_rendered_in_portuguese_not_codes(self):
        signals = [
            CandidateDecision.ReviewSignal.DELIVERS_TO_PT_CONFIRMED,
            CandidateDecision.ReviewSignal.ORIGIN_NOT_ALLOWED,
        ]
        self.client.post(self.reject_url, {"review_signals": signals})
        page = self.client.get(self.queue_url + "?view=rejected")
        self.assertContains(page, "Rejeitado · Sim, entrega em Portugal")
        self.assertContains(page, "País de envio fora dos cinco permitidos")
        self.assertNotContains(page, "DELIVERS_TO_PT_CONFIRMED")
        self.assertNotContains(page, "ORIGIN_NOT_ALLOWED")

    def test_legacy_reason_history_remains_human_readable(self):
        reject_candidate(
            self.candidate,
            user=self.staff,
            reason=CandidateDecision.Reason.WRONG_FAMILY,
        )
        page = self.client.get(self.queue_url + "?view=rejected")
        self.assertContains(page, "Produto pertence a outra família")
        self.assertNotContains(page, "WRONG_FAMILY")
