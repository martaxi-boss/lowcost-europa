import importlib

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import (
    CandidateDecision,
    Offer,
    OfferCandidate,
    OfferClick,
    OfferFamilyPlacement,
    OfferObservation,
    ProductFamily,
)
from apps.catalog.services.candidate_approval import CandidateApprovalError, approve_candidate
from apps.catalog.services.candidate_discovery import discover_family_candidates
from apps.catalog.services.candidate_move import CandidateMoveError, move_candidate_to_family


class TaxonomyConsolidation007Tests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="taxonomy-staff", password="x", is_staff=True
        )

    def test_data_migration_consolidates_relations_and_conflicts_defensively(self):
        survivor = ProductFamily.objects.create(
            name="Depilação Laser Triple Wave", slug="depilacao-laser-triple-wave", display_order=7
        )
        retired = ProductFamily.objects.create(
            name="Remoção de tatuagens / pigmentação",
            slug="remocao-tatuagens-pigmentacao",
            display_order=8,
        )
        survivor_primary = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="survivor-primary",
            product_family=survivor,
            is_primary=True,
        )
        OfferFamilyPlacement.objects.create(
            offer=survivor_primary, product_family=survivor, selection_position=1
        )
        moved_offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="moved-primary",
            product_family=retired,
            is_primary=True,
        )
        moved_placement = OfferFamilyPlacement.objects.create(
            offer=moved_offer, product_family=retired, selection_position=1, display_order=9
        )
        observation = OfferObservation.objects.create(offer=moved_offer)
        click = OfferClick.objects.create(offer=moved_offer)
        candidate = OfferCandidate.objects.create(
            product_family=retired,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="candidate-08",
            status=OfferCandidate.Status.APPROVED,
            approved_offer=moved_offer,
        )
        decision = CandidateDecision.objects.create(
            candidate=candidate,
            decision=CandidateDecision.Decision.APPROVE,
            decided_by=self.user,
        )

        migration = importlib.import_module(
            "apps.catalog.migrations.0014_consolidate_laser_tattoo_taxonomy"
        )
        migration.consolidate_taxonomy(django_apps, None)

        survivor.refresh_from_db()
        retired.refresh_from_db()
        moved_offer.refresh_from_db()
        moved_placement.refresh_from_db()
        candidate.refresh_from_db()
        self.assertEqual(survivor.name, "Diodo Laser / Remoção de tatuagens / Pigmentação")
        self.assertEqual(survivor.slug, "diodo-laser-remocao-tatuagens-pigmentacao")
        self.assertEqual(survivor.display_order, 7)
        self.assertEqual(retired.status, ProductFamily.Status.RETIRED)
        self.assertEqual(candidate.product_family_id, survivor.pk)
        self.assertEqual(candidate.approved_offer_id, moved_offer.pk)
        self.assertTrue(
            CandidateDecision.objects.filter(pk=decision.pk, candidate=candidate).exists()
        )
        self.assertEqual(moved_offer.product_family_id, survivor.pk)
        self.assertFalse(moved_offer.is_primary)
        self.assertEqual(moved_placement.product_family_id, survivor.pk)
        self.assertIsNone(moved_placement.selection_position)
        self.assertEqual(moved_placement.display_order, 9)
        self.assertTrue(
            OfferObservation.objects.filter(pk=observation.pk, offer=moved_offer).exists()
        )
        self.assertTrue(OfferClick.objects.filter(pk=click.pk, offer=moved_offer).exists())
        self.assertTrue(Offer.objects.get(pk=survivor_primary.pk).is_primary)

    def test_legacy_storefront_urls_redirect_to_surviving_slug(self):
        ProductFamily.objects.create(
            name="Diodo Laser / Remoção de tatuagens / Pigmentação",
            slug="diodo-laser-remocao-tatuagens-pigmentacao",
            display_order=7,
        )
        destination = reverse(
            "storefront:product-family-detail",
            kwargs={"slug": "diodo-laser-remocao-tatuagens-pigmentacao"},
        )
        for old_slug in ("depilacao-laser-triple-wave", "remocao-tatuagens-pigmentacao"):
            response = self.client.get(
                reverse("storefront:product-family-detail", kwargs={"slug": old_slug})
            )
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, destination)

    def test_retired_family_cannot_receive_discovery_approval_or_move(self):
        active = ProductFamily.objects.create(name="Active", slug="active")
        retired = ProductFamily.objects.create(
            name="Retired", slug="retired", status=ProductFamily.Status.RETIRED
        )
        candidate = OfferCandidate.objects.create(
            product_family=retired,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="retired-candidate",
        )
        with self.assertRaisesMessage(ValueError, "Retired family cannot receive discovery"):
            discover_family_candidates(retired, "laser", client=object())
        with self.assertRaisesMessage(
            CandidateApprovalError, "Retired family cannot receive approvals"
        ):
            approve_candidate(candidate, user=self.user, ship_from_country="PL")
        movable = OfferCandidate.objects.create(
            product_family=active,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="movable",
        )
        with self.assertRaisesMessage(
            CandidateMoveError, "Retired family cannot receive candidates"
        ):
            move_candidate_to_family(movable, target_family=retired, user=self.user)
        with self.assertRaisesMessage(CommandError, "Retired family cannot receive discovery"):
            call_command(
                "discover_family_candidates",
                family=retired.slug,
                keyword="laser",
                limit=1,
                max_details=0,
            )
