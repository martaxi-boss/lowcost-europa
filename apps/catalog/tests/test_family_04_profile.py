from django.test import SimpleTestCase

from apps.catalog.services.candidate_priority import priority_for_family
from apps.catalog.services.candidate_relevance import family_candidate_relevance
from apps.catalog.services.family_profiles import PRESSOTHERAPY_PROFILE, get_family_profile
from apps.integrations.aliexpress.types import AliExpressProduct


class PressotherapyProfileTests(SimpleTestCase):
    original_keywords = (
        "professional pressotherapy lymphatic drainage machine",
        "pressotherapy air compression therapy professional machine",
        "professional lymphatic drainage pressotherapy equipment",
        "air compression lymphatic drainage beauty salon machine",
        "pneumatic compression pressotherapy professional equipment",
        "pressotherapy body drainage professional machine",
        "professional pressotherapy beauty salon machine",
        "lymphatic drainage air pressure therapy machine",
        "pressotherapy compression therapy salon equipment",
        "pressotherapy vacuum lymphatic drainage machine",
        "professional pressotherapy vacuum drainage equipment",
        "air pressure pressotherapy lymphatic drainage equipment",
    )
    tecar_keywords = (
        "professional TECAR therapy machine",
        "RF TECAR therapy machine professional",
        "capacitive resistive TECAR therapy machine",
        "capacitive resistive radiofrequency therapy machine",
        "TECAR physiotherapy radiofrequency machine",
    )

    def product(self, title):
        return AliExpressProduct(
            product_id="p",
            title=title,
            product_url="https://example.com/p",
        )

    def test_profile_registered_with_original_pressotherapy_and_five_tecar_searches(self):
        self.assertIs(
            get_family_profile("pressoterapia-vacuum-drenagem"), PRESSOTHERAPY_PROFILE
        )
        self.assertEqual(PRESSOTHERAPY_PROFILE.search_keywords[:12], self.original_keywords)
        self.assertEqual(PRESSOTHERAPY_PROFILE.search_keywords[12:], self.tecar_keywords)
        self.assertEqual(len(PRESSOTHERAPY_PROFILE.search_keywords), 17)

    def test_existing_pressotherapy_titles_remain_relevant(self):
        for title in (
            "Professional Pressotherapy Lymphatic Drainage Machine",
            "Pneumatic Compression Pressotherapy Professional Equipment",
            "Pressotherapy Vacuum Lymphatic Drainage Machine",
        ):
            with self.subTest(title=title):
                self.assertEqual(
                    family_candidate_relevance(PRESSOTHERAPY_PROFILE.slug, title),
                    (True, None),
                )

    def test_minimal_tecar_relevance_accepts_tecar_and_capacitive_resistive_context(self):
        for title in (
            "Professional TECAR Therapy Machine",
            "RF TECAR Therapy Machine Professional",
            "Capacitive Resistive TECAR Therapy Equipment",
            "Capacitive Resistive Radiofrequency Therapy Machine",
            "TECAR Physiotherapy Radiofrequency Machine",
        ):
            with self.subTest(title=title):
                self.assertEqual(
                    family_candidate_relevance(PRESSOTHERAPY_PROFILE.slug, title),
                    (True, None),
                )

    def test_generic_rf_without_tecar_context_is_not_relevant(self):
        for title in (
            "Professional RF Facial Machine",
            "Generic Radiofrequency Facial Beauty Machine",
            "Cavitation RF Vacuum Body Slimming Machine",
            "RF Body Slimming Equipment",
        ):
            with self.subTest(title=title):
                self.assertEqual(
                    family_candidate_relevance(PRESSOTHERAPY_PROFILE.slug, title),
                    (False, "IRRELEVANT_FAMILY"),
                )

    def test_pressotherapy_machine_scores_above_vacuum_only_product(self):
        strong = self.product("Professional Pressotherapy Lymphatic Drainage Machine")
        weak = self.product("Professional Vacuum Body Machine")
        strong_score = priority_for_family(strong, PRESSOTHERAPY_PROFILE.slug)[0]
        weak_score = priority_for_family(weak, PRESSOTHERAPY_PROFILE.slug)[0]
        self.assertGreater(strong_score, weak_score)
