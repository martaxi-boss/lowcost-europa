"""Manually curated storefront categories: only owner-supplied affiliate links.

Keep the singular constant for the original Cavitation-only availability
monitor; use the plural set for shared storefront, queues and maintenance.
"""

MANUAL_ONLY_FAMILY_SLUG = "cavitacao-rf-vacuum-corpo"
MICRODERMO_MANUAL_FAMILY_SLUG = "hydrodermoabrasao-aqua-facial-multifuncoes"
MANUAL_ONLY_FAMILY_SLUGS = frozenset(
    (MANUAL_ONLY_FAMILY_SLUG, MICRODERMO_MANUAL_FAMILY_SLUG)
)
