from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from apps.catalog.admin import OfferClickAdmin
from apps.catalog.models import Offer, OfferClick, ProductFamily


class OfferClickModelTests(TestCase):
    def test_model_stores_only_offer_and_clicked_at(self):
        concrete = {field.name for field in OfferClick._meta.concrete_fields}
        self.assertEqual(concrete, {"id", "offer", "clicked_at"})

    def test_click_is_protected_with_offer(self):
        family = ProductFamily.objects.create(name="Family", slug="click-family")
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="click-model",
            product_family=family,
        )
        click = OfferClick.objects.create(offer=offer)
        self.assertEqual(click.offer, offer)
        self.assertIsNotNone(click.clicked_at)


class OfferClickAdminTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="click-admin",
            email="click-admin@example.com",
            password="test-password",
        )
        self.request = RequestFactory().get("/admin/")
        self.request.user = self.user
        family = ProductFamily.objects.create(name="Admin Family", slug="click-admin-family")
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="click-admin-offer",
            product_family=family,
        )
        self.click = OfferClick.objects.create(offer=offer)

    def test_admin_is_registered_and_inspection_only(self):
        model_admin = admin.site._registry[OfferClick]
        self.assertIsInstance(model_admin, OfferClickAdmin)
        self.assertFalse(model_admin.has_add_permission(self.request))
        self.assertFalse(model_admin.has_change_permission(self.request, self.click))
        self.assertFalse(model_admin.has_delete_permission(self.request, self.click))
        self.assertEqual(model_admin.list_select_related, ("offer",))
