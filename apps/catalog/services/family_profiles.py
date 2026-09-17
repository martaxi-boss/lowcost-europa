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
        _rx(r"\bcupping\b"),
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
        "accessories",
        "accesories",
        "stowage plate",
        "stand support",
        "pads only",
        "cup only",
        "cups only",
        "hose only",
        "tube only",
        "filter only",
        "power supply only",
        "cart only",
        "trolley only",
        "replacement head only",
    ),
    variant_patterns=(
        ("3-IN-1", _rx(r"\b3\s*[- ]?in\s*[- ]?1\b")),
        ("4-IN-1", _rx(r"\b4\s*[- ]?in\s*[- ]?1\b")),
        ("5-IN-1", _rx(r"\b5\s*[- ]?in\s*[- ]?1\b")),
        ("6-IN-1", _rx(r"\b6\s*[- ]?in\s*[- ]?1\b")),
        ("7-IN-1", _rx(r"\b7\s*[- ]?in\s*[- ]?1\b")),
        ("8-IN-1", _rx(r"\b8\s*[- ]?in\s*[- ]?1\b")),
        ("9-IN-1", _rx(r"\b9\s*[- ]?in\s*[- ]?1\b")),
    ),
    scoring_terms=(
        *_COMMON_SCORING,
        ("cavitation", 12, "cavitation"),
        ("vacuum", 10, "vacuum"),
        ("radio frequency", 8, "radio frequency"),
        ("cupping", 8, "cupping"),
        ("slimming", 5, "slimming"),
    ),
    search_keywords=(
        "cavitation RF vacuum body slimming machine",
        "6 in 1 cavitation RF vacuum beauty machine",
    ),
)


HYDRODERMO_PROFILE = FamilyProfile(
    slug="hydrodermoabrasao-aqua-facial-multifuncoes",
    required_patterns=(
        _rx(r"\bmicro\s*dermabrasion\b"),
        _rx(r"\bdiamond\s+micro\s*dermabrasion\b"),
        _rx(r"\bhydro\s*dermabrasion\b"),
        _rx(r"\bhydrodermabrasion\b"),
        _rx(r"\bhydro\s+facial\b"),
        _rx(r"\bhydra\s*facial\b"),
        _rx(r"\baqua\s+facial\b"),
        _rx(r"\baqua\s+peel\b"),
        _rx(r"\bwater\s+dermabrasion\b"),
    ),
    accessory_terms=(
        "tips only",
        "replacement tips",
        "diamond tips only",
        "serum only",
        "solution only",
        "liquid only",
        "bottle only",
        "handle only",
        "handpiece only",
        "probe only",
        "filter only",
        "tube only",
        "hose only",
        "spray gun only",
        "replacement part",
        "spare part",
        "accessory",
        "accessories",
        "consumable",
        "jar only",
    ),
    variant_patterns=(
        ("5-IN-1", _rx(r"\b5\s*[- ]?in\s*[- ]?1\b")),
        ("6-IN-1", _rx(r"\b6\s*[- ]?in\s*[- ]?1\b")),
        ("7-IN-1", _rx(r"\b7\s*[- ]?in\s*[- ]?1\b")),
        ("8-IN-1", _rx(r"\b8\s*[- ]?in\s*[- ]?1\b")),
        ("9-IN-1", _rx(r"\b9\s*[- ]?in\s*[- ]?1\b")),
        ("10-IN-1", _rx(r"\b10\s*[- ]?in\s*[- ]?1\b")),
        ("12-IN-1", _rx(r"\b12\s*[- ]?in\s*[- ]?1\b")),
        ("14-IN-1", _rx(r"\b14\s*[- ]?in\s*[- ]?1\b")),
    ),
    scoring_terms=(
        *_COMMON_SCORING,
        ("microdermabrasion", 14, "microdermabrasion"),
        ("diamond microdermabrasion", 16, "diamond microdermabrasion"),
        ("hydrodermabrasion", 14, "hydrodermabrasion"),
        ("hydro facial", 12, "hydro facial"),
        ("aqua facial", 12, "aqua facial"),
        ("aqua peel", 10, "aqua peel"),
        ("water dermabrasion", 10, "water dermabrasion"),
    ),
    search_keywords=(
        "microdermabrasion professional facial machine",
        "diamond microdermabrasion beauty salon machine",
        "hydrodermabrasion professional facial machine",
        "hydro facial multifunction beauty machine",
        "aqua peel hydro dermabrasion machine",
    ),
)

PROFILES = {
    HIFU_PROFILE.slug: HIFU_PROFILE,
    CAVITATION_PROFILE.slug: CAVITATION_PROFILE,
    HYDRODERMO_PROFILE.slug: HYDRODERMO_PROFILE,
}


def get_family_profile(family_slug):
    return PROFILES.get(family_slug)
