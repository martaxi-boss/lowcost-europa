from django.contrib import admin

from .models import Offer, OfferObservation, ProductFamily


@admin.register(ProductFamily)
class ProductFamilyAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "status", "updated_at")
    search_fields = ("name", "slug")
    list_filter = ("status",)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("source", "external_product_id", "product_family", "is_active", "last_seen_at")
    search_fields = ("external_product_id", "title", "product_family__name")
    list_filter = ("source", "is_active")


@admin.register(OfferObservation)
class OfferObservationAdmin(admin.ModelAdmin):
    list_display = (
        "offer",
        "observed_at",
        "destination_country",
        "price",
        "currency",
        "search_delivery_days",
        "delivery_days",
        "availability",
    )
    search_fields = ("offer__external_product_id",)
    list_filter = ("availability", "destination_country", "currency")
