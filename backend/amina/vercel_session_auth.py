"""Django-Ninja session auth wired to IAMINA's Vercel CSRF origin policy."""
from __future__ import annotations

from typing import Any, Callable, Optional

from django.http import HttpRequest, HttpResponseForbidden
from ninja.errors import HttpError
from ninja.security import SessionAuth as NinjaSessionAuth

from amina.middleware.vercel_csrf import IaminaVercelCsrfViewMiddleware


def _no_view() -> None:
    pass


def check_iamina_csrf(
    request: HttpRequest,
    callback: Callable = _no_view,
):
    middleware = IaminaVercelCsrfViewMiddleware(lambda _: HttpResponseForbidden())
    # Only a verified bearer may bypass session CSRF. A forged Bearer header
    # can otherwise set _dont_enforce_csrf_checks before cookie fallback.
    bearer_header = request.META.get("HTTP_AUTHORIZATION", "")
    force_check = bearer_header.lower().startswith("bearer ")
    old_bypass = getattr(request, "_dont_enforce_csrf_checks", False)
    if force_check:
        request._dont_enforce_csrf_checks = False  # type: ignore[attr-defined]
    try:
        request.csrf_processing_done = False  # type: ignore[attr-defined]
        middleware.process_request(request)
        return middleware.process_view(request, callback, (), {})
    finally:
        if force_check:
            request._dont_enforce_csrf_checks = old_bypass  # type: ignore[attr-defined]


class SessionAuth(NinjaSessionAuth):
    """Preserve Django session auth while using IAMINA's narrow Vercel CSRF policy."""

    def _get_key(self, request: HttpRequest) -> Optional[str]:
        key = request.COOKIES.get(self.param_name)
        # This authenticator handles browser-managed session cookies.
        # Never inherit an operation's Ninja CSRF-exempt flag for unsafe POSTs.
        if key and request.method not in ("GET", "HEAD", "OPTIONS", "TRACE"):
            error_response = check_iamina_csrf(request)
            if error_response:
                raise HttpError(403, "CSRF check Failed")
        return key

    def authenticate(
        self,
        request: HttpRequest,
        key: Optional[str],
    ) -> Optional[Any]:
        return super().authenticate(request, key)
