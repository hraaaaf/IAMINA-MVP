"""Patient-owned, CSRF-governed D2 in-app inbox, no push or medical alerts."""
from __future__ import annotations

from typing import Literal

from django.db import transaction
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel, ConfigDict

from amina.vercel_session_auth import check_iamina_csrf
from core.d2_notification_service import (
    MAX_INBOX,
    NOTICE_VERSION,
    maybe_record_language_preference,
    notice_contract,
)
from core.models.d2_notification import D2Notification, D2NotificationPreference

router = Router(tags=["d2-notifications"])
ROOT = "/account/notifications"


class ProactivityGrant(BaseModel):
    model_config = ConfigDict(extra="forbid")
    locale: Literal["fr", "en", "ar"]
    notice_version: str
    notice_digest: str
    acknowledgment: Literal["ENABLE_D2_IN_APP_PROACTIVITY"]


def _csrf_or_reject(request):
    """Django-Ninja views may bypass global middleware CSRF enforcement."""
    if request.COOKIES:
        if request.META.get("HTTP_AUTHORIZATION", "").strip():
            raise HttpError(403, "Mixed cookie and bearer credentials rejected")
        if check_iamina_csrf(request) is not None:
            raise HttpError(403, "CSRF check failed")


def _preference(patient_id: int):
    return D2NotificationPreference.objects.filter(patient_id=patient_id).first()


def _is_opted_in(pref):
    if pref is None or pref.proactive_opt_in is not True or pref.granted_at is None:
        return False
    return pref.notice_version == NOTICE_VERSION and any(
        pref.notice_digest == notice_contract(locale)["notice_digest"]
        for locale in ("fr", "en", "ar")
    )


def _serialize(row: D2Notification) -> dict:
    return {
        "id": row.pk, "kind": row.kind, "code": row.code,
        "created_at": row.created_at.isoformat(),
        "expires_at": row.expires_at.isoformat(),
        "read_at": row.read_at.isoformat() if row.read_at else None,
    }


@router.get(ROOT)
def inbox(request, locale: str = "fr"):
    """Read-only: no clinical queries, synthesized messages or side effects."""
    if locale not in ("fr", "ar", "en"):
        raise HttpError(422, "Unsupported notification locale")
    patient_id = request.user.pk  # from authenticated API router, never input
    now = timezone.now()
    items = list(
        D2Notification.objects.filter(
            patient_id=patient_id, expires_at__gt=now,
        ).order_by("-created_at", "-id")[:MAX_INBOX]
    )
    preference = _preference(patient_id)
    return {
        "purpose": "d2_in_app_notifications",
        "in_app_enabled": True,
        "browser_push_enabled": False,
        "proactive_opt_in": _is_opted_in(preference),
        "consent": notice_contract(locale),
        "unread_count": sum(row.read_at is None for row in items),
        "items": [_serialize(row) for row in items],
    }


@router.put(ROOT + "/proactivity")
@transaction.atomic
def enable_proactivity(request, data: ProactivityGrant):
    _csrf_or_reject(request)
    notice = notice_contract(data.locale)
    if data.notice_version != NOTICE_VERSION or data.notice_digest != notice["notice_digest"]:
        raise HttpError(422, "Consent text/version mismatch")
    preference, _ = D2NotificationPreference.objects.select_for_update().get_or_create(
        patient=request.user,
    )
    if not _is_opted_in(preference):
        preference.proactive_opt_in = True
        preference.notice_version = NOTICE_VERSION
        preference.notice_digest = notice["notice_digest"]
        preference.granted_at = timezone.now()
        preference.save(update_fields=[
            "proactive_opt_in", "notice_version", "notice_digest",
            "granted_at", "updated_at",
        ])
    # Nonmedical, patient-owned locale provenance only. This is not an alert.
    maybe_record_language_preference(patient_id=request.user.pk)
    return inbox(request, data.locale)


@router.delete(ROOT + "/proactivity")
@transaction.atomic
def disable_proactivity(request):
    _csrf_or_reject(request)
    preference = D2NotificationPreference.objects.select_for_update().filter(
        patient=request.user,
    ).first()
    if preference is not None:
        preference.proactive_opt_in = False
        preference.notice_version = ""
        preference.notice_digest = ""
        preference.granted_at = None
        preference.save(update_fields=[
            "proactive_opt_in", "notice_version", "notice_digest",
            "granted_at", "updated_at",
        ])
    # Revoke = remove proactive notices immediately. Real factual account
    # events remain patient-owned and visible for their bounded TTL.
    D2Notification.objects.filter(patient=request.user, kind="proactive").delete()
    return inbox(request)


@router.put(ROOT + "/{notice_id}/read")
@transaction.atomic
def mark_read(request, notice_id: int):
    _csrf_or_reject(request)
    now = timezone.now()
    row = D2Notification.objects.filter(
        pk=notice_id, patient=request.user, expires_at__gt=now,
    ).first()
    if row is None:
        raise HttpError(404, "Notification not found")
    if row.read_at is None:
        row.read_at = now
        row.save(update_fields=["read_at"])
    return {"item": _serialize(row)}


@router.post(ROOT + "/read-all")
@transaction.atomic
def mark_all_read(request):
    _csrf_or_reject(request)
    now = timezone.now()
    updated = D2Notification.objects.filter(
        patient=request.user, expires_at__gt=now, read_at__isnull=True,
    ).update(read_at=now)
    return {"updated": updated}


@router.delete(ROOT + "/{notice_id}")
@transaction.atomic
def delete_item(request, notice_id: int):
    _csrf_or_reject(request)
    deleted, _ = D2Notification.objects.filter(
        pk=notice_id, patient=request.user,
    ).delete()
    if not deleted:
        raise HttpError(404, "Notification not found")
    return {"deleted": True}
