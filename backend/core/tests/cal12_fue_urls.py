"""CAL-12 loopback-only isolated HTTP adapter for Chrome FUE.

NEVER imported into production URLConf. Run only via cal12_fue_runserver
with disposable PostgreSQL and CAL12_FUE_TEST_ONLY=1. No clinical export route.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.urls import path
from django.utils import timezone as django_timezone
from django.views.decorators.csrf import csrf_exempt

from amina.urls import urlpatterns as production_urls
from core.cal12_export_consent_ledger import (
    Cal12FixtureConsentDenied,
    fictional_preview_ready,
    grant_fixture_consent,
    revoke_fixture_consent,
)

_START = datetime(2026, 11, 1, tzinfo=timezone.utc)
_END = datetime(2026, 11, 8, tzinfo=timezone.utc)


def _allowed(request):
    return (
        os.environ.get("CAL12_FUE_TEST_ONLY") == "1"
        and getattr(settings, "CAL12_SYNTHETIC_EXPORT_LEDGER_ENABLED", False)
        and settings.DEBUG
        and request.get_host() == "127.0.0.1:8000"
        and request.META.get("REMOTE_ADDR") == "127.0.0.1"
    )


def _deny():
    return JsonResponse({"allowed": False}, status=403)


def _payload(request):
    if len(request.body) > 2048:
        raise Cal12FixtureConsentDenied("payload_too_large")
    item = json.loads(request.body)
    if not isinstance(item, dict):
        raise Cal12FixtureConsentDenied("invalid_payload")
    return item


def _bearer(request):
    value = request.headers.get("Authorization", "")
    prefix = "Bearer "
    if not value.startswith(prefix) or not value[len(prefix):].startswith("iamina."):
        raise Cal12FixtureConsentDenied("native_bearer_required")
    return value[len(prefix):]


def _scope(payload):
    return payload.get("owner_scope", "")


def _common(payload, bearer):
    locale = payload.get("locale", "")
    return {
        "bearer": bearer,
        "owner_scope": _scope(payload),
        "recipient_ref": payload.get("recipient_ref", ""),
        "channel": payload.get("channel", ""),
        "destination_fixture_proof": payload.get("destination_fixture_proof", ""),
        "notice_version": payload.get("notice_version", ""),
        "notice_sha256": payload.get("notice_sha256", ""),
        "locale": locale,
        "purpose": payload.get("purpose", ""),
        "data_category": payload.get("data_category", ""),
        "period_start_utc": _START,
        "period_end_utc": _END,
    }


def index(request):
    if not _allowed(request):
        return _deny()
    if request.method != "GET":
        return HttpResponse(status=405)
    html_path = Path(__file__).resolve().parents[3] / "tools" / "cal12_live_fue_fixture.html"
    response = HttpResponse(html_path.read_text(encoding="utf-8"), content_type="text/html; charset=utf-8")
    response["Cache-Control"] = "no-store"
    response["Content-Security-Policy"] = (
        "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
        "connect-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'"
    )
    return response


@csrf_exempt
def grant(request):
    if not _allowed(request):
        return _deny()
    if request.method != "POST":
        return HttpResponse(status=405)
    try:
        payload = _payload(request)
        bearer = _bearer(request)
        now = django_timezone.now()
        consent = grant_fixture_consent(
            **_common(payload, bearer),
            granted_at_utc=now,
            expires_at_utc=now + timedelta(minutes=10),
            explicitly_agreed=payload.get("explicitly_agreed") is True,
        )
        return JsonResponse({"record": consent.pk, "revision": consent.revision})
    except (Cal12FixtureConsentDenied, ValueError, TypeError, KeyError):
        return JsonResponse({"allowed": False}, status=403)


@csrf_exempt
def check(request):
    if not _allowed(request):
        return _deny()
    if request.method != "POST":
        return HttpResponse(status=405)
    try:
        payload = _payload(request)
        bearer = _bearer(request)
        offset = payload.get("offset_minutes", 0)
        if type(offset) is not int or offset not in (0, 20):
            return _deny()
        result = fictional_preview_ready(
            **_common(payload, bearer),
            receipt_id=payload.get("record"),
            revision=payload.get("revision"),
            now_utc=django_timezone.now() + timedelta(minutes=offset),
        )
        return JsonResponse({"allowed": result})
    except (Cal12FixtureConsentDenied, ValueError, TypeError, KeyError):
        return JsonResponse({"allowed": False})


@csrf_exempt
def revoke(request):
    if not _allowed(request):
        return _deny()
    if request.method != "POST":
        return HttpResponse(status=405)
    try:
        payload = _payload(request)
        result = revoke_fixture_consent(
            bearer=_bearer(request),
            owner_scope=_scope(payload),
            receipt_id=payload.get("record"),
            revoked_at_utc=django_timezone.now(),
        )
        return JsonResponse({"revoked": result})
    except (Cal12FixtureConsentDenied, ValueError, TypeError, KeyError):
        return JsonResponse({"revoked": False}, status=403)


urlpatterns = [
    *production_urls,
    path("_cal12_fixture/", index),
    path("_cal12_fixture/grant", grant),
    path("_cal12_fixture/check", check),
    path("_cal12_fixture/revoke", revoke),
]
