from apps.catalog.services.family_profiles import get_family_profile

_GENERIC_ACCESSORY_TERMS = (
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
)

_LASER_TATTOO_FAMILY = "diodo-laser-remocao-tatuagens-pigmentacao"
_LASER_COMPLETE_MACHINE_MARKERS = (
    "machine", "equipment", "system", "professional", "beauty salon", "clinic", "multifunction"
)
_LASER_COMPONENT_ALWAYS = (
    "press button", "switch button", "button for", "replacement handpiece",
    "replacement handle", "replacement bar", "replacement head", "screen replacement",
    "spare part", "replacement part", "power supply", "connector", "cartridge",
    "handpiece only", "handle only", "head only",
)
_LASER_COMPONENT_TERMS = (
    "laser bar", "laser module", "lens", "filter", "board", "pedal", "cable",
    "tip", "accessory", "consumable",
)
_LASER_VALID_TECH_MARKERS = (
    "diode", "picosecond", "pico laser", "nd yag", "nd:yag", "nd-yag",
    "tattoo", "pigment", "pigmentation", "q switch", "q-switch", "q switched",
)
_LASER_CONSUMER_IPL_MARKERS = (
    "home use ipl", "home-use ipl", "personal ipl", "home epilator",
    "consumer hair remover", "handheld consumer ipl", "ipl-only", "ipl only",
)


def _laser_family_component_or_consumer_only(lowered):
    if lowered.startswith(("accessory for ", "accessories for ")):
        return True
    if any(marker in lowered for marker in _LASER_CONSUMER_IPL_MARKERS):
        if not any(marker in lowered for marker in _LASER_VALID_TECH_MARKERS):
            return True
    if "ipl" in lowered and not any(marker in lowered for marker in _LASER_VALID_TECH_MARKERS):
        if any(
            marker in lowered
            for marker in ("home", "personal", "consumer", "handheld", "epilator")
        ):
            return True
    if any(marker in lowered for marker in _LASER_COMPONENT_ALWAYS):
        return True
    if "replacement" in lowered and any(
        part in lowered
        for part in (
            "handle",
            "handpiece",
            "bar",
            "head",
            "module",
            "screen",
            "lens",
            "filter",
            "board",
            "cable",
            "tip",
        )
    ):
        return True
    component_hits = [term for term in _LASER_COMPONENT_TERMS if term in lowered]
    if not component_hits:
        return False
    complete = any(marker in lowered for marker in _LASER_COMPLETE_MACHINE_MARKERS)
    # Component titles commonly say "for ... machine"; that is not evidence of a full machine.
    if " for " in lowered and any(
        marker in lowered for marker in ("machine", "handpiece", "handle")
    ):
        return True
    if not complete:
        return True
    # A complete-machine title may mention included components (e.g. "machine with cooling handle").
    return not any(f"with {term}" in lowered for term in component_hits)


def family_candidate_relevance(family_slug, title):
    text = " ".join((title or "").split())
    lowered = text.lower()
    profile = get_family_profile(family_slug)
    accessory_terms = profile.accessory_terms if profile else _GENERIC_ACCESSORY_TERMS
    if family_slug == _LASER_TATTOO_FAMILY:
        if _laser_family_component_or_consumer_only(lowered):
            return False, "ACCESSORY_OR_PART"
    elif any(term in lowered for term in accessory_terms):
        return False, "ACCESSORY_OR_PART"
    if profile and profile.required_patterns:
        if not any(pattern.search(text) for pattern in profile.required_patterns):
            return False, "IRRELEVANT_FAMILY"
    if family_slug == "cavitacao-rf-vacuum-corpo":
        facial_only = ("face" in lowered or "facial" in lowered) and not any(
            term in lowered for term in ("body", "slimming", "cavitation", "vacuum")
        )
        if facial_only:
            return False, "IRRELEVANT_FAMILY"
    return True, None


def is_family_candidate_relevant(family_slug, title):
    return family_candidate_relevance(family_slug, title)[0]
