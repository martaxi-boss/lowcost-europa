import re

_GENERIC_ACCESSORY_TERMS = (
    "cartridge only",
    "replacement cartridge",
    "probe only",
    "handle only",
    "accessory",
    "gel",
    "cream",
    "consumable",
    "spare part",
)

_HIFU_POSITIVE_PATTERNS = (
    re.compile(r"\bhifu\b", re.IGNORECASE),
    re.compile(r"\bhi[- ]?fu\b", re.IGNORECASE),
    re.compile(r"high\s+intensity\s+focused\s+ultrasound", re.IGNORECASE),
)


def is_family_candidate_relevant(family_slug, title):
    text = " ".join((title or "").split())
    lowered = text.lower()
    if any(term in lowered for term in _GENERIC_ACCESSORY_TERMS):
        return False
    if family_slug == "hifu":
        return any(pattern.search(text) for pattern in _HIFU_POSITIVE_PATTERNS)
    return True
