from decimal import Decimal

from django.test import SimpleTestCase

from apps.catalog.services.candidate_priority import priority_for_family
from apps.catalog.services.candidate_relevance import is_family_candidate_relevant
from apps.catalog.services.family_profiles import CAVITATION_PROFILE, HIFU_PROFILE
from apps.integrations.aliexpress.types import AliExpressProduct


class FamilyLearningTests(SimpleTestCase):
    def product(self, title, *, country=None):
        return AliExpressProduct(
            product_id="x",
            title=title,
            sales_count=10,
            evaluation_rate_percent=Decimal("98"),
            commission_rate=Decimal("7"),
            destination_country=country,
        )

    def test_country_does_not_affect_score(self):
        pl = self.product("Professional 22D MAX HIFU salon machine", country="PL")
        es = self.product("Professional 22D MAX HIFU salon machine", country="ES")
        self.assertEqual(
            priority_for_family(pl, "hifu", learned_variants={"22D MAX"})[0],
            priority_for_family(es, "hifu", learned_variants={"22D MAX"})[0],
        )

    def test_hifu_learning_does_not_contaminate_cavitation(self):
        product = self.product("Professional 22D MAX HIFU salon machine")
        hifu_score = priority_for_family(product, "hifu", learned_variants={"22D MAX"})[0]
        cav_score = priority_for_family(
            product, "cavitacao-rf-vacuum-corpo", learned_variants={"22D MAX"}
        )[0]
        self.assertGreater(hifu_score, cav_score)

    def test_exploration_variant_without_learned_pattern_can_still_score(self):
        product = self.product("Professional HIFU equipment for salon")
        score, signals = priority_for_family(product, "hifu", learned_variants=set())
        self.assertGreater(score, 0)
        self.assertIn("professional", signals)

    def test_cavitation_profile_accepts_real_combo_and_blocks_accessory(self):
        self.assertTrue(
            is_family_candidate_relevant(
                "cavitacao-rf-vacuum-corpo",
                "6 in 1 ultrasonic cavitation RF vacuum body slimming machine",
            )
        )
        self.assertFalse(
            is_family_candidate_relevant(
                "cavitacao-rf-vacuum-corpo", "Cavitation replacement handles only accessory"
            )
        )
        self.assertFalse(
            is_family_candidate_relevant(
                "cavitacao-rf-vacuum-corpo",
                "Plastic Stowage Plate Stand Support Accesories For 40K Cavitation Machine",
            )
        )

    def test_profiles_are_family_specific_and_ready(self):
        self.assertEqual(HIFU_PROFILE.slug, "hifu")
        self.assertEqual(CAVITATION_PROFILE.slug, "cavitacao-rf-vacuum-corpo")
        self.assertEqual(len(CAVITATION_PROFILE.search_keywords), 2)
