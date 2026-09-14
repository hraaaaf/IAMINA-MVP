"""Fail-closed abuse protection for IAMINA's public native-auth endpoints."""

from __future__ import annotations

import json

from django.http import JsonResponse

from core.auth_abuse import AuthRateLimitExceeded, enforce_auth_abuse_limit


_PATH_ACTIONS = {
    "/api/v1/auth/login": "login",
    "/api/v1/auth/register": "register",
    "/api/v1/auth/password/reset/request": "password_reset",
}
_MAX_AUTH_BODY_BYTES = 4096


def _request_identity(request) -> str | None:
    try:
        content_length = int(request.META.get("CONTENT_LENGTH") or 0)
    except (TypeError, ValueError):
        content_length = 0
    if content_length > _MAX_AUTH_BODY_BYTES:
        return None
    content_type = (request.META.get("CONTENT_TYPE") or "").split(";", 1)[0].strip().lower()
    if content_type != "application/json":
        return None
    try:
        payload = json.loads((request.body or b"{}").decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    email = payload.get("email")
    return email if isinstance(email, str) else None


class AuthAbuseProtectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        action = _PATH_ACTIONS.get(request.path)
        if request.method == "POST" and action is not None:
            try:
                enforce_auth_abuse_limit(
                    request,
                    action,
                    identity=_request_identity(request),
                )
            except AuthRateLimitExceeded as exc:
                response = JsonResponse(
                    {
                        "error": {
                            "code": "auth_rate_limited",
                            "message": "Too many authentication attempts. Try again later.",
                            "retryable": True,
                        }
                    },
                    status=429,
                )
                response["Retry-After"] = str(exc.retry_after)
                return response
        return self.get_response(request)
