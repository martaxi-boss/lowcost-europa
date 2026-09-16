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
