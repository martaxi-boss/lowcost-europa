import importlib

from django.apps import apps
from django.core.management.color import no_style
from django.db import connection
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import (
    Offer,
    OfferClick,
    OfferFamilyPlacement,
    OfferObservation,
    ProductFamily,
)

EXPECTED_ACTIVE = [
    (1, "Cavitação + RF + Vacuum (corpo)", "cavitacao-rf-vacuum-corpo"),
    (
        2,
        "Hydrodermoabrasão / Aqua Facial / Multifunções faciais",
        "hydrodermoabrasao-aqua-facial-multifuncoes",
    ),
    (3, "Radiofrequência facial", "radiofrequencia-facial"),
    (4, "Pressoterapia / Vacuum / Drenagem", "pressoterapia-vacuum-drenagem"),
    (5, "Microcorrente / Ultrassons", "microcorrente-ultrassons"),
    (6, "HIFU", "hifu"),
    (7, "Depilação Laser Triple Wave", "depilacao-laser-triple-wave"),
    (8, "Remoção de tatuagens / pigmentação", "remocao-tatuagens-pigmentacao"),
]


class EightFamilyTaxonomyMigrationTests(TestCase):
    def setUp(self):
        families = {
            1: ("Máquinas HIFU 7D", "maquinas-hifu-7d"),
            2: ("Máquinas HIFU 22D MAX", "maquinas-hifu-22d-max"),
            3: ("Máquinas Cavitation + RF Body Shaping", "maquinas-cavitation-rf-body-shaping"),
            4: ("Máquinas Diode Laser Hair Removal", "maquinas-diode-laser-hair-removal"),
            5: ("Máquinas Hydro Dermabrasion / Aqua Peel", "maquinas-hydro-dermabrasion-aqua-peel"),
        }
        for pk, (name, slug) in families.items():
            ProductFamily.objects.create(pk=pk, name=name, slug=slug)
        with connection.cursor() as cursor:
            for sql in connection.ops.sequence_reset_sql(no_style(), [ProductFamily]):
                cursor.execute(sql)

        offer_rows = (
            (51, "1005012522304882", 1, True),
            (52, "1005013116584854", 1, False),
            (53, "1005013002556821", 2, True),
            (54, "1005012828137048", 3, True),
            (55, "1005012991431121", 4, True),
            (56, "1005012839981986", 5, True),
        )
        for pk, external_id, family_id, is_primary in offer_rows:
            Offer.objects.create(
                pk=pk,
                source=Offer.Source.ALIEXPRESS,
                external_product_id=external_id,
                product_family_id=family_id,
                is_primary=is_primary,
            )

        placement_rows = (
            (51, 1, 1),
            (52, 1, None),
            (53, 2, 1),
            (54, 3, 1),
            (55, 4, 1),
            (56, 5, 1),
        )
        for offer_id, family_id, position in placement_rows:
            OfferFamilyPlacement.objects.create(
                offer_id=offer_id,
                product_family_id=family_id,
                selection_position=position,
            )

        for index in range(15):
            OfferObservation.objects.create(offer_id=51 + (index % 6))
        OfferClick.objects.create(offer_id=51)
        OfferClick.objects.create(offer_id=54)

        migration = importlib.import_module("apps.catalog.migrations.0008_eight_family_taxonomy")
        migration.apply_eight_family_taxonomy(apps, None)

    def test_exact_active_taxonomy_names_slugs_and_display_order(self):
        active = list(
            ProductFamily.objects.exclude(status=ProductFamily.Status.RETIRED)
            .order_by("display_order")
            .values_list("display_order", "name", "slug")
        )
        self.assertEqual(active, EXPECTED_ACTIVE)
        self.assertEqual(len(active), 8)

    def test_hifu_is_single_active_family_and_historical_family_is_retired(self):
        self.assertEqual(
            ProductFamily.objects.exclude(status=ProductFamily.Status.RETIRED)
            .filter(name="HIFU", slug="hifu")
            .count(),
            1,
        )
        historical = ProductFamily.objects.get(pk=2)
        self.assertEqual(historical.name, "Máquinas HIFU 22D MAX")
        self.assertEqual(historical.status, ProductFamily.Status.RETIRED)
        self.assertEqual(historical.display_order, 99)

    def test_hifu_offers_and_placements_are_consolidated(self):
        hifu = ProductFamily.objects.get(slug="hifu")
        offers = {
            offer.pk: offer for offer in Offer.objects.filter(pk__in=[51, 52, 53]).order_by("pk")
        }
        self.assertEqual(offers[51].product_family_id, hifu.pk)
        self.assertEqual(offers[52].product_family_id, hifu.pk)
        self.assertEqual(offers[53].product_family_id, hifu.pk)
        self.assertTrue(offers[51].is_primary)
        self.assertFalse(offers[53].is_primary)

        placements = {
            placement.offer_id: placement.selection_position
            for placement in OfferFamilyPlacement.objects.filter(product_family=hifu)
        }
        self.assertEqual(placements, {51: 1, 52: None, 53: 2})

    def test_counts_history_and_equipment_types_are_preserved(self):
        self.assertEqual(ProductFamily.objects.count(), 9)
        self.assertEqual(
            ProductFamily.objects.filter(status=ProductFamily.Status.RETIRED).count(), 1
        )
        self.assertEqual(Offer.objects.count(), 6)
        self.assertEqual(OfferObservation.objects.count(), 15)
        self.assertEqual(OfferClick.objects.count(), 2)
        self.assertEqual(OfferFamilyPlacement.objects.count(), 6)
        self.assertEqual(
            Offer.objects.filter(equipment_type=Offer.EquipmentType.UNKNOWN).count(), 6
        )

    def test_no_duplicate_placements_or_selection_positions(self):
        pairs = list(OfferFamilyPlacement.objects.values_list("offer_id", "product_family_id"))
        self.assertEqual(len(pairs), len(set(pairs)))
        positioned = list(
            OfferFamilyPlacement.objects.exclude(selection_position=None).values_list(
                "product_family_id", "selection_position"
            )
        )
        self.assertEqual(len(positioned), len(set(positioned)))

    def test_four_new_families_are_empty_and_renderable(self):
        new_slugs = (
            "radiofrequencia-facial",
            "pressoterapia-vacuum-drenagem",
            "microcorrente-ultrassons",
            "remocao-tatuagens-pigmentacao",
        )
        for slug in new_slugs:
            with self.subTest(slug=slug):
                family = ProductFamily.objects.get(slug=slug)
                self.assertEqual(family.offers.count(), 0)
                self.assertEqual(family.offer_placements.count(), 0)
                response = self.client.get(reverse("storefront:product-family-detail", args=[slug]))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, family.name)

    def test_homepage_uses_authorized_eight_family_factual_copy(self):
        response = self.client.get(reverse("storefront:home"))
        self.assertContains(response, "Oito famílias iniciais")
        self.assertNotContains(response, "Cinco famílias reais")


class EightFamilyTaxonomyBaselineSafetyTests(TestCase):
    def test_nonempty_unexpected_baseline_fails_loud(self):
        ProductFamily.objects.create(name="Unexpected", slug="unexpected")
        migration = importlib.import_module("apps.catalog.migrations.0008_eight_family_taxonomy")
        with self.assertRaisesRegex(RuntimeError, "baseline mismatch"):
            migration.apply_eight_family_taxonomy(apps, None)
