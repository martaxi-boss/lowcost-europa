from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("admin/", admin.site.urls),
    path("ops/", include("apps.catalog.urls")),
    path("painel/", include("apps.catalog.owner_panel_urls")),
    path("", include("apps.storefront.urls")),
    path("", include("apps.core.urls")),
]
