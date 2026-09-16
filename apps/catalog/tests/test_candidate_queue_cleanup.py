from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import CandidateDecision, Offer, OfferCandidate, ProductFamily
from apps.catalog.services.candidate_approval import reject_candidate
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
            ship_from_country="ES",
            ship_from_verified_at=timezone.now() - timedelta(days=8),
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

    def test_rejected_tab_shows_rejected(self):
        response = self.client.get(self.url + "?view=rejected")
        self.assertContains(response, "rejected-id")
        self.assertNotContains(response, "pending-id")

    def test_approved_tab_shows_approved(self):
        response = self.client.get(self.url + "?view=approved")
        self.assertContains(response, "fresh-approved")
        self.assertContains(response, "review-required")
        self.assertNotContains(response, "rejected-id")

    def test_all_tab_shows_everything(self):
        response = self.client.get(self.url + "?view=all")
        for external_id in (
            "pending-id",
            "rejected-id",
            "fresh-approved",
            "review-required",
        ):
            self.assertContains(response, external_id)

    def test_reject_redirects_to_default_and_candidate_disappears(self):
        url = reverse(
            "catalog:candidate-reject",
            kwargs={"family_slug": "hifu", "candidate_id": self.pending.pk},
        )
        response = self.client.post(url, {"reason": CandidateDecision.Reason.IRRELEVANT})
        self.assertRedirects(response, self.url)
        self.assertNotContains(self.client.get(self.url), "pending-id")
        self.assertContains(self.client.get(self.url + "?view=rejected"), "pending-id")


class CandidateMoveTests(TestCase):
    def setUp(self):
        self.hifu = ProductFamily.objects.create(name="HIFU", slug="hifu")
        self.target = ProductFamily.objects.create(name="RF", slug="radiofrequencia-facial")
        self.staff = get_user_model().objects.create_user(
            username="staff", password="x", is_staff=True
        )

    def test_move_preserves_history_and_enters_target_pending(self):
        candidate = OfferCandidate.objects.create(
            product_family=self.hifu,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="move-me",
            status=OfferCandidate.Status.REJECTED,
        )
        reject_candidate(
            candidate,
            user=self.staff,
            reason=CandidateDecision.Reason.IRRELEVANT,
        )
        decision_id = candidate.decisions.get().pk
        moved, changed_family = move_candidate_to_family(
            candidate, target_family=self.target, user=self.staff
        )
        moved.refresh_from_db()
        self.assertTrue(changed_family)
        self.assertEqual(moved.product_family, self.target)
        self.assertEqual(moved.status, OfferCandidate.Status.PENDING)
        self.assertIsNone(moved.approved_offer_id)
        self.assertTrue(moved.decisions.filter(pk=decision_id).exists())

    def test_duplicate_destination_candidate_is_reused_without_auto_approval(self):
        source = OfferCandidate.objects.create(
            product_family=self.hifu,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="duplicate-move",
            status=OfferCandidate.Status.REJECTED,
            title="Newer snapshot",
        )
        destination = OfferCandidate.objects.create(
            product_family=self.target,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="duplicate-move",
            status=OfferCandidate.Status.REJECTED,
            title="Old snapshot",
        )
        moved, changed_family = move_candidate_to_family(
            source, target_family=self.target, user=self.staff
        )
        moved.refresh_from_db()
        self.assertFalse(changed_family)
        self.assertEqual(moved.pk, destination.pk)
        self.assertEqual(moved.status, OfferCandidate.Status.PENDING)
        self.assertEqual(moved.title, "Newer snapshot")
        self.assertEqual(
            OfferCandidate.objects.filter(
                product_family=self.target,
                source=Offer.Source.ALIEXPRESS,
                external_product_id="duplicate-move",
            ).count(),
            1,
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
