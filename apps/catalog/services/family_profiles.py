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


LASER_TATTOO_PROFILE = FamilyProfile(
    slug="diodo-laser-remocao-tatuagens-pigmentacao",
    required_patterns=(
        _rx(r"\bdiode\s+laser\b"),
        _rx(r"\blaser\s+hair\s+removal\b"),
        _rx(r"\bhair\s+removal\s+(?:diode\s+)?laser\b"),
        _rx(r"\bprofessional\s+diode\s+laser\b"),
        _rx(r"\bsalon\s+diode\s+laser\b"),
        _rx(r"\b(?:triple\s+wave|triple\s+wavelength|3\s+wavelengths?)\b.*\b(?:laser|machine|equipment)\b"),
        _rx(r"(?=.*\b755\s*nm?\b)(?=.*\b808\s*nm?\b)(?=.*\b1064\s*nm?\b)(?=.*\b(?:laser|machine|equipment)\b)"),
        _rx(r"\bpermanent\s+hair\s+reduction\b"),
        _rx(
            r"(?=.*\balexandrite\b)(?=.*\bdiode\b)(?=.*\bnd\s*[:.-]?\s*yag\b)(?=.*\bhair\s+removal\b)"
        ),
        _rx(r"\btattoo\s+removal\b"),
        _rx(r"\blaser\s+tattoo\s+removal\b"),
        _rx(r"\bpigmentation\s+removal\b"),
        _rx(r"\bpigment\s+removal\b"),
        _rx(r"\bpigment\s+laser\b"),
        _rx(r"\b(?:q[- ]?switch(?:ed)?|q\s+switch)\s+(?:nd\s*[:.-]?\s*)?yag\b"),
        _rx(r"\bnd\s*[:.-]?\s*yag\b.*\b(?:tattoo|pigment|freckle|melanin|carbon\s+peel)\b"),
        _rx(r"\b(?:tattoo|pigment|freckle|melanin|carbon\s+peel)\b.*\bnd\s*[:.-]?\s*yag\b"),
        _rx(r"\bpicosecond\b"),
        _rx(r"\bpico\s+laser\b"),
        _rx(r"\bpico\s+tattoo\s+removal\b"),
        _rx(r"\bpicosure(?:-style)?\b"),
        _rx(r"\blaser\b.*\bfreckle\s+removal\b"),
        _rx(r"\bfreckle\s+removal\b.*\blaser\b"),
        _rx(r"\blaser\b.*\bmelanin\s+treatment\b"),
        _rx(r"\bmelanin\s+treatment\b.*\blaser\b"),
        _rx(
            r"\b(?:q[- ]?switch(?:ed)?|nd\s*[:.-]?\s*yag|tattoo|pigment)\b.*"
            r"\b532\s*nm\b.*\b1064\s*nm\b"
        ),
        _rx(
            r"\b532\s*nm\b.*\b1064\s*nm\b.*"
            r"\b(?:q[- ]?switch(?:ed)?|nd\s*[:.-]?\s*yag|tattoo|pigment)\b"
        ),
        _rx(r"\blaser\b.*\bcarbon\s+peel\b"),
        _rx(r"\bcarbon\s+peel\b.*\blaser\b"),
    ),
    accessory_terms=(
        "press button",
        "switch button",
        "button for",
        "handle only",
        "handpiece only",
        "replacement handpiece",
        "replacement handle",
        "laser bar",
        "replacement bar",
        "laser module",
        "replacement head",
        "head only",
        "lens",
        "filter",
        "screen replacement",
        "board",
        "power supply",
        "pedal",
        "cable",
        "connector",
        "tip",
        "cartridge",
        "spare part",
        "replacement part",
        "accessory",
        "consumable",
    ),
    variant_patterns=(
        ("808NM", _rx(r"\b808\s*nm\b")),
        (
            "TRIPLE WAVE",
            _rx(
                r"\b(?:triple\s+wave|triple\s+wavelength|3\s+wavelengths?|three\s+wavelengths?)\b|(?=.*\b755\s*nm?\b)(?=.*\b808\s*nm?\b)(?=.*\b1064\s*nm?\b)"
            ),
        ),
        ("755/808/1064", _rx(r"(?=.*\b755\s*nm?\b)(?=.*\b808\s*nm?\b)(?=.*\b1064\s*nm?\b)")),
        (
            "DUAL WAVE",
            _rx(r"\b(?:dual\s+wave|dual\s+wavelength|2\s+wavelengths?|two\s+wavelengths?)\b"),
        ),
        ("FOUR WAVE", _rx(r"\b(?:four\s+wave|four\s+wavelength|4\s+wavelengths?)\b")),
        ("PICOSECOND", _rx(r"\b(?:picosecond|pico\s+laser|picosure(?:-style)?)\b")),
        (
            "Q-SWITCH ND:YAG",
            _rx(
                r"\bq[- ]?switch(?:ed)?\b.*\b(?:nd\s*[:.-]?\s*)?yag\b|"
                r"\bnd\s*[:.-]?\s*yag\b.*\bq[- ]?switch(?:ed)?\b"
            ),
        ),
        (
            "532/1064",
            _rx(r"(?=.*\b532\s*nm?\b)(?=.*\b1064\s*nm?\b)"),
        ),
        ("TATTOO REMOVAL", _rx(r"\btattoo\s+removal\b")),
        ("PIGMENTATION REMOVAL", _rx(r"\b(?:pigmentation|pigment)\s+removal\b")),
        (
            "DIODE + PICO",
            _rx(r"(?=.*\bdiode\s+laser\b)(?=.*\b(?:picosecond|pico\s+laser)\b)"),
        ),
        (
            "DIODE + ND:YAG",
            _rx(r"(?=.*\bdiode\s+laser\b)(?=.*\bnd\s*[:.-]?\s*yag\b)"),
        ),
        (
            "MULTIFUNCTION LASER",
            _rx(
                r"\b(?:multi[- ]?function|multifunction)\b.*\blaser\b|"
                r"\blaser\b.*\b(?:multi[- ]?function|multifunction)\b"
            ),
        ),
    ),
    scoring_terms=(
        *_COMMON_SCORING,
        ("diode laser", 16, "diode laser"),
        ("hair removal", 12, "hair removal"),
        ("triple wave", 16, "triple wave"),
        ("triple wavelength", 16, "triple wavelength"),
        ("tattoo removal", 16, "tattoo removal"),
        ("pigmentation removal", 14, "pigmentation removal"),
        ("pigment removal", 14, "pigment removal"),
        ("q switch", 14, "q switch"),
        ("q-switched", 14, "q-switched"),
        ("picosecond", 16, "picosecond"),
        ("pico laser", 14, "pico laser"),
        ("nd:yag", 12, "nd:yag"),
        ("nd yag", 12, "nd yag"),
        ("carbon peel", 8, "carbon peel"),
    ),
    search_keywords=(
        # Priority 1 — Tattoo / Q-Switch
        "tattoo removal laser machine professional",
        "professional tattoo removal laser machine",
        "Q switch tattoo removal machine professional",
        "Q switched Nd YAG tattoo removal machine",
        "Nd YAG tattoo removal beauty salon machine",
        "532 1064 tattoo removal laser",
        "professional laser tattoo pigment removal machine",
        # Priority 2 — Pigmentation
        "professional pigmentation removal laser machine",
        "pigment removal beauty salon laser",
        "freckle pigmentation removal laser machine",
        "Nd YAG pigmentation removal machine",
        "532 1064 pigmentation removal laser",
        "melanin pigment removal professional machine",
        # Priority 3 — Pico / Picosecond
        "professional picosecond laser machine",
        "picosecond tattoo removal machine",
        "pico laser tattoo removal professional",
        "pico pigmentation removal machine",
        "professional pico laser beauty salon machine",
        "picosecond pigment removal laser",
        # Priority 4 — Triple Wave
        "professional triple wave diode laser machine",
        "triple wavelength diode laser salon equipment",
        "3 wavelength diode laser professional",
        "755 808 1064 professional diode laser",
        "755nm 808nm 1064nm diode laser salon",
        # Priority 5 — Professional Diode
        "professional diode laser hair removal machine",
        "808nm professional diode laser salon machine",
        "diode laser clinic hair removal equipment",
        # Priority 6 — Coherent professional combos
        "diode picosecond professional machine",
        "diode laser tattoo removal combo",
        "diode Nd YAG professional machine",
        "hair removal tattoo removal professional laser",
        "diode pico Nd YAG multifunction machine",
    ),
)

PROFILES = {
    HIFU_PROFILE.slug: HIFU_PROFILE,
    CAVITATION_PROFILE.slug: CAVITATION_PROFILE,
    HYDRODERMO_PROFILE.slug: HYDRODERMO_PROFILE,
    LASER_TATTOO_PROFILE.slug: LASER_TATTOO_PROFILE,
}


def get_family_profile(family_slug):
    return PROFILES.get(family_slug)
