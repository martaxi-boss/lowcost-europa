from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.catalog.models import CandidateDecision, Offer, OfferCandidate, ProductFamily
from apps.catalog.services.candidate_learning import (
    LISTING_FACTUAL_NEGATIVE,
    LOGISTICS_NEGATIVE,
    NEGATIVE_ACCESSORY,
    NEGATIVE_CLASSIFICATION,
    NEGATIVE_SEMANTIC,
    NEUTRAL_CONTEXT,
    QUALITY_NEGATIVE,
    family_learning_snapshot,
    interpret_decision,
    keyword_quality,
    prioritize_existing_keywords,
)
from apps.catalog.services.candidate_move import move_candidate_to_family
from apps.catalog.services.candidate_priority import priority_for_family
from apps.integrations.aliexpress.types import AliExpressProduct


class RejectionIntelligenceTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(
            name="Laser", slug="diodo-laser-remocao-tatuagens-pigmentacao"
        )
        self.other = ProductFamily.objects.create(name="Other", slug="other-family")
        self.user = get_user_model().objects.create_user(
            username="learning-owner", password="x", is_staff=True
        )

    def candidate(self, external_id, title, status=OfferCandidate.Status.REJECTED):
        return OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id=external_id,
            title=title,
            status=status,
        )

    def reject(self, external_id, title, *, reason="", signals=(), note=""):
        candidate = self.candidate(external_id, title)
        decision = CandidateDecision.objects.create(
            candidate=candidate,
            decision=CandidateDecision.Decision.REJECT,
            reason=reason,
            review_signals=list(signals),
            note=note,
            decided_by=self.user,
        )
        return candidate, decision

    def product(self, title):
        return AliExpressProduct(
            product_id="x",
            title=title,
            sales_count=10,
            evaluation_rate_percent=Decimal("98"),
            commission_rate=Decimal("5"),
        )

    def test_approval_is_neutral_and_does_not_learn_variants_or_ranking(self):
        approved = self.candidate(
            "approved",
            "Professional picosecond tattoo removal machine",
            status=OfferCandidate.Status.APPROVED,
        )
        decision = CandidateDecision.objects.create(
            candidate=approved,
            decision=CandidateDecision.Decision.APPROVE,
            decided_by=self.user,
        )
        self.assertEqual(interpret_decision(decision).kinds, frozenset())
        snapshot = family_learning_snapshot(self.family)
        self.assertNotIn("PICOSECOND", snapshot.learned_variants)
        learned = priority_for_family(
            self.product("Professional picosecond tattoo removal machine"),
            self.family.slug,
            learned_variants=snapshot.learned_variants,
        )[0]
        baseline = priority_for_family(
            self.product("Professional picosecond tattoo removal machine"),
            self.family.slug,
        )[0]
        self.assertEqual(learned, baseline)

    def test_accessory_rejection_is_semantic_and_strongly_downranks_pattern(self):
        title = "Replacement diode laser handle accessory"
        _, decision = self.reject(
            "accessory", title, reason=CandidateDecision.Reason.ACCESSORY_OR_PART
        )
        learning = interpret_decision(decision)
        self.assertIn(NEGATIVE_ACCESSORY, learning.kinds)
        self.assertIn(NEGATIVE_SEMANTIC, learning.kinds)
        snapshot = family_learning_snapshot(self.family)
        score, signals = priority_for_family(
            self.product("Replacement diode laser handle for machine"),
            self.family.slug,
            accessory_negative_titles=snapshot.accessory_negative_titles,
            semantic_negative_titles=snapshot.semantic_negative_titles,
        )
        self.assertLess(score, 0)
        self.assertIn("accessory rejection history", signals)

    def test_wrong_family_and_move_are_classification_only(self):
        candidate, decision = self.reject(
            "wrong", "Professional cavitation RF vacuum machine",
            reason=CandidateDecision.Reason.WRONG_FAMILY,
        )
        learning = interpret_decision(decision)
        self.assertIn(NEGATIVE_CLASSIFICATION, learning.kinds)
        self.assertNotIn(NEGATIVE_SEMANTIC, learning.kinds)
        moved, _ = move_candidate_to_family(candidate, target_family=self.other, user=self.user)
        self.assertEqual(moved.status, OfferCandidate.Status.PENDING)
        self.assertEqual(moved.decisions.filter(decision="APPROVE").count(), 0)
        self.assertIn(
            candidate.title, family_learning_snapshot(self.family).classification_negative_titles
        )
        self.assertIn(
            candidate.title,
            family_learning_snapshot(self.other).classification_positive_titles,
        )

    def test_poor_listing_is_quality_downrank_not_semantic_negative(self):
        title = "Professional diode laser machine unclear listing"
        _, decision = self.reject(
            "poor", title, reason=CandidateDecision.Reason.POOR_LISTING
        )
        learning = interpret_decision(decision)
        self.assertIn(QUALITY_NEGATIVE, learning.kinds)
        self.assertNotIn(NEGATIVE_SEMANTIC, learning.kinds)
        snapshot = family_learning_snapshot(self.family)
        score, signals = priority_for_family(
            self.product(title),
            self.family.slug,
            quality_negative_titles=snapshot.quality_negative_titles,
        )
        self.assertIn("poor-listing history", signals)
        self.assertGreater(score, -50)

    def test_logistics_signals_are_query_quality_only(self):
        signals = (
            CandidateDecision.ReviewSignal.DOES_NOT_DELIVER_TO_PT,
            CandidateDecision.ReviewSignal.DOES_NOT_SHIP_TO_PT,
            CandidateDecision.ReviewSignal.ORIGIN_NOT_ALLOWED,
        )
        for index, signal in enumerate(signals):
            _, decision = self.reject(
                f"log-{index}",
                f"Professional diode laser hair removal machine {index}",
                signals=[signal],
            )
            self.assertIn(LOGISTICS_NEGATIVE, interpret_decision(decision).kinds)
        snapshot = family_learning_snapshot(self.family)
        self.assertEqual(snapshot.semantic_negative_titles, ())
        self.assertEqual(len(snapshot.logistics_negative_titles), 3)
        quality = keyword_quality(self.family, "professional diode laser hair removal machine")
        self.assertGreater(quality.logistics_rejected, 0)

    def test_listing_unavailable_is_factual_not_semantic(self):
        _, decision = self.reject(
            "unavailable",
            "Professional Q switch tattoo removal machine",
            signals=[CandidateDecision.ReviewSignal.LISTING_UNAVAILABLE],
        )
        learning = interpret_decision(decision)
        self.assertIn(LISTING_FACTUAL_NEGATIVE, learning.kinds)
        self.assertNotIn(NEGATIVE_SEMANTIC, learning.kinds)
        snapshot = family_learning_snapshot(self.family)
        self.assertEqual(snapshot.semantic_negative_titles, ())
        self.assertIn(decision.candidate.title, snapshot.listing_factual_negative_titles)

    def test_delivers_confirmed_is_neutral_context_with_semantic_reason_preserved(self):
        _, decision = self.reject(
            "semantic-with-logistics-ok",
            "IPL-only consumer device",
            reason=CandidateDecision.Reason.IRRELEVANT,
            signals=[CandidateDecision.ReviewSignal.DELIVERS_TO_PT_CONFIRMED],
        )
        learning = interpret_decision(decision)
        self.assertIn(NEGATIVE_SEMANTIC, learning.kinds)
        self.assertIn(NEUTRAL_CONTEXT, learning.kinds)
        self.assertNotIn(LOGISTICS_NEGATIVE, learning.kinds)

    def test_note_is_audit_context_only_and_cannot_create_rule_or_keyword(self):
        _, decision = self.reject(
            "note-only",
            "Professional diode laser machine",
            reason=CandidateDecision.Reason.OTHER,
            note="não gostei da máquina",
        )
        learning = interpret_decision(decision)
        self.assertEqual(learning.note, "não gostei da máquina")
        self.assertEqual(learning.kinds, frozenset({NEUTRAL_CONTEXT}))
        snapshot = family_learning_snapshot(self.family)
        self.assertEqual(snapshot.semantic_negative_titles, ())
        original = ("professional diode laser machine", "picosecond tattoo removal machine")
        self.assertCountEqual(prioritize_existing_keywords(self.family, original), original)

    def test_keyword_quality_prioritizes_approval_over_accessory_and_logistics_history(self):
        approved = self.candidate(
            "qa", "Professional picosecond tattoo removal machine",
            status=OfferCandidate.Status.APPROVED,
        )
        CandidateDecision.objects.create(
            candidate=approved,
            decision=CandidateDecision.Decision.APPROVE,
            decided_by=self.user,
        )
        self.reject(
            "qb", "Replacement diode laser handle accessory",
            reason=CandidateDecision.Reason.ACCESSORY_OR_PART,
        )
        self.reject(
            "qc", "Professional diode laser hair removal machine",
            signals=[CandidateDecision.ReviewSignal.ORIGIN_NOT_ALLOWED],
        )
        keywords = (
            "replacement diode laser handle",
            "professional diode laser hair removal machine",
            "professional picosecond tattoo removal machine",
        )
        ordered = prioritize_existing_keywords(self.family, keywords)
        self.assertEqual(ordered[0], "professional picosecond tattoo removal machine")
        qualities = {value: keyword_quality(self.family, value) for value in keywords}
        self.assertGreater(qualities[keywords[2]].score, qualities[keywords[1]].score)
        self.assertGreater(qualities[keywords[1]].score, qualities[keywords[0]].score)
        self.assertGreater(qualities[keywords[0]].accessory_rejected, 0)
        self.assertGreater(qualities[keywords[1]].logistics_rejected, 0)

    def test_family_isolation(self):
        self.reject(
            "isolated", "Professional diode laser machine",
            reason=CandidateDecision.Reason.IRRELEVANT,
        )
        self.assertTrue(family_learning_snapshot(self.family).semantic_negative_titles)
        self.assertFalse(family_learning_snapshot(self.other).semantic_negative_titles)
