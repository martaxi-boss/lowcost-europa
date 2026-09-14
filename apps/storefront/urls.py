from django.urls import path

from . import views

app_name = "storefront"

urlpatterns = [
    path("", views.home, name="home"),
    path("products/<slug:slug>/", views.product_family_detail, name="product-family-detail"),
    path("go/<int:offer_id>/", views.offer_go, name="offer-go"),
]
