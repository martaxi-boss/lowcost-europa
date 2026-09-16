from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.catalog.models import CandidateDecision, Offer, OfferCandidate, ProductFamily
from apps.catalog.services.candidate_discovery import _learning_inputs
from apps.catalog.services.candidate_move import move_candidate_to_family


class LearningCausalityTests(TestCase):
    def setUp(self):
        self.hifu = ProductFamily.objects.create(name="HIFU", slug="hifu")
        self.cav = ProductFamily.objects.create(
            name="Cav", slug="cavitacao-rf-vacuum-corpo"
        )
        self.user = get_user_model().objects.create_user(
            username="staff-learning", password="x", is_staff=True
        )

    def rejected(self, external_id, title, reason):
        candidate = OfferCandidate.objects.create(
            product_family=self.hifu,
            source=Offer.Source.ALIEXPRESS,
            external_product_id=external_id,
            title=title,
            status=OfferCandidate.Status.REJECTED,
        )
        CandidateDecision.objects.create(
            candidate=candidate,
            decision=CandidateDecision.Decision.REJECT,
            reason=reason,
            decided_by=self.user,
        )
        return candidate

    def test_semantic_rejection_enters_learning_but_logistics_rejection_does_not(self):
        self.rejected("semantic", "Bad semantic model", CandidateDecision.Reason.POOR_LISTING)
        self.rejected(
            "logistics",
            "Good model wrong origin",
            CandidateDecision.Reason.ORIGIN_NOT_ALLOWED,
        )
        _, _, negatives = _learning_inputs(self.hifu)
        self.assertIn("Bad semantic model", negatives)
        self.assertNotIn("Good model wrong origin", negatives)

    def test_move_then_positive_learning_belongs_to_final_family(self):
        candidate = OfferCandidate.objects.create(
            product_family=self.hifu,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="move-learn",
            title="Professional 6 in 1 cavitation RF vacuum machine",
            status=OfferCandidate.Status.REJECTED,
        )
        moved, _ = move_candidate_to_family(candidate, target_family=self.cav, user=self.user)
        moved.status = OfferCandidate.Status.APPROVED
        moved.save(update_fields=["status", "updated_at"])
        _, hifu_variants, _ = _learning_inputs(self.hifu)
        _, cav_variants, _ = _learning_inputs(self.cav)
        self.assertNotIn("6-IN-1", hifu_variants)
        self.assertIn("6-IN-1", cav_variants)
