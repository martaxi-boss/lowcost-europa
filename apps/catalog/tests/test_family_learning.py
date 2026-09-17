from decimal import Decimal

from django.test import SimpleTestCase

from apps.catalog.services.candidate_priority import priority_for_family
from apps.catalog.services.candidate_relevance import is_family_candidate_relevant
from apps.catalog.services.family_profiles import (
    CAVITATION_PROFILE,
    HIFU_PROFILE,
    HYDRODERMO_PROFILE,
    LASER_TATTOO_PROFILE,
)
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

    def test_cavitation_profile_blocks_new_accessory_terms_and_accepts_variants(self):
        for title in (
            "Vacuum therapy cups only",
            "RF machine hose only",
            "Cavitation replacement head only",
            "40K cavitation power supply only",
        ):
            with self.subTest(title=title):
                self.assertFalse(is_family_candidate_relevant("cavitacao-rf-vacuum-corpo", title))
        for title in (
            "3 in 1 cavitation RF vacuum professional machine",
            "4 in 1 cavitation RF vacuum professional machine",
            "7 in 1 cavitation RF vacuum professional machine",
            "8 in 1 cavitation RF vacuum professional machine",
            "Professional electric cupping body therapy machine",
        ):
            with self.subTest(title=title):
                self.assertTrue(is_family_candidate_relevant("cavitacao-rf-vacuum-corpo", title))

    def test_hydrodermo_profile_accepts_family_signals_and_blocks_generic_or_accessories(self):
        family = "hydrodermoabrasao-aqua-facial-multifuncoes"
        positives = (
            "Professional diamond microdermabrasion facial machine",
            "Microdermabrasion beauty salon equipment",
            "Hydrodermabrasion professional facial machine",
            "Hydro facial multifunction beauty salon machine",
            "Aqua peel hydro dermabrasion facial machine",
            "7 in 1 hydrodermabrasion multifunction machine",
        )
        negatives = (
            "replacement diamond tips only",
            "hydro facial serum only",
            "microdermabrasion handle only",
            "aqua peel filter only",
            "generic facial steamer",
            "generic LED facial mask",
            "unrelated body slimming machine",
        )
        for title in positives:
            with self.subTest(title=title):
                self.assertTrue(is_family_candidate_relevant(family, title))
        for title in negatives:
            with self.subTest(title=title):
                self.assertFalse(is_family_candidate_relevant(family, title))

    def test_hydrodermo_profile_is_ready_for_future_discovery(self):
        self.assertEqual(HYDRODERMO_PROFILE.slug, "hydrodermoabrasao-aqua-facial-multifuncoes")
        self.assertEqual(len(HYDRODERMO_PROFILE.search_keywords), 5)
        product = self.product("Professional diamond microdermabrasion facial machine")
        score, signals = priority_for_family(product, HYDRODERMO_PROFILE.slug)
        self.assertGreater(score, 0)
        self.assertIn("diamond microdermabrasion", signals)

    def test_laser_tattoo_profile_accepts_scope_and_blocks_generic_laser(self):
        family = "diodo-laser-remocao-tatuagens-pigmentacao"
        positives = (
            "Professional diode laser hair removal machine",
            "Triple wavelength 755nm 808nm 1064nm diode laser hair removal machine",
            "Alexandrite + Diode + Nd:YAG hair removal system",
            "Q-switched Nd:YAG laser tattoo removal pigmentation machine 532nm 1064nm",
            "Picosecond pico laser tattoo removal pigment machine",
            "Picosure-style picosecond tattoo removal laser machine",
            "Diode laser + picosecond tattoo removal multifunction laser machine",
            "Laser freckle removal pigmentation equipment",
            "Nd:YAG carbon peel pigment removal laser machine",
        )
        negatives = (
            "generic laser beauty machine",
            "laser skin salon machine",
            "LED facial beauty machine",
            "laser handpiece only",
            "replacement laser handle accessory",
            "532nm 1064nm power supply only",
        )
        for title in positives:
            with self.subTest(title=title):
                self.assertTrue(is_family_candidate_relevant(family, title))
        for title in negatives:
            with self.subTest(title=title):
                self.assertFalse(is_family_candidate_relevant(family, title))

    def test_laser_tattoo_profile_variants_and_priority_are_family_specific(self):
        self.assertEqual(LASER_TATTOO_PROFILE.slug, "diodo-laser-remocao-tatuagens-pigmentacao")
        title = "Professional Triple Wave 755nm 808nm 1064nm diode laser hair removal machine"
        product = self.product(title)
        learned = {"TRIPLE WAVE", "755/808/1064", "808NM"}
        score, signals = priority_for_family(
            product, LASER_TATTOO_PROFILE.slug, learned_variants=learned
        )
        self.assertGreater(score, 0)
        self.assertIn("approved pattern: TRIPLE WAVE", signals)
        self.assertIn("diode laser", signals)
        self.assertGreaterEqual(len(LASER_TATTOO_PROFILE.search_keywords), 7)

    def test_laser_tattoo_new_variant_labels_are_detectable(self):
        cases = {
            "Professional picosecond laser tattoo removal machine": "PICOSECOND",
            "Q-switched Nd:YAG tattoo removal machine": "Q-SWITCH ND:YAG",
            "532nm 1064nm Nd:YAG tattoo removal machine": "532/1064",
            "Professional laser tattoo removal machine": "TATTOO REMOVAL",
            "Laser pigmentation removal machine": "PIGMENTATION REMOVAL",
            "Diode laser picosecond tattoo removal machine": "DIODE + PICO",
            "Diode laser Nd:YAG tattoo removal machine": "DIODE + ND:YAG",
            "Multifunction laser tattoo removal machine": "MULTIFUNCTION LASER",
        }
        for title, expected in cases.items():
            labels = {
                label
                for label, pattern in LASER_TATTOO_PROFILE.variant_patterns
                if pattern.search(title)
            }
            with self.subTest(title=title):
                self.assertIn(expected, labels)

    def test_profiles_are_family_specific_and_ready(self):
        self.assertEqual(HIFU_PROFILE.slug, "hifu")
        self.assertEqual(CAVITATION_PROFILE.slug, "cavitacao-rf-vacuum-corpo")
        self.assertEqual(len(CAVITATION_PROFILE.search_keywords), 2)
