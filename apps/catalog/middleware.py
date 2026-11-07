from apps.storefront.seo import PRIVATE_PATH_PREFIXES, public_indexing_active


class OwnerPanelPrivacyHeadersMiddleware:
    """Keep operational routes private even after public indexing is enabled."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(PRIVATE_PATH_PREFIXES):
            response["X-Robots-Tag"] = "noindex, nofollow"
            response["Cache-Control"] = "private, no-store"
        elif not public_indexing_active(request) or response.status_code >= 400:
            response["X-Robots-Tag"] = "noindex, nofollow"
        return response
