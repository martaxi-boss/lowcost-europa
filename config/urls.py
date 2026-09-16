from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("ops/", include("apps.catalog.urls")),
    path("", include("apps.storefront.urls")),
    path("", include("apps.core.urls")),
]
