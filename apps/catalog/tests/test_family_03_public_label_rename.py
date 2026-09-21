import importlib

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Offer, OfferCandidate, OfferFamilyPlacement, ProductFamily


class Family03PublicLabelRenameTests(TestCase):
    slug = "pressoterapia-vacuum-drenagem"
    old_name = "Pressoterapia / Drenagem"
    new_name = "Pressoterapia / RF Tecar"

    def setUp(self):
        self.family = ProductFamily.objects.create(
            name=self.old_name,
            slug=self.slug,
            display_order=3,
            status=ProductFamily.Status.NEW,
        )
        self.original_pk = self.family.pk
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="family-03-existing",
            product_family=self.family,
            title="Existing family 03 offer",
        )
        self.placement = OfferFamilyPlacement.objects.create(
            offer=self.offer,
            product_family=self.family,
            display_order=0,
        )
        self.candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="family-03-candidate",
            title="Existing family 03 candidate",
        )
        self.migration = importlib.import_module(
            "apps.catalog.migrations.0018_rename_family_03_rf_tecar"
        )

    def test_forward_changes_only_name_and_preserves_identity_and_relations(self):
        self.migration.rename_family(django_apps, None)

        self.family.refresh_from_db()
        self.offer.refresh_from_db()
        self.placement.refresh_from_db()
        self.candidate.refresh_from_db()

        self.assertEqual(self.family.pk, self.original_pk)
        self.assertEqual(self.family.name, self.new_name)
        self.assertEqual(self.family.slug, self.slug)
        self.assertEqual(self.family.display_order, 3)
        self.assertEqual(self.family.status, ProductFamily.Status.NEW)
        self.assertEqual(self.offer.product_family_id, self.original_pk)
        self.assertEqual(self.placement.product_family_id, self.original_pk)
        self.assertEqual(self.candidate.product_family_id, self.original_pk)

    def test_reverse_restores_old_name_and_preserves_identity(self):
        self.migration.rename_family(django_apps, None)
        self.migration.restore_family_name(django_apps, None)

        self.family.refresh_from_db()
        self.assertEqual(self.family.pk, self.original_pk)
        self.assertEqual(self.family.name, self.old_name)
        self.assertEqual(self.family.slug, self.slug)
        self.assertEqual(self.family.display_order, 3)
        self.assertEqual(self.family.status, ProductFamily.Status.NEW)

    def test_storefront_and_owner_panel_show_new_label_on_same_slug_url(self):
        self.migration.rename_family(django_apps, None)

        home = self.client.get(reverse("storefront:home"))
        self.assertEqual(home.status_code, 200)
        self.assertContains(home, self.new_name)
        self.assertNotContains(home, self.old_name)

        detail_url = reverse("storefront:product-family-detail", kwargs={"slug": self.slug})
        detail = self.client.get(detail_url)
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, self.new_name)
        self.assertNotContains(detail, self.old_name)
        self.assertEqual(detail_url, f"/products/{self.slug}/")

        staff = get_user_model().objects.create_user(
            username="family-03-staff", password="x", is_staff=True
        )
        self.client.force_login(staff)
        dashboard = self.client.get(reverse("owner-panel:dashboard"))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, self.new_name)
        self.assertNotContains(dashboard, self.old_name)
