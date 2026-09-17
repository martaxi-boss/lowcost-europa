import importlib

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import (
    Offer,
    OfferClick,
    OfferFamilyPlacement,
    OfferObservation,
    ProductFamily,
)


class Family02TaxonomyAlignmentTests(TestCase):
    slug = "hydrodermoabrasao-aqua-facial-multifuncoes"
    old_name = "Hydrodermoabrasão / Aqua Facial / Multifunções faciais"
    new_name = "Microdermoabrasão / Hidrodermoabrasão / Multifunções faciais"

    def setUp(self):
        self.family = ProductFamily.objects.create(
            name=self.old_name,
            slug=self.slug,
            display_order=2,
            status=ProductFamily.Status.NEW,
        )
        self.original_pk = self.family.pk
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="family-02-existing",
            product_family=self.family,
            title="Existing family 02 offer",
            is_primary=True,
            is_active=True,
            owner_hidden=False,
        )
        self.placement = OfferFamilyPlacement.objects.create(
            offer=self.offer,
            product_family=self.family,
            selection_position=1,
            display_order=0,
        )
        self.observations = [OfferObservation.objects.create(offer=self.offer) for _ in range(3)]
        self.clicks = [OfferClick.objects.create(offer=self.offer) for _ in range(6)]
        self.migration = importlib.import_module("apps.catalog.migrations.0015_rename_family_02")

    def test_forward_renames_only_family_and_preserves_identity_and_data(self):
        family_count = ProductFamily.objects.count()
        offer_count = Offer.objects.count()
        placement_count = OfferFamilyPlacement.objects.count()

        self.migration.rename_family(django_apps, None)

        self.family.refresh_from_db()
        self.offer.refresh_from_db()
        self.placement.refresh_from_db()
        self.assertEqual(self.family.pk, self.original_pk)
        self.assertEqual(self.family.name, self.new_name)
        self.assertEqual(self.family.slug, self.slug)
        self.assertEqual(self.family.display_order, 2)
        self.assertEqual(self.family.status, ProductFamily.Status.NEW)
        self.assertEqual(ProductFamily.objects.count(), family_count)
        self.assertEqual(Offer.objects.count(), offer_count)
        self.assertEqual(OfferFamilyPlacement.objects.count(), placement_count)
        self.assertEqual(self.offer.product_family_id, self.family.pk)
        self.assertTrue(self.offer.is_primary)
        self.assertTrue(self.offer.is_active)
        self.assertFalse(self.offer.owner_hidden)
        self.assertEqual(self.placement.product_family_id, self.family.pk)
        self.assertEqual(self.placement.selection_position, 1)
        self.assertEqual(OfferObservation.objects.filter(offer=self.offer).count(), 3)
        self.assertEqual(OfferClick.objects.filter(offer=self.offer).count(), 6)

    def test_reverse_restores_only_old_name(self):
        self.migration.rename_family(django_apps, None)
        self.migration.restore_family_name(django_apps, None)
        self.family.refresh_from_db()
        self.assertEqual(self.family.name, self.old_name)
        self.assertEqual(self.family.slug, self.slug)
        self.assertEqual(self.family.display_order, 2)
        self.assertEqual(self.family.status, ProductFamily.Status.NEW)
        self.assertEqual(Offer.objects.filter(pk=self.offer.pk).count(), 1)
        self.assertEqual(OfferFamilyPlacement.objects.filter(pk=self.placement.pk).count(), 1)

    def test_storefront_and_owner_dashboard_show_new_name_on_same_url(self):
        self.migration.rename_family(django_apps, None)
        detail_url = reverse("storefront:product-family-detail", kwargs={"slug": self.slug})
        detail = self.client.get(detail_url)
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, self.new_name)
        self.assertNotContains(detail, self.old_name)

        staff = get_user_model().objects.create_user(
            username="family-02-staff", password="x", is_staff=True
        )
        self.client.force_login(staff)
        dashboard = self.client.get(reverse("owner-panel:dashboard"))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, self.new_name)
        self.assertNotContains(dashboard, self.old_name)
