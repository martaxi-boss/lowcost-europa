"""Stable, opt-in locale URLs for the two launch markets.

Unprefixed indexed URLs remain unchanged. No IP-based redirect is introduced.
"""
import re

from django.conf import settings
from django.urls import reverse

SUPPORTED_SEO_LOCALES = {"pt": "pt-pt", "es": "es"}
PRODUCT_PATH = re.compile(r"^/products/[a-z0-9-]+/$")


def requested_seo_locale(path):
    for prefix, language in SUPPORTED_SEO_LOCALES.items():
        if path == f"/{prefix}/":
            return language
        if path.startswith(f"/{prefix}/") and PRODUCT_PATH.fullmatch(
            path[len(prefix) + 1:]
        ):
            return language
    return None


def root_public_path(path):
    if path == "/" or PRODUCT_PATH.fullmatch(path):
        return path
    for prefix in SUPPORTED_SEO_LOCALES:
        if path == f"/{prefix}/":
            return "/"
        if path.startswith(f"/{prefix}/"):
            rest = path[len(prefix) + 1:]
            if PRODUCT_PATH.fullmatch(rest):
                return rest
    return None


def localized_public_path(root_path, locale):
    if locale not in SUPPORTED_SEO_LOCALES:
        raise ValueError("Unsupported SEO locale")
    return f"/{locale}/" if root_path == "/" else f"/{locale}{root_path}"


def alternate_public_urls(path, base_url):
    root = root_public_path(path)
    if root is None:
        return []
    return [
        ("pt-PT", base_url + localized_public_path(root, "pt")),
        ("es-ES", base_url + localized_public_path(root, "es")),
        ("x-default", base_url + root),
    ]


def home_page_url(request):
    locale = requested_seo_locale(request.path_info)
    if settings.LOCALE_SEO_ENABLED and locale:
        return localized_public_path("/", "pt" if locale == "pt-pt" else "es")
    return reverse("storefront:home")


def family_page_url(request, slug):
    root = reverse("storefront:product-family-detail", kwargs={"slug": slug})
    locale = requested_seo_locale(request.path_info)
    if settings.LOCALE_SEO_ENABLED and locale:
        return localized_public_path(root, "pt" if locale == "pt-pt" else "es")
    return root
