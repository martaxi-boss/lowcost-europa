import re

_VARIANT_PATTERNS = {
    "7D": re.compile(r"\b7d\b", re.IGNORECASE),
    "22D MAX": re.compile(r"\b22d\s*max\b", re.IGNORECASE),
    "25D": re.compile(r"\b25d\b", re.IGNORECASE),
    "360MAX": re.compile(r"\b360\s*max\b", re.IGNORECASE),
}


def learned_hifu_variants(approved_titles):
    learned = set()
    for title in approved_titles:
        text = title or ""
        for label, pattern in _VARIANT_PATTERNS.items():
            if pattern.search(text):
                learned.add(label)
    return frozenset(learned)


def hifu_candidate_priority(product, *, learned_variants=()):
    """Return a deterministic discovery ordering score, never an approval score."""
    title = " ".join((product.title or "").split()).lower()
    score = 0
    signals = []
    for label in learned_variants:
        pattern = _VARIANT_PATTERNS.get(label)
        if pattern and pattern.search(title):
            score += 40
            signals.append(f"approved pattern: {label}")
    for term, points, label in (
        ("professional", 14, "professional"),
        ("beauty salon", 12, "beauty salon"),
        ("salon", 8, "salon"),
        ("machine", 8, "machine"),
        ("equipment", 8, "equipment"),
        ("face", 4, "face"),
        ("body", 4, "body"),
    ):
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
    return score, tuple(dict.fromkeys(signals))
