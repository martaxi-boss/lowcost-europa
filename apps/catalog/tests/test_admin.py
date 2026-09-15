from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.catalog.admin import OfferAdmin, OfferObservationAdmin, ProductFamilyAdmin
from apps.catalog.models import Offer, OfferObservation, ProductFamily


class CatalogAdminTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="catalog-admin",
            email="admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)
        self.request = RequestFactory().get("/admin/")
        self.request.user = self.user
        self.family = ProductFamily.objects.create(name="HIFU", slug="hifu")
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="123",
            product_family=self.family,
            title="HIFU machine",
        )
        self.observation = OfferObservation.objects.create(offer=self.offer)

    def test_catalog_models_are_registered(self):
        self.assertIsInstance(admin.site._registry[ProductFamily], ProductFamilyAdmin)
        self.assertIsInstance(admin.site._registry[Offer], OfferAdmin)
        self.assertIsInstance(admin.site._registry[OfferObservation], OfferObservationAdmin)

    def test_product_family_delete_is_disabled(self):
        model_admin = admin.site._registry[ProductFamily]
        self.assertFalse(model_admin.has_delete_permission(self.request, self.family))
        response = self.client.get(
            reverse("admin:catalog_productfamily_delete", args=[self.family.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_product_family_admin_exposes_editable_display_order(self):
        model_admin = admin.site._registry[ProductFamily]
        self.assertIn("display_order", model_admin.list_display)
        self.assertNotIn(
            "display_order", model_admin.get_readonly_fields(self.request, self.family)
        )
        self.assertEqual(model_admin.ordering[:1], ("display_order",))

    def test_product_family_form_limits_lifecycle_choices(self):
        model_admin = admin.site._registry[ProductFamily]
        form_class = model_admin.get_form(self.request)
        values = {value for value, _label in form_class().fields["status"].choices}
        self.assertEqual(
            values,
            {
                ProductFamily.Status.NEW,
                ProductFamily.Status.TESTING,
                ProductFamily.Status.OBSERVATION,
                ProductFamily.Status.RETIRED,
            },
        )
        self.assertNotIn(ProductFamily.Status.VERIFIED, values)
        self.assertNotIn(ProductFamily.Status.PROVEN, values)
        self.assertNotIn(ProductFamily.Status.WINNER, values)

    def test_offer_add_and_delete_are_disabled(self):
        model_admin = admin.site._registry[Offer]
        self.assertFalse(model_admin.has_add_permission(self.request))
        self.assertFalse(model_admin.has_delete_permission(self.request, self.offer))
        add_response = self.client.get(reverse("admin:catalog_offer_add"))
        delete_response = self.client.get(
            reverse("admin:catalog_offer_delete", args=[self.offer.pk])
        )
        self.assertEqual(add_response.status_code, 403)
        self.assertEqual(delete_response.status_code, 403)

    def test_offer_source_fields_are_read_only_and_curation_fields_editable(self):
        model_admin = admin.site._registry[Offer]
        readonly = set(model_admin.get_readonly_fields(self.request, self.offer))
        expected_readonly = {
            "source",
            "external_product_id",
            "title",
            "product_url",
            "image_url",
            "affiliate_url",
            "first_seen_at",
            "last_seen_at",
            "created_at",
            "updated_at",
        }
        self.assertTrue(expected_readonly.issubset(readonly))
        self.assertNotIn("product_family", readonly)
        self.assertNotIn("is_active", readonly)
        self.assertNotIn("is_primary", readonly)

    def test_offer_admin_rejects_inactive_primary(self):
        model_admin = admin.site._registry[Offer]
        form_class = model_admin.get_form(self.request, self.offer)
        form = form_class(
            data={
                "product_family": self.family.pk,
                "is_active": False,
                "is_primary": True,
            },
            instance=self.offer,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("catalog_offer_primary_requires_active", str(form.errors))

    def test_observation_is_inspection_only(self):
        model_admin = admin.site._registry[OfferObservation]
        self.assertFalse(model_admin.has_add_permission(self.request))
        self.assertFalse(model_admin.has_change_permission(self.request, self.observation))
        self.assertFalse(model_admin.has_delete_permission(self.request, self.observation))

    def test_admin_pages_render_for_authenticated_superuser(self):
        urls = (
            reverse("admin:catalog_productfamily_changelist"),
            reverse("admin:catalog_productfamily_add"),
            reverse("admin:catalog_offer_changelist"),
            reverse("admin:catalog_offer_change", args=[self.offer.pk]),
            reverse("admin:catalog_offerobservation_changelist"),
            reverse("admin:catalog_offerobservation_change", args=[self.observation.pk]),
        )
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
