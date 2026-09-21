from django.test import SimpleTestCase

from apps.catalog.services.candidate_priority import (
    learned_family_variants,
    priority_for_family,
)
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

    def test_profile_registered_and_preserves_pressotherapy_search_set(self):
        self.assertIs(
            get_family_profile("pressoterapia-vacuum-drenagem"), PRESSOTHERAPY_PROFILE
        )
        self.assertEqual(PRESSOTHERAPY_PROFILE.search_keywords[:12], self.original_keywords)
        self.assertEqual(len(PRESSOTHERAPY_PROFILE.search_keywords), 17)
        self.assertTrue(
            all(
                "vacuum" not in keyword.lower() or "pressotherapy" in keyword.lower()
                for keyword in self.original_keywords
            )
        )

    def test_profile_contains_exact_sanctioned_tecar_keywords(self):
        for keyword in self.tecar_keywords:
            with self.subTest(keyword=keyword):
                self.assertIn(keyword, PRESSOTHERAPY_PROFILE.search_keywords)

    def test_existing_pressotherapy_titles_remain_relevant(self):
        accepted = (
            "Professional Pressotherapy Lymphatic Drainage Machine",
            "Pneumatic Compression Pressotherapy Professional Equipment",
            "Pressotherapy Vacuum Lymphatic Drainage Machine",
        )
        for title in accepted:
            with self.subTest(title=title):
                self.assertEqual(
                    family_candidate_relevance(PRESSOTHERAPY_PROFILE.slug, title),
                    (True, None),
                )

    def test_professional_and_capacitive_resistive_tecar_titles_are_relevant(self):
        accepted = (
            "Professional TECAR Therapy Machine",
            "RF TECAR Therapy Machine Professional",
            "Capacitive Resistive TECAR Therapy Equipment",
            "Capacitive Resistive Radiofrequency Therapy Machine",
            "TECAR Physiotherapy Radiofrequency Machine",
            "Capacitive Resistive Energy Transfer Therapy Machine",
        )
        for title in accepted:
            with self.subTest(title=title):
                self.assertEqual(
                    family_candidate_relevance(PRESSOTHERAPY_PROFILE.slug, title),
                    (True, None),
                )

    def test_generic_rf_without_tecar_context_is_not_relevant(self):
        rejected = (
            "Professional RF Facial Machine",
            "Generic Radiofrequency Facial Beauty Machine",
            "Cavitation RF Vacuum Body Slimming Machine",
            "RF Body Slimming Equipment",
        )
        for title in rejected:
            with self.subTest(title=title):
                self.assertEqual(
                    family_candidate_relevance(PRESSOTHERAPY_PROFILE.slug, title),
                    (False, "IRRELEVANT_FAMILY"),
                )

    def test_obvious_tecar_parts_are_accessories_but_included_electrodes_are_safe(self):
        accessories = (
            "TECAR replacement electrode",
            "TECAR electrode only",
            "TECAR replacement handpiece",
            "TECAR handpiece only",
            "TECAR replacement probe",
            "TECAR probe only",
            "TECAR plate only",
            "TECAR replacement cable",
            "TECAR cable only",
        )
        for title in accessories:
            with self.subTest(title=title):
                self.assertEqual(
                    family_candidate_relevance(PRESSOTHERAPY_PROFILE.slug, title),
                    (False, "ACCESSORY_OR_PART"),
                )
        self.assertEqual(
            family_candidate_relevance(
                PRESSOTHERAPY_PROFILE.slug,
                "Professional TECAR Therapy Machine with electrodes and handpieces included",
            ),
            (True, None),
        )

    def test_tecar_variants_feed_existing_learning_and_priority(self):
        learned = learned_family_variants(
            PRESSOTHERAPY_PROFILE,
            ["Professional TECAR Therapy Machine"],
        )
        self.assertIn("TECAR", learned)
        self.assertIn("TECAR THERAPY", learned)
        learned_score, signals = priority_for_family(
            self.product("Professional TECAR Therapy Machine"),
            PRESSOTHERAPY_PROFILE.slug,
            learned_variants=learned,
        )
        baseline_score = priority_for_family(
            self.product("Professional TECAR Therapy Machine"),
            PRESSOTHERAPY_PROFILE.slug,
        )[0]
        self.assertGreater(learned_score, baseline_score)
        self.assertIn("approved pattern: TECAR", signals)
        self.assertIn("tecar", signals)

    def test_pressotherapy_machine_scores_above_vacuum_only_product(self):
        strong = self.product("Professional Pressotherapy Lymphatic Drainage Machine")
        weak = self.product("Professional Vacuum Body Machine")
        strong_score = priority_for_family(strong, PRESSOTHERAPY_PROFILE.slug)[0]
        weak_score = priority_for_family(weak, PRESSOTHERAPY_PROFILE.slug)[0]
        self.assertGreater(strong_score, weak_score)
