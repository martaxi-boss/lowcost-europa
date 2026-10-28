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
    OfferObservation,
    ProductFamily,
)
from apps.catalog.services.candidate_approval import (
    CandidateApprovalError,
    approve_candidate,
    reject_candidate,
    revalidate_candidate,
)
from apps.catalog.services.public_eligibility import is_protocol_verified
from apps.integrations.aliexpress.exceptions import AliExpressAPIError, AliExpressTransportError


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

    def approve(self, candidate=None, now=None):
        return approve_candidate(
            candidate or self.candidate,
            user=self.user,
            client=self.client_api,
            now=now,
        )

    def test_approval_requires_no_country_and_records_composite_protocol_attestation(self):
        now = timezone.now()
        result = self.approve(now=now)

        self.candidate.refresh_from_db()
        result.offer.refresh_from_db()
        self.assertEqual(self.candidate.status, OfferCandidate.Status.APPROVED)
        self.assertEqual(result.offer.protocol_verified_at, now)
        self.assertIsNone(result.offer.ship_from_country)
        self.assertIsNone(result.offer.ship_from_verified_at)
        self.assertEqual(result.decision.ship_from_country, "")
        self.assertEqual(result.decision.review_signals, [])
        self.client_api.generate_affiliate_link.assert_not_called()

    def test_approval_preserves_independently_known_exact_country_metadata(self):
        historical = timezone.now() - timedelta(days=30)
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="known-country",
            ship_from_country="ES",
            ship_from_verified_at=historical,
            owner_hidden=True,
        )
        candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id=offer.external_product_id,
            product_url="https://www.aliexpress.com/item/known-country.html",
        )
        result = self.approve(candidate, now=timezone.now())
        result.offer.refresh_from_db()
        self.assertEqual(result.offer.ship_from_country, "ES")
        self.assertEqual(result.offer.ship_from_verified_at, historical)

    def test_approval_creates_hidden_offer_observation_placement_and_history(self):
        result = self.approve()
        self.candidate.refresh_from_db()
        self.assertEqual(result.offer.affiliate_url, "")
        self.assertEqual(
            result.offer.affiliate_promotion_status,
            Offer.AffiliatePromotionStatus.UNKNOWN,
        )
        self.assertIsNone(result.offer.affiliate_promotion_verified_at)
        self.assertTrue(result.offer.owner_hidden)
        self.assertEqual(self.candidate.status, OfferCandidate.Status.APPROVED)
        self.assertEqual(self.candidate.approved_offer_id, result.offer.pk)
        self.assertEqual(result.offer.observations.count(), 1)
        self.assertIsNone(result.placement.selection_position)
        self.assertEqual(self.candidate.decisions.count(), 1)
        self.assertTrue(is_protocol_verified(result.offer))

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

    def test_existing_offer_approval_preserves_factual_country_and_hidden_state(self):
        verified_at = timezone.now() - timedelta(days=2)
        legacy = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="legacy",
            affiliate_url="https://affiliate.example/legacy",
            ship_from_country="PL",
            ship_from_verified_at=verified_at,
            owner_hidden=True,
        )
        candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="legacy",
            approved_offer=legacy,
            product_url="https://example.com/legacy",
        )
        now = timezone.now()
        result = self.approve(candidate, now=now)
        result.offer.refresh_from_db()
        self.assertEqual(result.offer.pk, legacy.pk)
        self.assertTrue(result.offer.owner_hidden)
        self.assertEqual(result.offer.ship_from_country, "PL")
        self.assertEqual(result.offer.ship_from_verified_at, verified_at)
        self.assertEqual(result.offer.protocol_verified_at, now)

    def test_existing_published_offer_keeps_its_link_when_approved_in_another_family(self):
        old_url = "https://affiliate.example/old"
        verified_at = timezone.now() - timedelta(days=1)
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="existing-old-link",
            affiliate_url=old_url,
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=verified_at,
            owner_hidden=False,
        )
        candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id=offer.external_product_id,
            product_url="https://www.aliexpress.com/item/200.html",
        )
        result = self.approve(candidate)
        result.offer.refresh_from_db()
        self.client_api.generate_affiliate_link.assert_not_called()
        self.assertEqual(result.offer.affiliate_url, old_url)
        self.assertEqual(result.offer.affiliate_promotion_verified_at, verified_at)
        self.assertFalse(result.offer.owner_hidden)

    def test_existing_eligible_hidden_offer_keeps_verified_link_at_approval(self):
        url = "https://affiliate.example/already-valid"
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="existing-eligible",
            affiliate_url=url,
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=timezone.now(),
            owner_hidden=True,
        )
        candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id=offer.external_product_id,
            product_url="https://www.aliexpress.com/item/201.html",
        )
        self.approve(candidate)
        offer.refresh_from_db()
        self.client_api.generate_affiliate_link.assert_not_called()
        self.assertEqual(offer.affiliate_url, url)
        self.assertTrue(offer.owner_hidden)

    def test_existing_unknown_and_ineligible_are_not_silently_promoted_on_approval(self):
        for index, status in enumerate(
            (Offer.AffiliatePromotionStatus.UNKNOWN, Offer.AffiliatePromotionStatus.INELIGIBLE)
        ):
            with self.subTest(status=status):
                old = f"https://affiliate.example/status-old-{index}"
                verified_at = timezone.now() - timedelta(days=2)
                offer = Offer.objects.create(
                    source=Offer.Source.ALIEXPRESS,
                    external_product_id=f"existing-status-{index}",
                    affiliate_url=old,
                    affiliate_promotion_status=status,
                    affiliate_promotion_verified_at=verified_at,
                    owner_hidden=True,
                )
                candidate = OfferCandidate.objects.create(
                    product_family=self.family,
                    source=Offer.Source.ALIEXPRESS,
                    external_product_id=offer.external_product_id,
                    product_url=f"https://www.aliexpress.com/item/{300 + index}.html",
                )
                api = Mock()
                approve_candidate(candidate, user=self.user, client=api)
                offer.refresh_from_db()
                api.generate_affiliate_link.assert_not_called()
                self.assertEqual(offer.affiliate_url, old)
                self.assertEqual(offer.affiliate_promotion_status, status)
                self.assertEqual(offer.affiliate_promotion_verified_at, verified_at)
                self.assertTrue(offer.owner_hidden)

    def test_approval_does_not_contact_affiliate_api_or_change_existing_history(self):
        old_url = "https://affiliate.example/original"
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="failure-existing",
            affiliate_url=old_url,
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=timezone.now() - timedelta(days=3),
            owner_hidden=True,
        )
        OfferObservation.objects.create(offer=offer, price="99.00", currency="EUR")
        candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id=offer.external_product_id,
            product_url="https://www.aliexpress.com/item/400.html",
        )
        api = Mock()
        api.generate_affiliate_link.side_effect = AliExpressTransportError("temporary")
        result = approve_candidate(candidate, user=self.user, client=api)
        api.generate_affiliate_link.assert_not_called()
        offer.refresh_from_db()
        self.assertEqual(result.candidate.status, OfferCandidate.Status.APPROVED)
        self.assertEqual(offer.affiliate_url, old_url)
        self.assertTrue(offer.owner_hidden)
        self.assertEqual(offer.observations.count(), 2)
        self.assertEqual(candidate.decisions.count(), 1)

    def test_explicitly_ineligible_offer_stays_ineligible_after_approval(self):
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="not-promotable",
            affiliate_url="https://affiliate.example/old-not-promotable",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.INELIGIBLE,
            affiliate_promotion_verified_at=timezone.now(),
            owner_hidden=True,
        )
        candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id=offer.external_product_id,
            product_url="https://www.aliexpress.com/item/401.html",
        )
        api = Mock()
        api.generate_affiliate_link.side_effect = AliExpressAPIError("not promotable")
        result = approve_candidate(candidate, user=self.user, client=api)
        api.generate_affiliate_link.assert_not_called()
        offer.refresh_from_db()
        self.assertEqual(result.candidate.status, OfferCandidate.Status.APPROVED)
        self.assertEqual(
            offer.affiliate_promotion_status, Offer.AffiliatePromotionStatus.INELIGIBLE
        )
        self.assertTrue(offer.owner_hidden)

    def test_non_pending_candidate_cannot_be_approved_or_generate_link(self):
        for index, status in enumerate(
            (OfferCandidate.Status.APPROVED, OfferCandidate.Status.REJECTED)
        ):
            with self.subTest(status=status):
                candidate = OfferCandidate.objects.create(
                    product_family=self.family,
                    source=Offer.Source.ALIEXPRESS,
                    external_product_id=f"non-pending-{index}",
                    product_url=f"https://www.aliexpress.com/item/{500 + index}.html",
                    status=status,
                )
                api = Mock()

                with self.assertRaises(CandidateApprovalError):
                    approve_candidate(candidate, user=self.user, client=api)

                api.generate_affiliate_link.assert_not_called()

    def test_21st_candidate_can_be_approved_but_stays_hidden(self):
        now = timezone.now()
        for i in range(20):
            offer = Offer.objects.create(
                source=Offer.Source.ALIEXPRESS,
                external_product_id=f"existing-{i}",
                affiliate_url=f"https://affiliate.example/{i}",
                protocol_verified_at=now,
                owner_hidden=False,
            )
            OfferFamilyPlacement.objects.create(offer=offer, product_family=self.family)
        result = self.approve(now=now)
        self.assertTrue(result.offer.owner_hidden)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.status, OfferCandidate.Status.APPROVED)

    def test_revalidation_refreshes_attestation_without_inventing_country(self):
        historical = timezone.now() - timedelta(days=30)
        result = self.approve(now=timezone.now() - timedelta(days=8))
        result.offer.ship_from_country = "ES"
        result.offer.ship_from_verified_at = historical
        result.offer.save(update_fields=["ship_from_country", "ship_from_verified_at"])
        now = timezone.now()
        decision = revalidate_candidate(result.candidate, user=self.user, now=now)
        result.offer.refresh_from_db()
        self.assertEqual(result.offer.ship_from_country, "ES")
        self.assertEqual(result.offer.ship_from_verified_at, historical)
        self.assertEqual(result.offer.protocol_verified_at, now)
        self.assertEqual(decision.ship_from_country, "")

    def test_reject_preserves_country_history_but_invalidates_protocol(self):
        result = self.approve()
        result.offer.ship_from_country = "PL"
        result.offer.ship_from_verified_at = timezone.now()
        result.offer.save(update_fields=["ship_from_country", "ship_from_verified_at"])
        reject_candidate(
            self.candidate, user=self.user, reason=CandidateDecision.Reason.LISTING_CHANGED
        )
        result.offer.refresh_from_db()
        self.assertEqual(result.offer.ship_from_country, "PL")
        self.assertIsNotNone(result.offer.ship_from_verified_at)
        self.assertIsNone(result.offer.protocol_verified_at)


class CandidateRejectionReasonTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(name="HIFU", slug="hifu-signals")
        self.user = get_user_model().objects.create_user(
            username="reason-staff", password="x", is_staff=True
        )
        self.candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="reason-candidate",
            title="Professional HIFU machine",
        )

    def test_rejection_requires_one_primary_reason(self):
        with self.assertRaises(CandidateApprovalError):
            reject_candidate(self.candidate, user=self.user)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.status, OfferCandidate.Status.PENDING)
        self.assertEqual(self.candidate.decisions.count(), 0)

    def test_every_owner_reason_can_be_persisted(self):
        for index, reason in enumerate(
            value
            for value in CandidateDecision.Reason.values
            if value != CandidateDecision.Reason.IRRELEVANT
        ):
            candidate = OfferCandidate.objects.create(
                product_family=self.family,
                source=Offer.Source.ALIEXPRESS,
                external_product_id=f"reason-{index}",
            )
            note = "Detalhe adicional" if reason == CandidateDecision.Reason.OTHER else ""
            decision = reject_candidate(
                candidate,
                user=self.user,
                reason=reason,
                note=note,
            )
            self.assertEqual(decision.reason, reason)
            self.assertEqual(decision.review_signals, [])

    def test_other_reason_requires_observation(self):
        with self.assertRaises(CandidateApprovalError):
            reject_candidate(
                self.candidate,
                user=self.user,
                reason=CandidateDecision.Reason.OTHER,
            )
        decision = reject_candidate(
            self.candidate,
            user=self.user,
            reason=CandidateDecision.Reason.OTHER,
            note="Motivo comercial específico observado pelo Owner.",
        )
        self.assertEqual(decision.note, "Motivo comercial específico observado pelo Owner.")

    def test_note_is_optional_for_specific_rejection_reason(self):
        decision = reject_candidate(
            self.candidate,
            user=self.user,
            reason=CandidateDecision.Reason.LISTING_UNAVAILABLE,
        )
        self.assertEqual(decision.note, "")
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.status, OfferCandidate.Status.REJECTED)

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
