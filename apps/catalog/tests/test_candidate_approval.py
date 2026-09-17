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

    def approve(self, candidate=None, country="ES", now=None):
        return approve_candidate(
            candidate or self.candidate,
            user=self.user,
            delivers_to_pt_confirmed=True,
            ship_from_country=country,
            client=self.client_api,
            now=now,
        )

    def test_allowed_countries_pass_and_persist_protocol(self):
        for index, country in enumerate(("PL", "CZ", "FR", "ES", "DE")):
            candidate = OfferCandidate.objects.create(
                product_family=self.family,
                source=Offer.Source.ALIEXPRESS,
                external_product_id=f"allowed-{index}",
                title=f"Allowed {country}",
                product_url=f"https://example.com/{index}",
            )
            result = self.approve(candidate, country=country)
            self.assertEqual(result.offer.ship_from_country, country)
            self.assertIsNotNone(result.offer.ship_from_verified_at)
            self.assertIsNotNone(result.offer.protocol_verified_at)
            self.assertTrue(result.offer.owner_hidden)
            self.assertEqual(result.decision.ship_from_country, country)
            self.assertIn(
                CandidateDecision.ReviewSignal.DELIVERS_TO_PT_CONFIRMED,
                result.decision.review_signals,
            )

    def test_unknown_disallowed_and_missing_pt_are_blocked(self):
        for country in ("", "CN", "UK", "IT", "US", "NL", "BE"):
            with self.subTest(country=country):
                with self.assertRaises(CandidateApprovalError):
                    approve_candidate(
                        self.candidate,
                        user=self.user,
                        delivers_to_pt_confirmed=True,
                        ship_from_country=country,
                        client=self.client_api,
                    )
        with self.assertRaises(CandidateApprovalError):
            approve_candidate(
                self.candidate,
                user=self.user,
                delivers_to_pt_confirmed=False,
                ship_from_country="ES",
                client=self.client_api,
            )
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.status, OfferCandidate.Status.PENDING)

    def test_approval_creates_hidden_offer_observation_placement_and_history(self):
        result = self.approve()
        self.candidate.refresh_from_db()
        self.assertEqual(result.offer.affiliate_url, "https://affiliate.example/1")
        self.assertTrue(result.offer.owner_hidden)
        self.assertEqual(self.candidate.status, OfferCandidate.Status.APPROVED)
        self.assertEqual(self.candidate.approved_offer_id, result.offer.pk)
        self.assertEqual(result.offer.observations.count(), 1)
        self.assertIsNone(result.placement.selection_position)
        self.assertEqual(self.candidate.decisions.count(), 1)
        self.assertFalse(is_protocol_verification_fresh(result.offer) is False)

    def test_candidate_and_offer_identities_are_global(self):
        other = ProductFamily.objects.create(name="RF", slug="rf")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OfferCandidate.objects.create(
                    product_family=other,
                    source=Offer.Source.ALIEXPRESS,
                    external_product_id=self.candidate.external_product_id,
                )
        Offer.objects.create(source=Offer.Source.ALIEXPRESS, external_product_id="same")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Offer.objects.create(source=Offer.Source.ALIEXPRESS, external_product_id="same")

    def test_existing_offer_is_reused_and_owner_hidden_is_never_cleared(self):
        legacy = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="legacy",
            affiliate_url="https://affiliate.example/legacy",
            owner_hidden=True,
        )
        candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="legacy",
            approved_offer=legacy,
            product_url="https://example.com/legacy",
        )
        result = self.approve(candidate, country="PL")
        self.assertEqual(result.offer.pk, legacy.pk)
        result.offer.refresh_from_db()
        self.assertTrue(result.offer.owner_hidden)
        self.assertEqual(Offer.objects.filter(external_product_id="legacy").count(), 1)

    def test_21st_candidate_can_be_approved_but_stays_hidden(self):
        now = timezone.now()
        for i in range(20):
            offer = Offer.objects.create(
                source=Offer.Source.ALIEXPRESS,
                external_product_id=f"existing-{i}",
                affiliate_url=f"https://affiliate.example/{i}",
                ship_from_country="PL",
                ship_from_verified_at=now,
                protocol_verified_at=now,
                owner_hidden=False,
            )
            OfferFamilyPlacement.objects.create(offer=offer, product_family=self.family)
        result = self.approve(now=now)
        self.assertTrue(result.offer.owner_hidden)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.status, OfferCandidate.Status.APPROVED)

    def test_revalidation_requires_and_refreshes_complete_protocol(self):
        now = timezone.now()
        result = self.approve(country="PL", now=now - timedelta(days=8))
        with self.assertRaises(CandidateApprovalError):
            revalidate_candidate(result.candidate, user=self.user, ship_from_country="ES", now=now)
        decision = revalidate_candidate(
            result.candidate,
            user=self.user,
            delivers_to_pt_confirmed=True,
            ship_from_country="ES",
            now=now,
        )
        result.offer.refresh_from_db()
        self.assertEqual(result.offer.ship_from_country, "ES")
        self.assertEqual(result.offer.ship_from_verified_at, now)
        self.assertEqual(result.offer.protocol_verified_at, now)
        self.assertEqual(decision.ship_from_country, "ES")
        self.assertIn(
            CandidateDecision.ReviewSignal.DELIVERS_TO_PT_CONFIRMED,
            decision.review_signals,
        )

    def test_reject_preserves_country_history_but_invalidates_protocol(self):
        result = self.approve(country="PL")
        reject_candidate(
            self.candidate,
            user=self.user,
            reason=CandidateDecision.Reason.LISTING_CHANGED,
        )
        result.offer.refresh_from_db()
        self.assertEqual(result.offer.ship_from_country, "PL")
        self.assertIsNotNone(result.offer.ship_from_verified_at)
        self.assertIsNone(result.offer.protocol_verified_at)


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
