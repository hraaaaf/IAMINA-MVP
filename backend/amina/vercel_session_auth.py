"""Django-Ninja session auth wired to IAMINA's Vercel CSRF origin policy."""
from __future__ import annotations

from typing import Any, Callable, Optional

from django.http import HttpRequest, HttpResponseForbidden, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from ninja.errors import HttpError
from ninja.security import SessionAuth as NinjaSessionAuth

from amina.middleware.vercel_csrf import IaminaVercelCsrfViewMiddleware
from core.native_auth import NativeTokenError, verify_native_token


def _no_view() -> None:
    pass


def check_iamina_csrf(
    request: HttpRequest,
    callback: Callable = _no_view,
):
    middleware = IaminaVercelCsrfViewMiddleware(lambda _: HttpResponseForbidden())
    request.csrf_processing_done = False  # type: ignore[attr-defined]
    middleware.process_request(request)
    return middleware.process_view(request, callback, (), {})


class SessionAuth(NinjaSessionAuth):
    """Preserve Django session auth while using IAMINA's narrow Vercel CSRF policy."""

    def _get_key(self, request: HttpRequest) -> Optional[str]:
        # An explicit Authorization header selects bearer authentication.
        # When that bearer is invalid, never silently fall back to another
        # patient who happens to have a valid Django session cookie. A request
        # with no Authorization header retains the Web/PWA session + CSRF path.
        if "HTTP_AUTHORIZATION" in request.META:
            return None
        if self.csrf and not getattr(request, "_ninja_csrf_exempt", False):
            error_response = check_iamina_csrf(request)
            if error_response:
                raise HttpError(403, "CSRF check Failed")
        return request.COOKIES.get(self.param_name)

    def authenticate(
        self,
        request: HttpRequest,
        key: Optional[str],
    ) -> Optional[Any]:
        # Django-Ninja 1.7.3's APIKeyBase.__call__ invokes authenticate
        # even when _get_key returned None. Its SessionAuth.authenticate
        # checks request.user but ignores key entirely. Guard both methods:
        # an invalid explicit bearer must NEVER authorize via cookie.
        if "HTTP_AUTHORIZATION" in request.META:
            return None
        return super().authenticate(request, key)


class ExplicitBearerCookieIdentityMiddleware(MiddlewareMixin):
    """D11: fail closed before Ninja dispatch when cookie and bearer conflict.

    Ninja's router-level auth callback can accept a Django session identity
    independently of an explicit bearer. At this boundary Django's
    AuthenticationMiddleware has already resolved the session identity, so a
    request with two different patients must not reach clinical endpoints.
    Browser cookie-only sessions and native bearer-only requests are unchanged.
    """

    def process_view(self, request: HttpRequest, view_func, view_args, view_kwargs):
        if not request.path_info.startswith("/api/v1/"):
            return None
        raw = request.META.get("HTTP_AUTHORIZATION")
        if not raw:
            return None
        session_user = request.user
        if not session_user.is_authenticated:
            return None

        scheme, _, token = raw.partition(" ")
        if scheme.lower() != "bearer" or not token.startswith("iamina."):
            return JsonResponse({"detail": "Conflicting authentication identities"}, status=401)
        try:
            bearer_user = verify_native_token(token)
        except NativeTokenError:
            return JsonResponse({"detail": "Conflicting authentication identities"}, status=401)
        if bearer_user.pk != session_user.pk:
            return JsonResponse({"detail": "Conflicting authentication identities"}, status=401)
        return None
