from django.test import SimpleTestCase

from apps.catalog.services.candidate_priority import priority_for_family
from apps.catalog.services.family_profiles import PRESSOTHERAPY_PROFILE, get_family_profile
from apps.integrations.aliexpress.types import AliExpressProduct


class PressotherapyProfileTests(SimpleTestCase):
    def test_profile_registered_with_expected_slug_and_keywords(self):
        self.assertIs(
            get_family_profile("pressoterapia-vacuum-drenagem"), PRESSOTHERAPY_PROFILE
        )
        self.assertEqual(len(PRESSOTHERAPY_PROFILE.search_keywords), 12)
        self.assertTrue(
            all(
                "vacuum" not in keyword.lower() or "pressotherapy" in keyword.lower()
                for keyword in PRESSOTHERAPY_PROFILE.search_keywords
            )
        )

    def test_pressotherapy_machine_scores_above_vacuum_only_product(self):
        strong = AliExpressProduct(
            product_id="p",
            title="Professional Pressotherapy Lymphatic Drainage Machine",
            product_url="https://example.com/p",
        )
        weak = AliExpressProduct(
            product_id="v",
            title="Professional Vacuum Body Machine",
            product_url="https://example.com/v",
        )
        strong_score = priority_for_family(strong, PRESSOTHERAPY_PROFILE.slug)[0]
        weak_score = priority_for_family(weak, PRESSOTHERAPY_PROFILE.slug)[0]
        self.assertGreater(strong_score, weak_score)
