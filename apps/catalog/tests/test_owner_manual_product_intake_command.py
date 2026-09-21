from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.catalog.models import Offer, OfferCandidate, ProductFamily
from apps.catalog.services.manual_candidate_intake import ManualCandidateIntakeResult


class OwnerManualProductIntakeCommandTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(
            name="Pressoterapia / RF Tecar",
            slug="pressoterapia-vacuum-drenagem",
        )

    @patch(
        "apps.catalog.management.commands.owner_manual_product_intake."
        "intake_manual_aliexpress_candidate"
    )
    def test_command_uses_separate_manual_intake_path(self, intake):
        candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="1005001234567890",
            status=OfferCandidate.Status.PENDING,
        )
        intake.return_value = ManualCandidateIntakeResult(
            outcome="CREATED",
            external_product_id=candidate.external_product_id,
            candidate=candidate,
        )

        call_command(
            "owner_manual_product_intake",
            "https://s.click.aliexpress.com/e/_Example",
            family=self.family.slug,
        )

        intake.assert_called_once_with(
            url="https://s.click.aliexpress.com/e/_Example",
            family=self.family,
        )

    def test_unknown_family_fails_without_creating_data(self):
        with self.assertRaises(CommandError):
            call_command(
                "owner_manual_product_intake",
                "https://s.click.aliexpress.com/e/_Example",
                family="missing-family",
            )

        self.assertEqual(OfferCandidate.objects.count(), 0)
        self.assertEqual(Offer.objects.count(), 0)
