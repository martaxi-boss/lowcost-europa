from apps.catalog.services.family_profiles import HIFU_PROFILE, get_family_profile


def _normalise(text):
    return " ".join((text or "").lower().split())


def learned_family_variants(profile, approved_titles):
    if not profile:
        return frozenset()
    learned = set()
    for title in approved_titles:
        text = title or ""
        for label, pattern in profile.variant_patterns:
            if pattern.search(text):
                learned.add(label)
    return frozenset(learned)


def family_candidate_priority(
    product,
    *,
    profile,
    learned_variants=(),
    semantic_negative_titles=(),
    classification_positive_titles=(),
):
    """Return discovery ordering signals only; never an approval decision."""
    title = _normalise(product.title)
    score = 0
    signals = []
    if profile:
        for label, pattern in profile.variant_patterns:
            if label in learned_variants and pattern.search(title):
                score += 40
                signals.append(f"approved pattern: {label}")
        for term, points, label in profile.scoring_terms:
            if term in title:
                score += points
                signals.append(label)
    if product.sales_count is not None:
        score += min(int(product.sales_count), 1000) // 100
        signals.append("sales metadata")
    if product.evaluation_rate_percent is not None:
        score += 5
        signals.append("rating metadata")
    if product.commission_rate is not None:
        score += 3
        signals.append("commission metadata")
    positive_titles = {_normalise(value) for value in classification_positive_titles if value}
    if title and title in positive_titles:
        score += 20
        signals.append("family move destination history")
    negative_titles = {_normalise(value) for value in semantic_negative_titles if value}
    if title and title in negative_titles:
        score -= 50
        signals.append("semantic rejection history")
    return score, tuple(dict.fromkeys(signals))


def hifu_candidate_priority(product, *, learned_variants=()):
    return family_candidate_priority(
        product,
        profile=HIFU_PROFILE,
        learned_variants=learned_variants,
    )


def learned_hifu_variants(approved_titles):
    return learned_family_variants(HIFU_PROFILE, approved_titles)


def priority_for_family(
    product,
    family_slug,
    *,
    learned_variants=(),
    semantic_negative_titles=(),
    classification_positive_titles=(),
):
    return family_candidate_priority(
        product,
        profile=get_family_profile(family_slug),
        learned_variants=learned_variants,
        semantic_negative_titles=semantic_negative_titles,
        classification_positive_titles=classification_positive_titles,
    )
