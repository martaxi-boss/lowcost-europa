import re

_NOT_SHIPPABLE_PT_PATTERNS = (
    re.compile(r"(?:cannot|can't|does not|doesn't|not)\s+ship\s+to\s+(?:pt|portugal)", re.I),
    re.compile(r"(?:pt|portugal)\s+(?:is\s+)?(?:not\s+available|unsupported)", re.I),
    re.compile(r"no\s+delivery\s+to\s+(?:pt|portugal)", re.I),
)


def is_factually_not_shippable_to_pt(product):
    raw = (getattr(product, "ship_to_days_raw", None) or "").strip()
    if not raw:
        return False
    return any(pattern.search(raw) for pattern in _NOT_SHIPPABLE_PT_PATTERNS)
