"""Manually curated storefront categories: only owner-supplied affiliate links.

Keep the singular constant for backwards compatibility; use the plural set for all shared
storefront, discovery, maintenance and availability checks.
"""

MANUAL_ONLY_FAMILY_SLUG = "cavitacao-rf-vacuum-corpo"
MICRODERMO_MANUAL_FAMILY_SLUG = "hydrodermoabrasao-aqua-facial-multifuncoes"
PRESSOTERAPIA_MANUAL_FAMILY_SLUG = "pressoterapia-vacuum-drenagem"
HIFU_MANUAL_FAMILY_SLUG = "hifu"
DIODO_LASER_MANUAL_FAMILY_SLUG = "diodo-laser-remocao-tatuagens-pigmentacao"
MANUAL_ONLY_FAMILY_SLUGS = frozenset(
    (MANUAL_ONLY_FAMILY_SLUG, MICRODERMO_MANUAL_FAMILY_SLUG,
     PRESSOTERAPIA_MANUAL_FAMILY_SLUG, HIFU_MANUAL_FAMILY_SLUG,
     DIODO_LASER_MANUAL_FAMILY_SLUG)
)
