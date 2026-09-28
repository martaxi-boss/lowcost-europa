import re
from collections import defaultdict
from dataclasses import dataclass

from django.db.models import Q

from apps.catalog.models import CandidateDecision, CandidateFamilyMoveEvent, OfferCandidate
from apps.catalog.services.candidate_priority import learned_family_variants
from apps.catalog.services.family_profiles import get_family_profile

POSITIVE_SEMANTIC = "POSITIVE_SEMANTIC"
NEGATIVE_SEMANTIC = "NEGATIVE_SEMANTIC"
NEGATIVE_CLASSIFICATION = "NEGATIVE_CLASSIFICATION"
NEGATIVE_ACCESSORY = "NEGATIVE_ACCESSORY"
LOGISTICS_NEGATIVE = "LOGISTICS_NEGATIVE"
LISTING_FACTUAL_NEGATIVE = "LISTING_FACTUAL_NEGATIVE"
QUALITY_NEGATIVE = "QUALITY_NEGATIVE"
NEUTRAL_CONTEXT = "NEUTRAL_CONTEXT"

_LOGISTICS_SIGNALS = frozenset(
    {
        CandidateDecision.ReviewSignal.DOES_NOT_DELIVER_TO_PT,
        CandidateDecision.ReviewSignal.DOES_NOT_SHIP_TO_PT,
        CandidateDecision.ReviewSignal.ORIGIN_NOT_ALLOWED,
    }
)
_LOGISTICS_REASONS = frozenset(
    {
        CandidateDecision.Reason.DOES_NOT_SHIP_TO_PT,
        CandidateDecision.Reason.PT_DELIVERY_NOT_CONFIRMED,
        CandidateDecision.Reason.ORIGIN_NOT_CONFIRMED,
        CandidateDecision.Reason.ORIGIN_NOT_ALLOWED,
    }
)
_STOPWORDS = frozenset(
    {
        "professional", "machine", "laser", "beauty", "salon", "equipment",
        "removal", "device", "system", "for", "and", "the", "with", "new",
    }
)


@dataclass(frozen=True)
class DecisionLearning:
    kinds: frozenset[str]
    title: str
    note: str


@dataclass(frozen=True)
class FamilyLearningSnapshot:
    learned_variants: frozenset[str]
    positive_titles: tuple[str, ...]
    semantic_negative_titles: tuple[str, ...]
    accessory_negative_titles: tuple[str, ...]
    classification_negative_titles: tuple[str, ...]
    quality_negative_titles: tuple[str, ...]
    classification_positive_titles: tuple[str, ...]
    logistics_negative_titles: tuple[str, ...]
    listing_factual_negative_titles: tuple[str, ...]


@dataclass(frozen=True)
class KeywordQuality:
    keyword: str
    results_discovered: int = 0
    approved: int = 0
    semantic_rejected: int = 0
    accessory_rejected: int = 0
    wrong_family: int = 0
    quality_rejected: int = 0
    logistics_rejected: int = 0
    listing_unavailable: int = 0

    @property
    def score(self):
        return (
            - self.accessory_rejected * 10
            - self.semantic_rejected * 8
            - self.wrong_family * 7
            - self.quality_rejected * 4
            - self.logistics_rejected * 3
            - self.listing_unavailable * 2
        )


def interpret_decision(decision):
    title = decision.candidate.title or ""
    kinds = set()
    if decision.decision == CandidateDecision.Decision.APPROVE:
        # Approval is protocol attestation, not a discovery-learning signal.
        return DecisionLearning(frozenset(), title, decision.note or "")

    reason = decision.reason
    if reason == CandidateDecision.Reason.ACCESSORY_OR_PART:
        kinds.update({NEGATIVE_ACCESSORY, NEGATIVE_SEMANTIC})
    elif reason == CandidateDecision.Reason.WRONG_FAMILY:
        kinds.add(NEGATIVE_CLASSIFICATION)
    elif reason == CandidateDecision.Reason.POOR_LISTING:
        kinds.add(QUALITY_NEGATIVE)
    elif reason == CandidateDecision.Reason.IRRELEVANT:
        kinds.add(NEGATIVE_SEMANTIC)
    elif reason in _LOGISTICS_REASONS:
        kinds.add(LOGISTICS_NEGATIVE)
    elif reason in {
        CandidateDecision.Reason.LISTING_UNAVAILABLE,
        CandidateDecision.Reason.LISTING_CHANGED,
    }:
        kinds.add(LISTING_FACTUAL_NEGATIVE)
    elif reason:
        kinds.add(NEUTRAL_CONTEXT)

    signals = set(decision.review_signals or ())
    if signals & _LOGISTICS_SIGNALS:
        kinds.add(LOGISTICS_NEGATIVE)
    if CandidateDecision.ReviewSignal.LISTING_UNAVAILABLE in signals:
        kinds.add(LISTING_FACTUAL_NEGATIVE)
    if CandidateDecision.ReviewSignal.DELIVERS_TO_PT_CONFIRMED in signals:
        kinds.add(NEUTRAL_CONTEXT)
    if not kinds:
        kinds.add(NEUTRAL_CONTEXT)
    return DecisionLearning(frozenset(kinds), title, decision.note or "")


def family_learning_snapshot(family):
    profile = get_family_profile(family.slug)
    decisions = list(
        CandidateDecision.objects.filter(
            Q(candidate__product_family=family)
            | Q(candidate__family_move_events__from_family=family)
            | Q(candidate__family_move_events__to_family=family)
        )
        .select_related("candidate")
        .distinct()
        .order_by("pk")
    )
    candidate_ids = {decision.candidate_id for decision in decisions}
    moves_by_candidate = defaultdict(list)
    for move in CandidateFamilyMoveEvent.objects.filter(candidate_id__in=candidate_ids).order_by(
        "candidate_id", "acted_at", "pk"
    ):
        moves_by_candidate[move.candidate_id].append(move)

    def decision_family_id(decision):
        family_id = decision.candidate.product_family_id
        for move in reversed(moves_by_candidate[decision.candidate_id]):
            if decision.decided_at >= move.acted_at:
                break
            family_id = move.from_family_id
        return family_id

    decisions = [decision for decision in decisions if decision_family_id(decision) == family.pk]
    buckets = {
        POSITIVE_SEMANTIC: [], NEGATIVE_SEMANTIC: [], NEGATIVE_ACCESSORY: [],
        NEGATIVE_CLASSIFICATION: [], QUALITY_NEGATIVE: [], LOGISTICS_NEGATIVE: [],
        LISTING_FACTUAL_NEGATIVE: [],
    }
    for decision in decisions:
        learning = interpret_decision(decision)
        for kind in buckets:
            if kind in learning.kinds and learning.title:
                buckets[kind].append(learning.title)

    # Owner approval must never create positive discovery/ranking feedback.
    positive_titles = ()
    move_positive = tuple(
        CandidateFamilyMoveEvent.objects.filter(to_family=family).values_list(
            "title_snapshot", flat=True
        )
    )
    move_negative = tuple(
        CandidateFamilyMoveEvent.objects.filter(from_family=family).values_list(
            "title_snapshot", flat=True
        )
    )
    classification_negative = tuple(
        dict.fromkeys([*buckets[NEGATIVE_CLASSIFICATION], *move_negative])
    )
    return FamilyLearningSnapshot(
        learned_variants=learned_family_variants(profile, positive_titles),
        positive_titles=positive_titles,
        semantic_negative_titles=tuple(dict.fromkeys(buckets[NEGATIVE_SEMANTIC])),
        accessory_negative_titles=tuple(dict.fromkeys(buckets[NEGATIVE_ACCESSORY])),
        classification_negative_titles=classification_negative,
        quality_negative_titles=tuple(dict.fromkeys(buckets[QUALITY_NEGATIVE])),
        classification_positive_titles=tuple(dict.fromkeys(move_positive)),
        logistics_negative_titles=tuple(dict.fromkeys(buckets[LOGISTICS_NEGATIVE])),
        listing_factual_negative_titles=tuple(
            dict.fromkeys(buckets[LISTING_FACTUAL_NEGATIVE])
        ),
    )


def _tokens(text):
    return {
        token for token in re.findall(r"[a-z0-9]+", (text or "").lower())
        if len(token) > 2 and token not in _STOPWORDS
    }


def _keyword_matches_title(keyword, title):
    keyword_tokens = _tokens(keyword)
    title_tokens = _tokens(title)
    if not keyword_tokens or not title_tokens:
        return False
    overlap = len(keyword_tokens & title_tokens)
    needed = 1 if len(keyword_tokens) == 1 else max(2, (len(keyword_tokens) + 1) // 2)
    return overlap >= needed


def keyword_quality(family, keyword, snapshot=None):
    snapshot = snapshot or family_learning_snapshot(family)
    results_discovered = sum(
        _keyword_matches_title(keyword, title)
        for title in OfferCandidate.objects.filter(product_family=family).values_list(
            "title", flat=True
        )
    )
    groups = (
        ("semantic_rejected", snapshot.semantic_negative_titles),
        ("accessory_rejected", snapshot.accessory_negative_titles),
        ("wrong_family", snapshot.classification_negative_titles),
        ("quality_rejected", snapshot.quality_negative_titles),
        ("logistics_rejected", snapshot.logistics_negative_titles),
        ("listing_unavailable", snapshot.listing_factual_negative_titles),
    )
    counts = {
        name: sum(_keyword_matches_title(keyword, title) for title in titles)
        for name, titles in groups
    }
    counts["approved"] = 0
    return KeywordQuality(
        keyword=keyword, results_discovered=results_discovered, **counts
    )


def prioritize_existing_keywords(family, keywords):
    snapshot = family_learning_snapshot(family)
    indexed = list(enumerate(keywords))
    qualities = {
        index: keyword_quality(family, keyword, snapshot=snapshot)
        for index, keyword in indexed
    }
    return tuple(
        keyword
        for index, keyword in sorted(
            indexed,
            key=lambda item: (-qualities[item[0]].score, item[0]),
        )
    )
