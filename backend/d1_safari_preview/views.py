"""D1-6: synthetic-only account bootstrap and static Safari research assets.

Never import/mount this package from clinical IAMINA URLconfs.
"""
from __future__ import annotations

import secrets
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.http import require_POST

from core.models import BasePatientProfile

_ASSETS = Path(__file__).resolve().parent / "assets"
_TYPES = {
    "": ("index.html", "text/html; charset=utf-8"),
    "client.js": ("client.js", "text/javascript; charset=utf-8"),
    "bridge.js": ("bridge.js", "text/javascript; charset=utf-8"),
    "lab.css": ("lab.css", "text/css; charset=utf-8"),
}
_CSP = (
    "default-src 'none'; script-src 'self'; style-src 'self'; "
    "connect-src 'self'; img-src 'none'; object-src 'none'; "
    "base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
)


def _enabled():
    return getattr(settings, "D1_PASSKEY_RESEARCH_ENABLED", False) is True and (
        getattr(settings, "ROOT_URLCONF", "") == "d1_safari_preview.urls"
    )


def _synthetic_account(request):
    user = getattr(request, "user", None)
    return bool(
        user is not None and user.is_authenticated and user.is_active
        and user.username.startswith("d1lab_")
        and request.session.get("d1lab_synthetic_user") == user.pk
    )


class SyntheticAccountOnlyMiddleware(MiddlewareMixin):
    """Deny any credential operation for legacy/foreign/nonlab identities."""

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.path_info.startswith("/api/") and not _synthetic_account(request):
            return JsonResponse({"detail": "Synthetic account required"}, status=401)
        return None


def lab_asset(request, asset=""):
    if not _enabled() or request.method != "GET" or asset not in _TYPES:
        return HttpResponse(status=404)
    filename, content_type = _TYPES[asset]
    response = HttpResponse((_ASSETS / filename).read_bytes(), content_type=content_type)
    response["Content-Security-Policy"] = _CSP
    response["Cache-Control"] = "no-store"
    response["Referrer-Policy"] = "same-origin" if asset == "" else "no-referrer"
    response["X-Robots-Tag"] = "noindex, nofollow"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@require_POST
def start_synthetic_session(request):
    """Create exactly one generated disposable laboratory identity per session.

    Protected by Vercel deployment SSO, same-origin HTTPS and Django CSRF.
    No clinical profile or patient API is used. Password is returned once
    for synthetic enrollment only, never persisted in logs or on the page.
    """
    if not _enabled() or request.META.get("HTTP_AUTHORIZATION"):
        return HttpResponse(status=404)
    if _synthetic_account(request):
        response = JsonResponse({"status": "ALREADY_STARTED", "patient_ready": False})
        response["Cache-Control"] = "no-store"
        return response
    user_model = get_user_model()
    with transaction.atomic():
        if user_model.objects.filter(username__startswith="d1lab_").count() >= 20:
            return HttpResponse(status=429)
        username = "d1lab_" + secrets.token_hex(12)
        password = secrets.token_urlsafe(32)
        user = user_model.objects.create_user(username=username, password=password)
        BasePatientProfile.objects.create(patient=user)
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    request.session["d1lab_synthetic_user"] = user.pk
    request.session.set_expiry(14400)
    response = JsonResponse({
        "status": "SYNTHETIC_LAB_CREATED",
        "patient_ready": False,
        "enrollment_password": password,
    })
    response["Cache-Control"] = "no-store"
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response
