import importlib

from django.apps import apps
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.catalog.models import (
    Offer,
    OfferClick,
    OfferFamilyPlacement,
    OfferObservation,
    ProductFamily,
)


class OfferFamilyPlacementTests(TestCase):
    def setUp(self):
        self.family_a = ProductFamily.objects.create(name="Family A", slug="family-a")
        self.family_b = ProductFamily.objects.create(name="Family B", slug="family-b")
        self.offer_a = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="placement-a",
        )
        self.offer_b = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="placement-b",
        )

    def test_same_offer_can_be_placed_in_two_families(self):
        OfferFamilyPlacement.objects.create(offer=self.offer_a, product_family=self.family_a)
        OfferFamilyPlacement.objects.create(offer=self.offer_a, product_family=self.family_b)
        self.assertEqual(self.offer_a.family_placements.count(), 2)

    def test_same_offer_cannot_have_duplicate_placement_in_family(self):
        OfferFamilyPlacement.objects.create(offer=self.offer_a, product_family=self.family_a)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OfferFamilyPlacement.objects.create(
                    offer=self.offer_a, product_family=self.family_a
                )

    def test_selection_position_accepts_one_through_five(self):
        for position in range(1, 6):
            family = ProductFamily.objects.create(
                name=f"Position {position}", slug=f"position-{position}"
            )
            placement = OfferFamilyPlacement.objects.create(
                offer=self.offer_a,
                product_family=family,
                selection_position=position,
            )
            self.assertEqual(placement.selection_position, position)

    def test_selection_position_rejects_zero(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OfferFamilyPlacement.objects.create(
                    offer=self.offer_a,
                    product_family=self.family_a,
                    selection_position=0,
                )

    def test_selection_position_rejects_above_five(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OfferFamilyPlacement.objects.create(
                    offer=self.offer_a,
                    product_family=self.family_a,
                    selection_position=6,
                )

    def test_two_offers_cannot_share_selection_position_in_family(self):
        OfferFamilyPlacement.objects.create(
            offer=self.offer_a,
            product_family=self.family_a,
            selection_position=1,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OfferFamilyPlacement.objects.create(
                    offer=self.offer_b,
                    product_family=self.family_a,
                    selection_position=1,
                )

    def test_null_selection_position_can_repeat_in_family(self):
        OfferFamilyPlacement.objects.create(
            offer=self.offer_a, product_family=self.family_a, selection_position=None
        )
        OfferFamilyPlacement.objects.create(
            offer=self.offer_b, product_family=self.family_a, selection_position=None
        )
        self.assertEqual(
            OfferFamilyPlacement.objects.filter(
                product_family=self.family_a, selection_position=None
            ).count(),
            2,
        )

    def test_equipment_type_accepts_authorized_choices(self):
        for index, equipment_type in enumerate(Offer.EquipmentType.values, start=1):
            offer = Offer.objects.create(
                source=Offer.Source.ALIEXPRESS,
                external_product_id=f"equipment-{index}",
                equipment_type=equipment_type,
            )
            self.assertEqual(offer.equipment_type, equipment_type)

    def test_invalid_equipment_type_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Offer.objects.create(
                    source=Offer.Source.ALIEXPRESS,
                    external_product_id="equipment-invalid",
                    equipment_type="INVALID",
                )


class PlacementBackfillTests(TestCase):
    def test_backfill_creates_six_placements_without_touching_history(self):
        families = [
            ProductFamily.objects.create(name=f"Family {i}", slug=f"backfill-{i}")
            for i in range(1, 6)
        ]
        offers = []
        for index in range(6):
            family = families[0] if index < 2 else families[index - 1]
            offers.append(
                Offer.objects.create(
                    source=Offer.Source.ALIEXPRESS,
                    external_product_id=f"backfill-offer-{index}",
                    product_family=family,
                    is_primary=index != 1,
                )
            )
        OfferObservation.objects.create(offer=offers[0])
        OfferClick.objects.create(offer=offers[0])
        before = (OfferObservation.objects.count(), OfferClick.objects.count())
        migration = importlib.import_module(
            "apps.catalog.migrations.0006_backfill_offer_family_placements"
        )
        migration.backfill_offer_family_placements(apps, None)

        placements = OfferFamilyPlacement.objects.order_by("offer_id")
        self.assertEqual(placements.count(), 6)
        self.assertEqual(
            list(placements.values_list("selection_position", flat=True)),
            [1, None, 1, 1, 1, 1],
        )
        self.assertEqual(
            list(placements.values_list("offer_id", "product_family_id")),
            [(offer.id, offer.product_family_id) for offer in offers],
        )
        self.assertEqual((OfferObservation.objects.count(), OfferClick.objects.count()), before)
