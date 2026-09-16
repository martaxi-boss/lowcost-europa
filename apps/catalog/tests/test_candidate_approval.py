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
from apps.catalog.services.public_eligibility import (
    ALLOWED_SHIP_FROM_COUNTRIES,
    is_ship_from_verification_fresh,
)


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

    def test_allowed_countries_approve(self):
        for code in sorted(ALLOWED_SHIP_FROM_COUNTRIES):
            candidate = OfferCandidate.objects.create(
                product_family=self.family,
                source=Offer.Source.ALIEXPRESS,
                external_product_id=f"id-{code}",
                product_url=f"https://example.com/{code}",
            )
            result = approve_candidate(
                candidate,
                ships_to_pt_confirmed=True,
                ship_from_country=code,
                user=self.user,
                client=self.client_api,
            )
            self.assertEqual(result.offer.ship_from_country, code)
            self.assertTrue(is_ship_from_verification_fresh(result.offer))

    def test_cn_blank_unknown_are_blocked(self):
        for code in ("CN", "", "UNKNOWN"):
            with self.assertRaises(CandidateApprovalError):
                approve_candidate(
                    self.candidate,
                    ships_to_pt_confirmed=True,
                    ship_from_country=code,
                    user=self.user,
                    client=self.client_api,
                )

    def test_approval_without_pt_confirmation_is_blocked(self):
        with self.assertRaises(CandidateApprovalError):
            approve_candidate(
                self.candidate,
                ships_to_pt_confirmed=False,
                ship_from_country="PL",
                user=self.user,
                client=self.client_api,
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

    def test_candidate_unique_within_family_source_and_external_id(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OfferCandidate.objects.create(
                    product_family=self.family,
                    source=Offer.Source.ALIEXPRESS,
                    external_product_id=self.candidate.external_product_id,
                )

    def test_invalid_candidate_status_is_blocked(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OfferCandidate.objects.create(
                    product_family=self.family,
                    source=Offer.Source.ALIEXPRESS,
                    external_product_id="invalid-status",
                    status="INVALID",
                )

    def test_decision_records_staff_identity_and_timestamp(self):
        decision = reject_candidate(
            self.candidate,
            user=self.user,
            reason=CandidateDecision.Reason.DUPLICATE,
        )
        self.assertEqual(decision.decided_by, self.user)
        self.assertIsNotNone(decision.decided_at)

    def test_database_blocks_invalid_offer_country(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Offer.objects.create(
                    source=Offer.Source.ALIEXPRESS,
                    external_product_id="bad-country",
                    ship_from_country="CN",
                )

    def test_database_blocks_approve_decision_with_invalid_country(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CandidateDecision.objects.create(
                    candidate=self.candidate,
                    decision="APPROVE",
                    ship_from_country="CN",
                    decided_by=self.user,
                )

    def test_approval_is_atomic_and_creates_offer_observation_placement_decision(self):
        result = approve_candidate(
            self.candidate,
            ships_to_pt_confirmed=True,
            ship_from_country="ES",
            user=self.user,
            client=self.client_api,
        )
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.status, OfferCandidate.Status.APPROVED)
        self.assertEqual(self.candidate.approved_offer_id, result.offer.pk)
        self.assertEqual(result.offer.observations.count(), 1)
        self.assertEqual(result.placement.selection_position, None)
        self.assertEqual(self.candidate.decisions.count(), 1)

    def test_reject_persists_history_and_no_offer(self):
        reject_candidate(
            self.candidate,
            user=self.user,
            reason=CandidateDecision.Reason.ORIGIN_NOT_CONFIRMED,
            note="not clear",
        )
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.status, OfferCandidate.Status.REJECTED)
        self.assertIsNone(self.candidate.approved_offer_id)
        self.assertEqual(
            self.candidate.decisions.get().reason, CandidateDecision.Reason.ORIGIN_NOT_CONFIRMED
        )

    def test_reapproval_refreshes_timestamp_and_preserves_history(self):
        past = timezone.now() - timedelta(days=8)
        result = approve_candidate(
            self.candidate,
            ships_to_pt_confirmed=True,
            ship_from_country="PL",
            user=self.user,
            client=self.client_api,
            now=past,
        )
        self.assertFalse(is_ship_from_verification_fresh(result.offer))
        revalidate_candidate(
            self.candidate,
            user=self.user,
            ship_from_country="DE",
            confirmed=True,
            ships_to_pt_confirmed=True,
            now=timezone.now(),
        )
        self.candidate.refresh_from_db()
        self.candidate.approved_offer.refresh_from_db()
        self.assertTrue(is_ship_from_verification_fresh(self.candidate.approved_offer))
        self.assertEqual(self.candidate.approved_offer.ship_from_country, "DE")
        self.assertEqual(self.candidate.decisions.count(), 2)

    def test_invalid_revalidation_hides_offer_without_deleting_history(self):
        approve_candidate(
            self.candidate,
            ships_to_pt_confirmed=True,
            ship_from_country="FR",
            user=self.user,
            client=self.client_api,
        )
        revalidate_candidate(
            self.candidate,
            user=self.user,
            confirmed=False,
            reason=CandidateDecision.Reason.LISTING_CHANGED,
        )
        self.candidate.refresh_from_db()
        self.candidate.approved_offer.refresh_from_db()
        self.assertIsNone(self.candidate.approved_offer.ship_from_country)
        self.assertEqual(self.candidate.decisions.count(), 2)
        self.assertEqual(Offer.objects.count(), 1)

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
        result = approve_candidate(
            c,
            ships_to_pt_confirmed=True,
            ship_from_country="CZ",
            user=self.user,
            client=self.client_api,
        )
        self.assertEqual(result.offer.pk, legacy.pk)
        self.assertEqual(Offer.objects.filter(external_product_id="legacy").count(), 1)

    def test_21st_fresh_offer_is_blocked_without_partial_records(self):
        now = timezone.now()
        for i in range(20):
            o = Offer.objects.create(
                source=Offer.Source.ALIEXPRESS,
                external_product_id=f"existing-{i}",
                ship_from_country="PL",
                ship_from_verified_at=now,
            )
            OfferFamilyPlacement.objects.create(offer=o, product_family=self.family)
        before = (
            Offer.objects.count(),
            OfferFamilyPlacement.objects.count(),
            CandidateDecision.objects.count(),
        )
        with self.assertRaises(CandidateApprovalError):
            approve_candidate(
                self.candidate,
                ships_to_pt_confirmed=True,
                ship_from_country="PL",
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


class CandidateQueueAccessTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(name="HIFU", slug="hifu")
        self.url = reverse("catalog:candidate-queue", kwargs={"family_slug": "hifu"})
        U = get_user_model()
        self.staff = U.objects.create_user(username="staff", password="x", is_staff=True)
        self.normal = U.objects.create_user(username="normal", password="x", is_staff=False)

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
        c = OfferCandidate.objects.create(
            product_family=self.family, source=Offer.Source.ALIEXPRESS, external_product_id="x"
        )
        self.client.force_login(self.staff)
        for name in ("candidate-approve", "candidate-reject", "candidate-revalidate"):
            url = reverse(f"catalog:{name}", kwargs={"family_slug": "hifu", "candidate_id": c.pk})
            self.assertEqual(self.client.get(url).status_code, 405)

    def test_approve_requires_csrf(self):
        c = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="csrf",
            product_url="https://example.com/csrf",
        )
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.staff)
        url = reverse(
            "catalog:candidate-approve", kwargs={"family_slug": "hifu", "candidate_id": c.pk}
        )
        self.assertEqual(client.post(url, {"ship_from_country": "PL"}).status_code, 403)
