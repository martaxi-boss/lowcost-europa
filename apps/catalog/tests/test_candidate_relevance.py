from django.test import SimpleTestCase

from apps.catalog.services.candidate_relevance import is_family_candidate_relevant


class HifuCandidateRelevanceTests(SimpleTestCase):
    def test_anlan_ems_like_title_is_blocked(self):
        title = "ANLAN EMS Facial Massager Face Lifting LED Photon Deep Cleaning"
        self.assertFalse(is_family_candidate_relevant("hifu", title))

    def test_hifu_title_passes(self):
        self.assertTrue(is_family_candidate_relevant("hifu", "Professional 22D HIFU Machine"))

    def test_hifu_combo_passes(self):
        title = "HIFU 3 in 1 RF EMS professional beauty machine"
        self.assertTrue(is_family_candidate_relevant("hifu", title))

    def test_cartridge_only_is_blocked_even_with_hifu(self):
        self.assertFalse(
            is_family_candidate_relevant("hifu", "HIFU replacement cartridge only 4.5mm")
        )

    def test_generic_face_lifting_without_hifu_is_blocked(self):
        self.assertFalse(
            is_family_candidate_relevant("hifu", "Face lifting anti-aging slimming beauty device")
        )

    def test_high_intensity_focused_ultrasound_passes(self):
        self.assertTrue(
            is_family_candidate_relevant(
                "hifu", "High Intensity Focused Ultrasound professional machine"
            )
        )


class PressotherapyCandidateRelevanceTests(SimpleTestCase):
    slug = "pressoterapia-vacuum-drenagem"

    def test_positive_core_titles_pass(self):
        titles = (
            "Professional Pressotherapy Lymphatic Drainage Machine",
            "Pressotherapy Air Compression Therapy Beauty Salon Equipment",
            "Professional Pneumatic Compression Lymphatic Drainage Machine",
            "Air Pressure Pressotherapy Body Drainage Equipment",
            "Professional Pressotherapy Vacuum Lymphatic Drainage Machine",
        )
        for title in titles:
            with self.subTest(title=title):
                self.assertTrue(is_family_candidate_relevant(self.slug, title))

    def test_machine_with_boots_is_not_treated_as_boots_only(self):
        self.assertTrue(
            is_family_candidate_relevant(
                self.slug,
                "Professional Pressotherapy Lymphatic Drainage Machine with Boots and Cuffs",
            )
        )

    def test_accessories_are_blocked(self):
        titles = (
            "Replacement Pressotherapy Boots Only",
            "Pressotherapy Hose Only",
            "Compression Pants Only",
            "Replacement Air Hose For Pressotherapy Machine",
            "Pressotherapy Replacement Boots",
        )
        for title in titles:
            with self.subTest(title=title):
                self.assertFalse(is_family_candidate_relevant(self.slug, title))

    def test_wrong_family_and_consumer_titles_are_blocked(self):
        titles = (
            "Vacuum RF Cavitation Body Slimming Machine",
            "Vacuum Butt Lifting Machine",
            "Home Leg Air Compression Massager",
            "Compression Socks",
            "Sports Recovery Boots Air Compression",
            "HIFU Machine",
            "RF Facial Machine",
            "Ultrasound Cavitation Machine",
        )
        for title in titles:
            with self.subTest(title=title):
                self.assertFalse(is_family_candidate_relevant(self.slug, title))


class MicrocurrentUltrasoundCandidateRelevanceTests(SimpleTestCase):
    slug = "microcorrente-ultrassons"

    def test_positive_core_titles_pass(self):
        titles = (
            "Professional Microcurrent Facial Lifting Machine",
            "Microcurrent Beauty Salon Skin Care Equipment",
            "Professional Ultrasonic Facial Beauty Machine",
            "Ultrasound Facial Treatment Salon Equipment",
            "Professional Microcurrent Ultrasound Facial Machine",
            "Microcurrent Ultrasonic Multifunction Beauty Equipment",
        )
        for title in titles:
            with self.subTest(title=title):
                self.assertTrue(is_family_candidate_relevant(self.slug, title))

    def test_complete_machine_with_probes_is_allowed(self):
        self.assertTrue(
            is_family_candidate_relevant(
                self.slug,
                "Professional Microcurrent Facial Machine with Probes and Electrodes",
            )
        )

    def test_accessories_are_blocked(self):
        titles = (
            "Microcurrent Probe Only",
            "Replacement Microcurrent Handle",
            "Microcurrent Electrode Pads Only",
            "Ultrasound Gel",
            "Replacement Ultrasound Transducer Only",
        )
        for title in titles:
            with self.subTest(title=title):
                self.assertFalse(is_family_candidate_relevant(self.slug, title))

    def test_wrong_family_medical_and_consumer_titles_are_blocked(self):
        titles = (
            "7D HIFU Beauty Machine",
            "22D MAX HIFU Machine",
            "Ultrasonic Cavitation RF Vacuum Body Slimming Machine",
            "Pregnancy Ultrasound Scanner",
            "Medical Diagnostic Ultrasound Machine",
            "Ultrasonic Cleaner",
            "Ultrasonic Tooth Cleaner",
            "Home Ultrasonic Massager",
            "Pressotherapy Machine",
            "Diode Laser Machine",
        )
        for title in titles:
            with self.subTest(title=title):
                self.assertFalse(is_family_candidate_relevant(self.slug, title))
