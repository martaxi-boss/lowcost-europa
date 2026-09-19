import logging

from django.http import HttpResponse

from apps.core.login_rate_limit import FileLoginRateLimiter, source_token

logger = logging.getLogger(__name__)

PROTECTED_LOGIN_PATHS = {
    "/painel/entrar/": "owner-login",
    "/admin/login/": "admin-login",
}


class PrivateLoginRateLimitMiddleware:
    """Rate-limit repeated private authentication POSTs by trusted source."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        endpoint = PROTECTED_LOGIN_PATHS.get(request.path)
        if request.method != "POST" or endpoint is None:
            return self.get_response(request)

        token = source_token(request)
        limiter = FileLoginRateLimiter()

        try:
            retry_after = limiter.retry_after(token)
        except Exception:
            logger.error("Private login limiter unavailable endpoint=%s", endpoint)
            return self.get_response(request)

        if retry_after:
            logger.warning(
                "Private login throttled endpoint=%s source=%s",
                endpoint,
                token[:16],
            )
            response = HttpResponse(
                "Muitas tentativas. Tente novamente mais tarde.",
                status=429,
                content_type="text/plain; charset=utf-8",
            )
            response["Retry-After"] = str(retry_after)
            response["Cache-Control"] = "private, no-store"
            response["X-Robots-Tag"] = "noindex, nofollow"
            return response

        response = self.get_response(request)

        # A CSRF rejection is not an authentication attempt.
        if response.status_code == 403:
            return response

        if request.user.is_authenticated and request.user.is_staff:
            try:
                limiter.clear(token)
            except Exception:
                logger.error("Private login limiter clear failed endpoint=%s", endpoint)
            return response

        try:
            limiter.record_failure(token)
            logger.info(
                "Private login authentication failed endpoint=%s source=%s",
                endpoint,
                token[:16],
            )
        except Exception:
            logger.error("Private login limiter update failed endpoint=%s", endpoint)

        return response
