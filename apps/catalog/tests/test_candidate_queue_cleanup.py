from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import CandidateDecision, Offer, OfferCandidate, ProductFamily
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
        stale_offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="stale-offer",
            protocol_verified_at=timezone.now() - timedelta(days=8),
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
        self.assertContains(response, "Rejected 1")
        self.assertContains(response, "Review required 1")

    def test_one_click_ui_has_no_country_or_pt_question(self):
        response = self.client.get(self.url)
        self.assertContains(response, ">APROVAR<", html=False)
        self.assertContains(response, ">REVALIDAR<", html=False)
        self.assertNotContains(response, 'name="ships_to_pt"')
        self.assertNotContains(response, 'name="ship_from_country" value="PL"')
        self.assertContains(response, "protocolo Lowcost Europa")

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
        response = self.client.post(url, {"reason": CandidateDecision.Reason.IRRELEVANT})
        self.assertRedirects(response, self.url)
        self.assertNotContains(self.client.get(self.url), "pending-id")
        self.assertContains(self.client.get(self.url + "?view=rejected"), "pending-id")

    def test_one_click_approve_endpoint_requires_no_country(self):
        api = __import__("unittest.mock").mock.Mock()
        api.generate_affiliate_link.return_value = "https://affiliate.example/pending"
        result = approve_candidate(self.pending, user=self.staff, client=api)
        result.offer.refresh_from_db()
        self.assertIsNone(result.offer.ship_from_country)
        self.assertIsNotNone(result.offer.protocol_verified_at)


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
        self.assertTrue(moved.decisions.filter(pk=decision_id).exists())

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
