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


def family_candidate_relevance(family_slug, title):
    text = " ".join((title or "").split())
    lowered = text.lower()
    profile = get_family_profile(family_slug)
    accessory_terms = profile.accessory_terms if profile else _GENERIC_ACCESSORY_TERMS
    if any(term in lowered for term in accessory_terms):
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
