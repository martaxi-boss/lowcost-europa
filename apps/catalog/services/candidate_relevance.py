import re

ACCESSORY_TERMS = (
    "cartridge",
    "replacement cartridge",
    "transducer replacement",
    "probe only",
    "handle only",
    "spare part",
    "accessory",
    "consumable",
    "gel",
    "cream",
)

_HIFU_POSITIVE_PATTERNS = (
    re.compile(r"\bhifu\b", re.IGNORECASE),
    re.compile(r"\bhi[- ]?fu\b", re.IGNORECASE),
    re.compile(r"high\s+intensity\s+focused\s+ultrasound", re.IGNORECASE),
)


def family_candidate_relevance(family_slug, title):
    text = " ".join((title or "").split())
    lowered = text.lower()
    if any(term in lowered for term in ACCESSORY_TERMS):
        return False, "ACCESSORY_OR_PART"
    if family_slug == "hifu" and not any(
        pattern.search(text) for pattern in _HIFU_POSITIVE_PATTERNS
    ):
        return False, "IRRELEVANT_FAMILY"
    return True, None


def is_family_candidate_relevant(family_slug, title):
    return family_candidate_relevance(family_slug, title)[0]
