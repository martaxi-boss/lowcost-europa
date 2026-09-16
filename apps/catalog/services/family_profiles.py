import re
from dataclasses import dataclass


@dataclass(frozen=True)
class FamilyProfile:
    slug: str
    required_patterns: tuple[re.Pattern, ...]
    accessory_terms: tuple[str, ...]
    variant_patterns: tuple[tuple[str, re.Pattern], ...]
    scoring_terms: tuple[tuple[str, int, str], ...]
    search_keywords: tuple[str, ...] = ()


def _rx(pattern):
    return re.compile(pattern, re.IGNORECASE)


_COMMON_SCORING = (
    ("professional", 14, "professional"),
    ("beauty salon", 12, "beauty salon"),
    ("salon", 8, "salon"),
    ("machine", 8, "machine"),
    ("equipment", 8, "equipment"),
    ("body", 4, "body"),
)

HIFU_PROFILE = FamilyProfile(
    slug="hifu",
    required_patterns=(
        _rx(r"\bhifu\b"),
        _rx(r"\bhi[- ]?fu\b"),
        _rx(r"high\s+intensity\s+focused\s+ultrasound"),
    ),
    accessory_terms=(
        "cartridge only",
        "replacement cartridge",
        "transducer replacement",
        "probe only",
        "handle only",
        "spare part",
        "accessory",
        "consumable",
        "gel",
        "cream",
    ),
    variant_patterns=(
        ("7D", _rx(r"\b7d\b")),
        ("22D MAX", _rx(r"\b22d\s*max\b")),
        ("25D", _rx(r"\b25d\b")),
        ("360MAX", _rx(r"\b360\s*max\b")),
    ),
    scoring_terms=((*_COMMON_SCORING, ("face", 4, "face"))),
    search_keywords=(
        "22D MAX HIFU professional machine",
        "7D HIFU beauty salon machine",
        "25D 360MAX HIFU professional equipment",
    ),
)

CAVITATION_PROFILE = FamilyProfile(
    slug="cavitacao-rf-vacuum-corpo",
    required_patterns=(
        _rx(r"\bcavitation\b"),
        _rx(r"ultrasonic\s+cavitation"),
        _rx(r"\brf\b"),
        _rx(r"radio\s+frequency"),
        _rx(r"\bvacuum\b"),
    ),
    accessory_terms=(
        "gel",
        "cream",
        "handle only",
        "handles only",
        "probe only",
        "probes only",
        "replacement part",
        "replacement parts",
        "spare part",
        "consumable",
        "accessory",
        "pads only",
    ),
    variant_patterns=(
        ("5-IN-1", _rx(r"\b5\s*[- ]?in\s*[- ]?1\b")),
        ("6-IN-1", _rx(r"\b6\s*[- ]?in\s*[- ]?1\b")),
        ("9-IN-1", _rx(r"\b9\s*[- ]?in\s*[- ]?1\b")),
    ),
    scoring_terms=(
        *_COMMON_SCORING,
        ("cavitation", 12, "cavitation"),
        ("vacuum", 10, "vacuum"),
        ("radio frequency", 8, "radio frequency"),
        ("slimming", 5, "slimming"),
    ),
    search_keywords=(
        "cavitation RF vacuum body slimming machine",
        "6 in 1 cavitation RF vacuum beauty machine",
    ),
)

PROFILES = {
    HIFU_PROFILE.slug: HIFU_PROFILE,
    CAVITATION_PROFILE.slug: CAVITATION_PROFILE,
}


def get_family_profile(family_slug):
    return PROFILES.get(family_slug)
