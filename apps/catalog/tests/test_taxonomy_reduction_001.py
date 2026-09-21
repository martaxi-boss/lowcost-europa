import importlib

from django.apps import apps
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Offer, OfferCandidate, ProductFamily


class TaxonomyReduction001Tests(TestCase):
    def setUp(self):
        rows = (
            (3, 1, "Cavitação + RF + Vacuum (corpo)", "cavitacao-rf-vacuum-corpo"),
            (
                5,
                2,
                "Microdermoabrasão / Hidrodermoabrasão / Multifunções faciais",
                "hydrodermoabrasao-aqua-facial-multifuncoes",
            ),
            (6, 3, "Radiofrequência facial", "radiofrequencia-facial"),
            (7, 4, "Pressoterapia / Vacuum / Drenagem", "pressoterapia-vacuum-drenagem"),
            (8, 5, "Microcorrente / Ultrassons", "microcorrente-ultrassons"),
            (1, 6, "HIFU", "hifu"),
            (
                4,
                7,
                "Diodo Laser / Remoção de tatuagens / Pigmentação",
                "diodo-laser-remocao-tatuagens-pigmentacao",
            ),
        )
        for pk, order, name, slug in rows:
            ProductFamily.objects.create(pk=pk, display_order=order, name=name, slug=slug)
        self.rf = ProductFamily.objects.get(slug="radiofrequencia-facial")
        self.micro = ProductFamily.objects.get(slug="microcorrente-ultrassons")
        OfferCandidate.objects.create(
            product_family=self.rf,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="history-rf",
            title="Historical RF candidate",
        )
        OfferCandidate.objects.create(
            product_family=self.micro,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="history-micro",
            title="Historical microcurrent candidate",
        )
        migration = importlib.import_module(
            "apps.catalog.migrations.0017_taxonomy_reduction_menu_realignment"
        )
        migration.apply_taxonomy_reduction(apps, None)
        rename_migration = importlib.import_module(
            "apps.catalog.migrations.0018_rename_family_03_rf_tecar"
        )
        rename_migration.rename_family(apps, None)

    def test_exact_surviving_operational_taxonomy(self):
        active = list(
            ProductFamily.objects.exclude(status=ProductFamily.Status.RETIRED)
            .order_by("display_order")
            .values_list("display_order", "name", "slug", "pk")
        )
        self.assertEqual(
            active,
            [
                (1, "Cavitação + RF + Vacuum", "cavitacao-rf-vacuum-corpo", 3),
                (
                    2,
                    "Microdermoabrasão / Hidrodermoabrasão / Multifunções faciais",
                    "hydrodermoabrasao-aqua-facial-multifuncoes",
                    5,
                ),
                (3, "Pressoterapia / RF Tecar", "pressoterapia-vacuum-drenagem", 7),
                (4, "HIFU", "hifu", 1),
                (
                    5,
                    "Diodo Laser / Remoção de tatuagens / Pigmentação",
                    "diodo-laser-remocao-tatuagens-pigmentacao",
                    4,
                ),
            ],
        )

    def test_removed_families_are_retired_not_deleted_and_history_remains(self):
        self.rf.refresh_from_db()
        self.micro.refresh_from_db()
        self.assertEqual(self.rf.status, ProductFamily.Status.RETIRED)
        self.assertEqual(self.micro.status, ProductFamily.Status.RETIRED)
        self.assertTrue(self.rf.candidates.filter(external_product_id="history-rf").exists())
        self.assertTrue(self.micro.candidates.filter(external_product_id="history-micro").exists())

    def test_retired_families_do_not_appear_on_homepage(self):
        response = self.client.get(reverse("storefront:home"))
        self.assertNotContains(response, "Radiofrequência facial")
        self.assertNotContains(response, "Microcorrente / Ultrassons")
        self.assertNotContains(response, "5 categorias")
        self.assertContains(response, "Cavitação + RF + Vacuum")
        self.assertContains(response, "Pressoterapia / RF Tecar")
        self.assertNotContains(response, "Pressoterapia / Drenagem")
