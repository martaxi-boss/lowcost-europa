from django.urls import path

from . import views

app_name = "storefront"

urlpatterns = [
    path("", views.home, name="home"),
    path("pesquisar/", views.search, name="search"),
    path(
        "como-funciona/",
        views.institutional_page,
        {"page": "como-funciona"},
        name="como-funciona",
    ),
    path("afiliados/", views.institutional_page, {"page": "afiliados"}, name="afiliados"),
    path("privacidade/", views.institutional_page, {"page": "privacidade"}, name="privacidade"),
    path("termos/", views.institutional_page, {"page": "termos"}, name="termos"),
    path("contacto/", views.institutional_page, {"page": "contacto"}, name="contacto"),
    path("contactar/whatsapp/", views.whatsapp_contact, name="whatsapp-contact"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap"),
    path("robots.txt", views.robots_txt, name="robots"),
    path("products/<slug:slug>/", views.product_family_detail, name="product-family-detail"),
    path("go/<int:offer_id>/", views.offer_go, name="offer-go"),
]
