"""D2: explicit, patient-scoped savings of governed nonurgent previews.

This is a pull-only saved-items inbox. Never call /proactive-insights/evaluate,
deliver browser push or create a notification automatically.
"""
import hashlib
import hmac
from datetime import timedelta
from typing import Literal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel, ConfigDict

from core.api.v1.d2_preview_consent import _require_cookie_session_csrf, _status
from core.models import BasePatientProfile, D2InAppNotice
from diabetes.services.clinical.proactive_preview import preview_proactive_insights

router = Router(tags=["d2-in-app-notices"])
PATH = "/account/notification-inbox"
TTL = timedelta(days=7)
MAX_ITEMS = 20
SOURCE_VERSION = "proactive.personal-response.lifecycle.v1"


class SaveNoticeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    acknowledgment: Literal["SAVE_GOVERNED_PREVIEW"]


def _require_opt_in(user):
    if not _status(user)["opted_in"]:
        raise HttpError(409, "Current D2 preview-only consent is required")


def _present(row):
    return {
        "id": row.pk,
        "kind": row.kind,
        "created_at": row.created_at.isoformat(),
        "expires_at": row.expires_at.isoformat(),
        "read_at": row.read_at.isoformat() if row.read_at else None,
    }


@router.get(PATH)
def get_inbox(request):
    _require_opt_in(request.user)
    now = timezone.now()
    # Bounded TTL also bounds response size and prevents stale medical context.
    active = D2InAppNotice.objects.filter(
        patient=request.user, expires_at__gt=now,
    ).order_by("-created_at", "-id")[:MAX_ITEMS]
    return {"delivery_enabled": False, "items": [_present(row) for row in active]}


@router.post(PATH + "/save")
@transaction.atomic
def save_current_governed_preview(request, data: SaveNoticeRequest):
    _require_cookie_session_csrf(request)
    _require_opt_in(request.user)
    candidate = preview_proactive_insights(patient_id=request.user.pk)
    item = candidate.item
    if (
        candidate.status != "available"
        or item is None
        or item.source_version != SOURCE_VERSION
        or item.escalation_class != "none"
        or item.surface_now
        or item.priority.safety_time_sensitivity != "non_urgent_observation"
        or item.kind not in ("context", "meal")
        or not item.evidence_id
        or not item.observation_key
    ):
        raise HttpError(409, "No eligible nonurgent observation to save")

    # HMAC: non-reversible, account-bound dedup key. No clinical IDs stored.
    message = (
        f"{request.user.pk}|{item.observation_key}|{item.evidence_id}|"
        f"{item.source_version}|{item.state}"
    ).encode("utf-8")
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"), message, hashlib.sha256,
    ).hexdigest()
    now = timezone.now()
    # Serialize saves for the same patient and bound the inbox to 20 items.
    get_user_model().objects.select_for_update().get(pk=request.user.pk)
    # Serialize against D2 revoke and global consent withdrawal: both lock
    # the patient profile before deleting stored notices.
    BasePatientProfile.objects.select_for_update().filter(
        patient=request.user,
    ).first()
    _require_opt_in(request.user)
    D2InAppNotice.objects.filter(patient=request.user, expires_at__lte=now).delete()
    existing = D2InAppNotice.objects.filter(
        patient=request.user, signature=signature,
    ).first()
    if existing is None and D2InAppNotice.objects.filter(
        patient=request.user,
    ).count() >= MAX_ITEMS:
        raise HttpError(429, "Saved preview limit reached")
    row, created = D2InAppNotice.objects.get_or_create(
        patient=request.user, signature=signature,
        defaults={"kind": item.kind, "expires_at": now + TTL},
    )
    return {"created": created, "delivery_enabled": False, "item": _present(row)}


@router.put(PATH + "/{notice_id}/read")
@transaction.atomic
def mark_inbox_read(request, notice_id: int):
    _require_cookie_session_csrf(request)
    _require_opt_in(request.user)
    now = timezone.now()
    updated = D2InAppNotice.objects.filter(
        pk=notice_id, patient=request.user, expires_at__gt=now,
        read_at__isnull=True,
    ).update(read_at=now)
    row = D2InAppNotice.objects.filter(
        pk=notice_id, patient=request.user, expires_at__gt=now,
    ).first()
    if row is None:
        raise HttpError(404, "Notice not found")
    return {"updated": bool(updated), "item": _present(row)}


@router.delete(PATH + "/{notice_id}")
@transaction.atomic
def delete_inbox_item(request, notice_id: int):
    _require_cookie_session_csrf(request)
    _require_opt_in(request.user)
    deleted, _ = D2InAppNotice.objects.filter(
        pk=notice_id, patient=request.user,
    ).delete()
    if not deleted:
        raise HttpError(404, "Notice not found")
    return {"deleted": True}
