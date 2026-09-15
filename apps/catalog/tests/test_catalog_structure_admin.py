from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.catalog.admin import OfferAdmin, OfferFamilyPlacementAdmin
from apps.catalog.models import Offer, OfferFamilyPlacement, ProductFamily


class CatalogStructureAdminTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="structure-admin",
            email="structure@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)
        self.request = RequestFactory().get("/admin/")
        self.request.user = self.user
        self.family = ProductFamily.objects.create(name="Admin Family", slug="admin-family")
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="admin-structure-offer",
            product_family=self.family,
        )
        self.placement = OfferFamilyPlacement.objects.create(
            offer=self.offer,
            product_family=self.family,
            selection_position=1,
            display_order=2,
            selection_reason="Editorial test reason",
        )

    def test_offer_and_placement_admin_are_registered(self):
        self.assertIsInstance(admin.site._registry[Offer], OfferAdmin)
        self.assertIsInstance(admin.site._registry[OfferFamilyPlacement], OfferFamilyPlacementAdmin)

    def test_equipment_type_is_editable_in_offer_admin(self):
        model_admin = admin.site._registry[Offer]
        readonly = set(model_admin.get_readonly_fields(self.request, self.offer))
        self.assertNotIn("equipment_type", readonly)
        self.assertIn("equipment_type", model_admin.fields)

    def test_placement_admin_exposes_editorial_fields(self):
        model_admin = admin.site._registry[OfferFamilyPlacement]
        self.assertIn("selection_position", model_admin.list_display)
        self.assertIn("display_order", model_admin.list_display)
        self.assertIn("selection_reason", model_admin.list_display)
        self.assertFalse(model_admin.has_delete_permission(self.request, self.placement))

    def test_placement_admin_pages_render(self):
        urls = (
            reverse("admin:catalog_offerfamilyplacement_changelist"),
            reverse("admin:catalog_offerfamilyplacement_add"),
            reverse("admin:catalog_offerfamilyplacement_change", args=[self.placement.pk]),
        )
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url, secure=True).status_code, 200)
