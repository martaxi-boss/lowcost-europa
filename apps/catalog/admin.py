from django import forms
from django.contrib import admin

from .models import Offer, OfferClick, OfferObservation, ProductFamily


class ProductFamilyAdminForm(forms.ModelForm):
    class Meta:
        model = ProductFamily
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        allowed = {
            ProductFamily.Status.NEW,
            ProductFamily.Status.TESTING,
            ProductFamily.Status.OBSERVATION,
            ProductFamily.Status.RETIRED,
        }
        self.fields["status"].choices = [
            choice for choice in ProductFamily.Status.choices if choice[0] in allowed
        ]


@admin.register(ProductFamily)
class ProductFamilyAdmin(admin.ModelAdmin):
    form = ProductFamilyAdminForm
    list_display = ("name", "slug", "status", "created_at", "updated_at")
    search_fields = ("name", "slug")
    list_filter = ("status",)
    ordering = ("name", "pk")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = (
        "source",
        "external_product_id",
        "title",
        "product_family",
        "is_active",
        "is_primary",
        "last_seen_at",
    )
    search_fields = ("external_product_id", "title")
    list_filter = ("source", "is_active", "is_primary", "product_family")
    list_select_related = ("product_family",)
    fields = (
        "source",
        "external_product_id",
        "title",
        "product_url",
        "image_url",
        "affiliate_url",
        "product_family",
        "is_active",
        "is_primary",
        "first_seen_at",
        "last_seen_at",
        "created_at",
        "updated_at",
    )
    readonly_fields = (
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
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OfferObservation)
class OfferObservationAdmin(admin.ModelAdmin):
    list_display = (
        "offer",
        "observed_at",
        "price",
        "currency",
        "sales_count",
        "commission_rate",
        "search_delivery_days",
        "delivery_days",
        "availability",
    )
    search_fields = ("offer__external_product_id", "offer__title")
    list_filter = ("availability", "destination_country", "currency")
    list_select_related = ("offer",)
    ordering = ("-observed_at", "-pk")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OfferClick)
class OfferClickAdmin(admin.ModelAdmin):
    list_display = ("offer", "clicked_at")
    search_fields = ("offer__external_product_id", "offer__title")
    list_filter = ("clicked_at",)
    list_select_related = ("offer",)
    ordering = ("-clicked_at", "-pk")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
