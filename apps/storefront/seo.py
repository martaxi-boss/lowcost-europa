from urllib.parse import urlsplit

from django.conf import settings


def public_indexing_active(request):
    """Enable discovery only on the explicitly configured public hostname."""
    public = urlsplit(settings.PUBLIC_SITE_URL)
    return bool(
        settings.PUBLIC_INDEXING_ENABLED
        and public.scheme == "https"
        and public.netloc
        and request.get_host().lower() == public.netloc.lower()
    )


PRIVATE_PATH_PREFIXES = (
    "/painel/",
    "/admin/",
    "/ops/",
    "/health/",
    "/i18n/",
    "/go/",
    "/contactar/",
    "/aliexpress/",
)
