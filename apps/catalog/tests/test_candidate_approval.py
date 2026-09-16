from datetime import timedelta
from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import (
    CandidateDecision,
    Offer,
    OfferCandidate,
    OfferFamilyPlacement,
    ProductFamily,
)
from apps.catalog.services.candidate_approval import (
    CandidateApprovalError,
    approve_candidate,
    reject_candidate,
    revalidate_candidate,
)
from apps.catalog.services.public_eligibility import is_protocol_verification_fresh


class CandidateApprovalTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(name="HIFU", slug="hifu")
        self.user = get_user_model().objects.create_user(
            username="staff", password="x", is_staff=True
        )
        self.candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="new-1",
            title="Professional HIFU",
            image_url="https://img.example/1.jpg",
            product_url="https://www.aliexpress.com/item/1.html",
            price="100.00",
            currency="EUR",
        )
        self.client_api = Mock()
        self.client_api.generate_affiliate_link.return_value = "https://affiliate.example/1"

    def test_one_click_approve_sets_protocol_without_inventing_country(self):
        result = approve_candidate(self.candidate, user=self.user, client=self.client_api)
        result.offer.refresh_from_db()
        self.assertIsNotNone(result.offer.protocol_verified_at)
        self.assertIsNone(result.offer.ship_from_country)
        self.assertIsNone(result.offer.ship_from_verified_at)
        self.assertEqual(result.decision.ship_from_country, "")
        self.assertTrue(is_protocol_verification_fresh(result.offer))

    def test_approval_creates_affiliate_observation_placement_and_history(self):
        result = approve_candidate(self.candidate, user=self.user, client=self.client_api)
        self.candidate.refresh_from_db()
        self.assertEqual(result.offer.affiliate_url, "https://affiliate.example/1")
        self.assertEqual(self.candidate.status, OfferCandidate.Status.APPROVED)
        self.assertEqual(self.candidate.approved_offer_id, result.offer.pk)
        self.assertEqual(result.offer.observations.count(), 1)
        self.assertIsNone(result.placement.selection_position)
        self.assertEqual(self.candidate.decisions.count(), 1)

    def test_candidate_identity_is_global_across_families(self):
        other = ProductFamily.objects.create(name="RF", slug="rf")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OfferCandidate.objects.create(
                    product_family=other,
                    source=Offer.Source.ALIEXPRESS,
                    external_product_id=self.candidate.external_product_id,
                )

    def test_offer_identity_is_global(self):
        Offer.objects.create(source=Offer.Source.ALIEXPRESS, external_product_id="same")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Offer.objects.create(source=Offer.Source.ALIEXPRESS, external_product_id="same")

    def test_candidate_and_linked_offer_can_coexist(self):
        result = approve_candidate(self.candidate, user=self.user, client=self.client_api)
        self.assertEqual(OfferCandidate.objects.filter(external_product_id="new-1").count(), 1)
        self.assertEqual(Offer.objects.filter(external_product_id="new-1").count(), 1)
        self.assertEqual(result.candidate.approved_offer_id, result.offer.pk)

    def test_database_allows_blank_country_for_approve_decision(self):
        decision = CandidateDecision.objects.create(
            candidate=self.candidate,
            decision=CandidateDecision.Decision.APPROVE,
            ship_from_country="",
            decided_by=self.user,
        )
        self.assertEqual(decision.ship_from_country, "")

    def test_database_blocks_invalid_country_if_approve_decision_records_one(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CandidateDecision.objects.create(
                    candidate=self.candidate,
                    decision=CandidateDecision.Decision.APPROVE,
                    ship_from_country="CN",
                    decided_by=self.user,
                )

    def test_other_rejection_requires_note(self):
        with self.assertRaises(CandidateApprovalError):
            reject_candidate(self.candidate, user=self.user, reason=CandidateDecision.Reason.OTHER)
        decision = reject_candidate(
            self.candidate,
            user=self.user,
            reason=CandidateDecision.Reason.OTHER,
            note="Razão específica",
        )
        self.assertEqual(decision.note, "Razão específica")

    def test_reject_preserves_country_history_but_invalidates_protocol(self):
        legacy = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="legacy-country",
            ship_from_country="PL",
            ship_from_verified_at=timezone.now() - timedelta(days=2),
            protocol_verified_at=timezone.now(),
        )
        self.candidate.approved_offer = legacy
        self.candidate.status = OfferCandidate.Status.APPROVED
        self.candidate.save(update_fields=["approved_offer", "status", "updated_at"])
        reject_candidate(
            self.candidate,
            user=self.user,
            reason=CandidateDecision.Reason.LISTING_CHANGED,
        )
        legacy.refresh_from_db()
        self.assertEqual(legacy.ship_from_country, "PL")
        self.assertIsNotNone(legacy.ship_from_verified_at)
        self.assertIsNone(legacy.protocol_verified_at)

    def test_one_click_revalidate_only_renews_protocol_and_preserves_country(self):
        old_protocol = timezone.now() - timedelta(days=8)
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="revalidate",
            ship_from_country="ES",
            ship_from_verified_at=timezone.now() - timedelta(days=30),
            protocol_verified_at=old_protocol,
        )
        self.candidate.approved_offer = offer
        self.candidate.status = OfferCandidate.Status.APPROVED
        self.candidate.save(update_fields=["approved_offer", "status", "updated_at"])
        now = timezone.now()
        revalidate_candidate(self.candidate, user=self.user, now=now)
        offer.refresh_from_db()
        self.assertEqual(offer.protocol_verified_at, now)
        self.assertEqual(offer.ship_from_country, "ES")
        self.assertNotEqual(offer.ship_from_verified_at, now)
        self.assertEqual(self.candidate.decisions.count(), 1)

    def test_legacy_offer_is_reused_not_duplicated(self):
        legacy = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="legacy",
            affiliate_url="https://affiliate.example/legacy",
        )
        c = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="legacy",
            approved_offer=legacy,
            product_url="https://example.com/legacy",
        )
        result = approve_candidate(c, user=self.user, client=self.client_api)
        self.assertEqual(result.offer.pk, legacy.pk)
        self.assertEqual(Offer.objects.filter(external_product_id="legacy").count(), 1)

    def test_21st_fresh_offer_is_blocked_without_partial_records(self):
        now = timezone.now()
        for i in range(20):
            offer = Offer.objects.create(
                source=Offer.Source.ALIEXPRESS,
                external_product_id=f"existing-{i}",
                protocol_verified_at=now,
            )
            OfferFamilyPlacement.objects.create(offer=offer, product_family=self.family)
        before = (
            Offer.objects.count(),
            OfferFamilyPlacement.objects.count(),
            CandidateDecision.objects.count(),
        )
        with self.assertRaises(CandidateApprovalError):
            approve_candidate(
                self.candidate,
                user=self.user,
                client=self.client_api,
                now=now,
            )
        self.assertEqual(
            (
                Offer.objects.count(),
                OfferFamilyPlacement.objects.count(),
                CandidateDecision.objects.count(),
            ),
            before,
        )
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.status, OfferCandidate.Status.PENDING)


class CandidateRejectionSignalTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(name="HIFU", slug="hifu-signals")
        self.user = get_user_model().objects.create_user(
            username="signal-staff", password="x", is_staff=True
        )
        self.candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="signal-candidate",
            title="Professional HIFU machine",
        )

    def reject(self, signals):
        return reject_candidate(self.candidate, user=self.user, review_signals=signals)

    def test_zero_signals_is_blocked_without_rejecting_candidate(self):
        with self.assertRaises(CandidateApprovalError):
            self.reject([])
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.status, OfferCandidate.Status.PENDING)
        self.assertEqual(self.candidate.decisions.count(), 0)

    def test_each_signal_can_be_persisted_individually(self):
        for index, signal in enumerate(CandidateDecision.ReviewSignal.values):
            candidate = OfferCandidate.objects.create(
                product_family=self.family,
                source=Offer.Source.ALIEXPRESS,
                external_product_id=f"single-{index}",
            )
            decision = reject_candidate(candidate, user=self.user, review_signals=[signal])
            self.assertEqual(decision.review_signals, [signal])
            self.assertEqual(decision.reason, "")

    def test_two_signals_are_persisted_in_one_decision(self):
        signals = [
            CandidateDecision.ReviewSignal.DELIVERS_TO_PT_CONFIRMED,
            CandidateDecision.ReviewSignal.ORIGIN_NOT_ALLOWED,
        ]
        decision = self.reject(signals)
        self.assertEqual(decision.review_signals, signals)
        self.assertEqual(self.candidate.decisions.count(), 1)

    def test_all_five_signals_are_persisted_in_one_decision(self):
        decision = self.reject(list(CandidateDecision.ReviewSignal.values))
        self.assertEqual(decision.review_signals, list(CandidateDecision.ReviewSignal.values))
        self.assertEqual(self.candidate.decisions.count(), 1)

    def test_duplicate_signal_is_stored_once(self):
        signal = CandidateDecision.ReviewSignal.LISTING_UNAVAILABLE
        decision = self.reject([signal, signal])
        self.assertEqual(decision.review_signals, [signal])

    def test_unknown_signal_is_rejected_server_side(self):
        with self.assertRaises(CandidateApprovalError):
            self.reject(["UNKNOWN_SIGNAL"])
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.status, OfferCandidate.Status.PENDING)
        self.assertEqual(self.candidate.decisions.count(), 0)

    def test_rejection_sets_candidate_rejected(self):
        self.reject([CandidateDecision.ReviewSignal.DELIVERS_TO_PT_CONFIRMED])
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.status, OfferCandidate.Status.REJECTED)

    def test_legacy_reason_history_is_preserved(self):
        decision = reject_candidate(
            self.candidate,
            user=self.user,
            reason=CandidateDecision.Reason.WRONG_FAMILY,
        )
        self.assertEqual(decision.reason, CandidateDecision.Reason.WRONG_FAMILY)
        self.assertEqual(decision.review_signals, [])


class CandidateQueueAccessTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(name="HIFU", slug="hifu")
        self.url = reverse("catalog:candidate-queue", kwargs={"family_slug": "hifu"})
        users = get_user_model()
        self.staff = users.objects.create_user(username="staff", password="x", is_staff=True)
        self.normal = users.objects.create_user(username="normal", password="x", is_staff=False)

    def test_anonymous_and_nonstaff_denied_staff_allowed(self):
        self.assertNotEqual(self.client.get(self.url).status_code, 200)
        self.client.force_login(self.normal)
        self.assertNotEqual(self.client.get(self.url).status_code, 200)
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")
        self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_actions_are_post_only(self):
        candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="x",
        )
        self.client.force_login(self.staff)
        for name in ("candidate-approve", "candidate-reject", "candidate-revalidate"):
            url = reverse(
                f"catalog:{name}",
                kwargs={"family_slug": "hifu", "candidate_id": candidate.pk},
            )
            self.assertEqual(self.client.get(url).status_code, 405)

    def test_approve_requires_csrf(self):
        candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="csrf",
            product_url="https://example.com/csrf",
        )
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.staff)
        url = reverse(
            "catalog:candidate-approve",
            kwargs={"family_slug": "hifu", "candidate_id": candidate.pk},
        )
        self.assertEqual(client.post(url).status_code, 403)
