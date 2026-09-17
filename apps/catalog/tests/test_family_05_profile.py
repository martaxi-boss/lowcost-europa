from django.test import SimpleTestCase

from apps.catalog.services.candidate_priority import priority_for_family
from apps.catalog.services.family_profiles import (
    MICROCURRENT_ULTRASOUND_PROFILE,
    get_family_profile,
)
from apps.integrations.aliexpress.types import AliExpressProduct


class MicrocurrentUltrasoundProfileTests(SimpleTestCase):
    def test_profile_registered_with_expected_slug_and_keywords(self):
        self.assertIs(
            get_family_profile("microcorrente-ultrassons"),
            MICROCURRENT_ULTRASOUND_PROFILE,
        )
        self.assertEqual(len(MICROCURRENT_ULTRASOUND_PROFILE.search_keywords), 15)
        forbidden = ("hifu", "cavitation", "pressotherapy", "laser")
        self.assertTrue(
            all(
                not any(term in keyword.lower() for term in forbidden)
                for keyword in MICROCURRENT_ULTRASOUND_PROFILE.search_keywords
            )
        )

    def test_microcurrent_professional_machine_scores_above_generic_product(self):
        strong = AliExpressProduct(
            product_id="p",
            title="Professional Microcurrent Facial Lifting Machine",
            product_url="https://example.com/p",
        )
        weak = AliExpressProduct(
            product_id="g",
            title="Professional Facial Beauty Machine",
            product_url="https://example.com/g",
        )
        strong_score = priority_for_family(
            strong, MICROCURRENT_ULTRASOUND_PROFILE.slug
        )[0]
        weak_score = priority_for_family(weak, MICROCURRENT_ULTRASOUND_PROFILE.slug)[0]
        self.assertGreater(strong_score, weak_score)
