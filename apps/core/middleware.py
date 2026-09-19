import logging

from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

from apps.core.login_rate_limit import FileLoginRateLimiter, source_token

logger = logging.getLogger(__name__)

PROTECTED_LOGIN_PATHS = {
    "/painel/entrar/": "owner-login",
    "/admin/login/": "admin-login",
}


class PrivateLoginRateLimitMiddleware(MiddlewareMixin):
    """Rate-limit private authentication POSTs after CSRF has accepted the request."""

    def process_view(self, request, view_func, view_args, view_kwargs):
        endpoint = PROTECTED_LOGIN_PATHS.get(request.path)
        if request.method != "POST" or endpoint is None:
            return None

        token = source_token(request)
        request._private_login_rate_limit = (endpoint, token)
        limiter = FileLoginRateLimiter()

        try:
            retry_after = limiter.retry_after(token)
        except Exception:
            logger.error("Private login limiter unavailable endpoint=%s", endpoint)
            request._private_login_rate_limit = None
            return None

        if not retry_after:
            return None

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
        request._private_login_rate_limit = None
        return response

    def process_response(self, request, response):
        context = getattr(request, "_private_login_rate_limit", None)
        if context is None:
            return response

        endpoint, token = context
        limiter = FileLoginRateLimiter()

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
