"""One-shot W01-G5 synthetic-only Preview erasure. Never for patient data.

This endpoint is disabled by default and is protected by Vercel SSO at the
edge, an explicit per-Preview environment gate, a fresh signed challenge and
an exact two-user synthetic-only PostgreSQL preflight. It must be REMOVED
before W01 is merged; it is not an administrative account-deletion feature.
"""
from __future__ import annotations

import os

from django.contrib.auth.models import User
from django.core import signing
from django.db import connection, transaction
from django.utils import timezone
from ninja import Router, Schema
from ninja.errors import HttpError

from amina.preview_db_identity import preview_identity_allowed, read_synthetic_identity
from core.account_hooks import run_account_delete_hooks
from core.audit import record_audit
from core.models.erasure_record import ErasureRecord
from diabetes.synthetic_preview_erasure import (
    can_erase_synthetic_without_cache,
    synthetic_preview_without_redis,
)

router = Router(tags=["ops"])
_IDS = (3, 4)
_SALT = "iamina.w01g5.synthetic-erasure-v1"


class SyntheticCleanupConfirm(Schema):
    confirm: str
    challenge: str


def _check_scope(request) -> None:
    if not (
        os.environ.get("IAMINA_W01_G5_CLEANUP_ENABLED") == "true"
        and synthetic_preview_without_redis()
        and preview_identity_allowed(request.headers.get("host", ""))
    ):
        raise HttpError(404, "Not found")


def _assert_target() -> None:
    # This is NOT a general-purpose erasure route. Never act on other IDs.
    users = list(User.objects.filter(id__in=_IDS).order_by("id"))
    if len(users) != 2 or User.objects.exclude(id__in=_IDS).exists():
        raise HttpError(409, "Synthetic target is not the exact expected pair")
    if not all(can_erase_synthetic_without_cache(user.pk, "") for user in users):
        raise HttpError(409, "Synthetic deletion invariants not met")


def _check_runtime_db() -> None:
    try:
        with connection.cursor() as cursor:
            identity = read_synthetic_identity(cursor)
    except Exception as exc:
        raise HttpError(503, "Synthetic database identity unavailable") from exc
    if not identity:
        raise HttpError(503, "Synthetic database identity mismatch")


@router.get("/ops/w01-g5-synthetic-cleanup", auth=None, include_in_schema=False)
def synthetic_cleanup_preflight(request):
    _check_scope(request)
    _check_runtime_db()
    _assert_target()
    challenge = signing.dumps({"ids": list(_IDS)}, salt=_SALT)
    return {"eligible_accounts": 2, "challenge": challenge}


@router.post("/ops/w01-g5-synthetic-cleanup", auth=None, include_in_schema=False)
def synthetic_cleanup_execute(request, data: SyntheticCleanupConfirm):
    _check_scope(request)
    if data.confirm != "DELETE TWO W01 SYNTHETIC ACCOUNTS":
        raise HttpError(400, "Explicit synthetic cleanup confirmation required")
    try:
        challenge = signing.loads(data.challenge, salt=_SALT, max_age=300)
    except (signing.BadSignature, signing.SignatureExpired) as exc:
        raise HttpError(403, "Invalid or expired cleanup challenge") from exc
    if challenge != {"ids": list(_IDS)}:
        raise HttpError(403, "Cleanup challenge scope mismatch")
    _check_runtime_db()
    # Hold account locks while re-verifying all non-PHI synthetic invariants.
    with transaction.atomic():
        locked = list(User.objects.select_for_update().filter(id__in=_IDS).order_by("id"))
        _assert_target()
        if [user.id for user in locked] != list(_IDS):
            raise HttpError(409, "Synthetic account set changed")
        for user in locked:
            # Reuse the real deletion hooks, not manual SQL / raw cascade.
            run_account_delete_hooks(user.id, "")
            record_audit(user, "account_deleted", request, username=user.username)
            patient_id = user.id
            user.delete()
            ErasureRecord.objects.create(
                patient_id_snapshot=patient_id, firebase_uid_snapshot="",
                completed_at=timezone.now(),
            )
        remaining = User.objects.count()
        if remaining != 0:
            raise HttpError(409, "Synthetic cleanup postcondition failed")
    return {"deleted_accounts": 2, "remaining_accounts": 0}
