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
    request.csrf_processing_done = False  # type: ignore[attr-defined]
    middleware.process_request(request)
    return middleware.process_view(request, callback, (), {})


class SessionAuth(NinjaSessionAuth):
    """Preserve Django session auth while using IAMINA's narrow Vercel CSRF policy."""

    def _get_key(self, request: HttpRequest) -> Optional[str]:
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
        return super().authenticate(request, key)
