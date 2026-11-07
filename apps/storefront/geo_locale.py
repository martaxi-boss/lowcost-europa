"""Opt-in, Europe-focused storefront language selection by public IP country.

Only PT, ES, FR and DE receive non-English automatic languages. GB and
every other location (including unresolved IPs) default to English. No IP is
stored and no remote lookup is performed. Browser and old language cookies are ignored.
"""

import ipaddress
import logging
from functools import lru_cache
from pathlib import Path

import maxminddb
from django.conf import settings
from django.middleware.locale import LocaleMiddleware
from django.utils import translation
from django.utils.cache import patch_vary_headers
from maxminddb.errors import InvalidDatabaseError

logger = logging.getLogger(__name__)

COUNTRY_LANGUAGES = {
    "PT": "pt-pt",
    "ES": "es",
    "FR": "fr",
    "DE": "de",
    "GB": "en",
}

PUBLIC_PAGES = frozenset({
    "/",
    "/pesquisar/",
    "/como-funciona/",
    "/afiliados/",
    "/privacidade/",
    "/termos/",
    "/contacto/",
})


def is_public_storefront_page(path):
    return path in PUBLIC_PAGES or (
        path.startswith("/products/") and path.endswith("/")
    )


def public_client_ip(request):
    """Trust X-Real-IP only when the immediate upstream is local Nginx.

    Nginx MUST overwrite this header with $remote_addr; never trust an
    arbitrary client-controlled X-Forwarded-For chain.
    """
    try:
        peer = ipaddress.ip_address(request.META.get("REMOTE_ADDR", ""))
    except ValueError:
        return None

    if peer.is_loopback:
        try:
            forwarded = ipaddress.ip_address(request.META.get("HTTP_X_REAL_IP", ""))
        except ValueError:
            return None
        return forwarded if forwarded.is_global else None

    return peer if peer.is_global else None


@lru_cache(maxsize=1)
def _reader(db_path):
    """A shared, read-only MMDB reader; restart the process after DB updates."""
    return maxminddb.open_database(db_path)


def lookup_country(ip):
    """Resolve an ISO country code from the project's local MMDB, not an API."""
    if ip is None:
        return None
    db_path = Path(settings.GEO_LANGUAGE_COUNTRY_DB)
    if not db_path.is_file():
        return None
    try:
        record = _reader(str(db_path)).get(str(ip))
        return (record or {}).get("country", {}).get("iso_code")
    except (InvalidDatabaseError, OSError, ValueError) as exc:
        logger.warning("Country database unavailable: %s", type(exc).__name__)
        return None


class EuropeCountryLocaleMiddleware(LocaleMiddleware):
    """Enforce IP-based language on public UI, not cookies or browser settings."""

    def process_request(self, request):
        super().process_request(request)
        if not settings.GEO_LANGUAGE_ENABLED or not is_public_storefront_page(
            request.path_info
        ):
            return

        country = lookup_country(public_client_ip(request))
        language = COUNTRY_LANGUAGES.get(country, "en")
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()

    def process_response(self, request, response):
        response = super().process_response(request, response)
        if settings.GEO_LANGUAGE_ENABLED and is_public_storefront_page(
            request.path_info
        ):
            # A reverse proxy may not reuse an HTML page across visitors.
            patch_vary_headers(response, ("Cookie",))
            response["Cache-Control"] = "private, no-store"
        return response
