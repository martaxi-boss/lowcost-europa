from django.urls import path, re_path

from . import views

app_name = "storefront"

urlpatterns = [
    path("", views.home, name="home"),
    path("pt/", views.locale_home, {"locale": "pt"}, name="home-pt"),
    path("es/", views.locale_home, {"locale": "es"}, name="home-es"),
    path("pt/products/<slug:slug>/", views.locale_product_family_detail,
         {"locale": "pt"}, name="product-pt"),
    path("es/products/<slug:slug>/", views.locale_product_family_detail,
         {"locale": "es"}, name="product-es"),
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
    path("sitemap.txt", views.sitemap_txt, name="sitemap-text"),
    path("robots.txt", views.robots_txt, name="robots"),
    re_path(r"^indexnow-(?P<key>[a-f0-9]{32})\.txt$", views.indexnow_key, name="indexnow-key"),
    path("products/<slug:slug>/", views.product_family_detail, name="product-family-detail"),
    path("go/<int:offer_id>/", views.offer_go, name="offer-go"),
]
