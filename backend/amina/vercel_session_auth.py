"""Django-Ninja session auth wired to IAMINA's Vercel CSRF origin policy."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Callable, Optional

from django.conf import settings
from django.http import HttpRequest, HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from ninja.errors import HttpError
from ninja.security import SessionAuth as NinjaSessionAuth

from amina.middleware.vercel_csrf import IaminaVercelCsrfViewMiddleware
from core.native_auth import (
    NATIVE_SESSION_ISSUED_AT_KEY,
    NativeTokenError,
    native_token_max_age_seconds,
    verify_native_token,
)


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
        cookie = request.COOKIES.get(self.param_name)
        if not cookie:
            # Anonymous writes must remain 401 (no credential), not 403
            # (missing CSRF). Django Ninja's SessionAuth.authenticate ignores
            # its key argument, so this case is also guarded below.
            return None
        # Django Ninja exempts its router view from Django's outer CSRF
        # middleware. The cookie auth path must therefore enforce CSRF
        # itself on every request, irrespective of Ninja's per-operation
        # exemption marker or the auth constructor's optional csrf flag.
        # An explicit bearer never enters this cookie-only path.
        error_response = check_iamina_csrf(request)
        if error_response:
            raise HttpError(403, "CSRF check Failed")
        return cookie

    def authenticate(
        self,
        request: HttpRequest,
        key: Optional[str],
    ) -> Optional[Any]:
        # Django-Ninja 1.7.3's APIKeyBase.__call__ invokes authenticate
        # even when _get_key returned None. Its SessionAuth.authenticate
        # checks request.user but ignores key entirely. Guard both methods:
        # an invalid explicit bearer must NEVER authorize via cookie.
        if "HTTP_AUTHORIZATION" in request.META or not key:
            return None
        return super().authenticate(request, key)


# Native login/logout/reset are public entry/exit routes; an old cookie must
# not prevent a patient from reauthenticating or explicitly signing out.
_PUBLIC_NATIVE_SESSION_PATHS = frozenset({
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/firebase",
    "/api/v1/auth/logout",
    "/api/v1/auth/password/reset/request",
    "/api/v1/auth/password/reset/confirm",
})


def _bounded_native_login_cookie(request: HttpRequest) -> bool:
    """Reject unbounded legacy cookie authority, with no cookie replay grace.

    The marker is server-side Django session state, not browser-authored input.
    Checking issued-at on each request also honors a newly SHORTENED bearer
    policy rather than leaving an older session alive until its prior deadline.
    """
    value = request.session.get(NATIVE_SESSION_ISSUED_AT_KEY)
    if not isinstance(value, str):
        return False
    try:
        issued_at = datetime.fromisoformat(value)
        max_age = native_token_max_age_seconds()
    except (TypeError, ValueError, OverflowError, NativeTokenError):
        return False
    if issued_at.tzinfo is None:
        return False
    now = timezone.now()
    return issued_at <= now < issued_at + timedelta(seconds=max_age)


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
            # Django Ninja routes are csrf_exempt at the outer Django view
            # boundary. Enforce CSRF *before view dispatch* whenever Django
            # has authenticated a browser session cookie, including public
            # auth routes such as logout. Operation-level auth is not a
            # sufficient security boundary for session-cookie writes.
            if (
                request.user.is_authenticated
                and request.COOKIES.get(settings.SESSION_COOKIE_NAME)
            ):
                # An existing Django session may predate F08 and still carry
                # Django's historic 14-day default. Never let it authorize
                # clinical reads/writes or protected identity routes without
                # the server-issued fixed-duration native login provenance.
                if (
                    request.path_info not in _PUBLIC_NATIVE_SESSION_PATHS
                    and not _bounded_native_login_cookie(request)
                ):
                    return JsonResponse({"detail": "Authentication required"}, status=401)
                denied = check_iamina_csrf(request)
                if denied:
                    return denied
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
