"""
RGPD account management — Art. 7 (consent) + Art. 17 (erasure).

DELETE /api/v1/account        — full cascade erasure
POST   /api/v1/account/consent — record explicit AI consent
DELETE /api/v1/account/consent — withdraw AI consent
GET    /api/v1/account/consent — consent status
"""
import logging

import firebase_admin.auth
from django.contrib.auth import logout
from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from core.account_hooks import run_account_delete_hooks
from core.audit import record_audit
from core.models import BasePatientProfile
from core.models.erasure_record import ErasureRecord

logger = logging.getLogger(__name__)
router = Router(tags=["account"])


class ConsentStatusSchema(BaseModel):
    ai_consent_given: bool
    ai_consent_given_at: str | None


class DeleteConfirmSchema(BaseModel):
    confirm: str  # must equal "DELETE MY ACCOUNT"


# ──────────────────────────────────────────────────────────────
# CONSENT
# ──────────────────────────────────────────────────────────────

@router.get("/account/consent", response=ConsentStatusSchema)
def get_consent_status(request):
    try:
        base = BasePatientProfile.objects.get(patient=request.user)
        given_at = base.ai_consent_given_at
        return {
            "ai_consent_given": given_at is not None,
            "ai_consent_given_at": given_at.isoformat() if given_at else None,
        }
    except BasePatientProfile.DoesNotExist:
        return {"ai_consent_given": False, "ai_consent_given_at": None}


@router.post("/account/consent", response=ConsentStatusSchema)
def give_consent(request):
    """Record explicit AI processing consent (RGPD Art. 7)."""
    from datetime import date as _date
    base, _ = BasePatientProfile.objects.get_or_create(
        patient=request.user,
        defaults={"date_of_birth": _date(1980, 1, 1)},
    )
    if base.ai_consent_given_at is None:
        base.ai_consent_given_at = timezone.now()
        base.save(update_fields=["ai_consent_given_at"])
        record_audit(request.user, "consent_given", request)
    return {
        "ai_consent_given": True,
        "ai_consent_given_at": base.ai_consent_given_at.isoformat(),
    }


@router.delete("/account/consent", response=ConsentStatusSchema)
def withdraw_consent(request):
    """Withdraw AI processing consent. AI features are suspended until re-consent."""
    try:
        base = BasePatientProfile.objects.get(patient=request.user)
        if base.ai_consent_given_at is not None:
            base.ai_consent_given_at = None
            base.save(update_fields=["ai_consent_given_at"])
            record_audit(request.user, "consent_withdrawn", request)
    except BasePatientProfile.DoesNotExist:
        pass
    return {"ai_consent_given": False, "ai_consent_given_at": None}


# ──────────────────────────────────────────────────────────────
# ACCOUNT ERASURE (RGPD Art. 17)
# ──────────────────────────────────────────────────────────────

@router.delete("/account")
def delete_account(request, data: DeleteConfirmSchema):
    """
    Full RGPD erasure. Cascade-deletes all patient data.
    Requires explicit confirmation string to prevent accidental calls.

    Preserved (immutable audit trail):
      - AuditLog rows (patient FK → NULL)
    """
    if data.confirm != "DELETE MY ACCOUNT":
        from ninja.errors import HttpError
        raise HttpError(400, "Confirmation string mismatch. Send: DELETE MY ACCOUNT")

    user = request.user
    patient_id = user.id
    firebase_uid = getattr(user, "firebase_uid", "") or ""
    username = user.username

    # Resolve firebase_uid from BasePatientProfile if not on User directly
    if not firebase_uid:
        try:
            base = BasePatientProfile.objects.get(patient=user)
            firebase_uid = base.firebase_uid or ""
        except Exception:
            firebase_uid = ""

    try:
        # Audit before deletion (FK still valid here)
        record_audit(user, "account_deleted", request, username=username)

        # --- RGPD Art. 17: run registered cleanup hooks BEFORE user deletion ---
        # Any hook failure raises RuntimeError and blocks the deletion.
        try:
            run_account_delete_hooks(patient_id, firebase_uid)
        except RuntimeError as hook_err:
            logger.error(
                "delete_account blocked by hook failures patient=%s err=%s",
                patient_id, hook_err,
            )
            from ninja.errors import HttpError
            raise HttpError(500, "Erasure blocked by cleanup hook failure — contact support.")

        # --- Delete Firebase Auth user (non-blocking: log failure but continue) ---
        if firebase_uid:
            try:
                firebase_admin.auth.delete_user(firebase_uid)
            except Exception as fb_err:
                logger.error(
                    "firebase_delete_failed uid=%s err=%s", firebase_uid, fb_err
                )

        # --- Delete Django User — CASCADE handles: ---
        # LogEntry, AIChatMessage, BasePatientProfile → DiabetesProfile, IAminaMemorySnapshot
        # AuditLog.patient → SET_NULL (rows preserved)
        user.delete()

        # --- Create immutable erasure audit record ---
        ErasureRecord.objects.create(
            patient_id_snapshot=patient_id,
            firebase_uid_snapshot=firebase_uid,
        )

        logout(request)
        logger.info("RGPD erasure complete for patient_id=%s username=%s", patient_id, username)
        return {"detail": "Account and all associated data deleted."}

    except Exception:
        logger.exception("delete_account failed for patient=%s", patient_id)
        return {"detail": "Erasure failed — contact support."}, 500
