"""
RGPD account management — Art. 7 (consent) + Art. 17 (erasure).

DELETE /api/v1/account         — full cascade erasure
POST   /api/v1/account/consent — record explicit AI consent
DELETE /api/v1/account/consent — withdraw AI consent
GET    /api/v1/account/consent — consent status
"""

import logging

import firebase_admin.auth
from django.contrib.auth import logout
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
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
    confirm: str


@router.get("/account/consent", response=ConsentStatusSchema)
def get_consent_status(request):
    try:
        base = BasePatientProfile.objects.get(patient=request.user)
    except BasePatientProfile.DoesNotExist:
        return {"ai_consent_given": False, "ai_consent_given_at": None}

    given_at = base.ai_consent_given_at
    return {
        "ai_consent_given": given_at is not None,
        "ai_consent_given_at": given_at.isoformat() if given_at else None,
    }


@router.post("/account/consent", response=ConsentStatusSchema)
def give_consent(request):
    """Record explicit AI processing consent without inventing patient facts."""
    base, _ = BasePatientProfile.objects.get_or_create(patient=request.user)
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
    """Withdraw AI processing consent. AI features remain suspended until re-consent."""
    try:
        base = BasePatientProfile.objects.get(patient=request.user)
        if base.ai_consent_given_at is not None:
            base.ai_consent_given_at = None
            base.save(update_fields=["ai_consent_given_at"])
            record_audit(request.user, "consent_withdrawn", request)
    except BasePatientProfile.DoesNotExist:
        pass
    return {"ai_consent_given": False, "ai_consent_given_at": None}


@router.delete("/account")
def delete_account(request, data: DeleteConfirmSchema):
    """Delete the authenticated patient's account and associated patient data."""
    if data.confirm != "DELETE MY ACCOUNT":
        raise HttpError(400, "Confirmation string mismatch. Send: DELETE MY ACCOUNT")

    user = request.user
    patient_id = user.id
    username = user.username

    try:
        base = BasePatientProfile.objects.get(patient=user)
        firebase_uid = base.firebase_uid or ""
    except BasePatientProfile.DoesNotExist:
        firebase_uid = ""

    try:
        record_audit(user, "account_deleted", request, username=username)

        try:
            run_account_delete_hooks(patient_id, firebase_uid)
        except RuntimeError as hook_error:
            logger.error(
                "delete_account blocked by hook failures patient=%s category=cleanup_hook",
                patient_id,
            )
            raise HttpError(
                500,
                "Erasure blocked by cleanup hook failure — contact support.",
            ) from hook_error

        if firebase_uid:
            try:
                firebase_admin.auth.delete_user(firebase_uid)
            except Exception:
                logger.exception(
                    "firebase_delete_failed patient=%s",
                    patient_id,
                )

        user.delete()
        ErasureRecord.objects.create(
            patient_id_snapshot=patient_id,
            firebase_uid_snapshot=firebase_uid,
        )
        logout(request)
        logger.info("RGPD erasure complete for patient_id=%s", patient_id)
        return {"detail": "Account and all associated data deleted."}

    except HttpError:
        raise
    except Exception:
        logger.exception("delete_account failed for patient=%s", patient_id)
        return {"detail": "Erasure failed — contact support."}, 500
