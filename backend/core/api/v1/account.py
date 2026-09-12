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
from django.db import transaction
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel

from core.account_hooks import run_account_delete_hooks
from core.audit import record_audit
from core.consent_notice import profile_has_current_consent, validate_notice_claim
from core.models import AIConsentReceipt, AIMediaConsentGrant, BasePatientProfile
from core.models.erasure_record import ErasureRecord

logger = logging.getLogger(__name__)
router = Router(tags=["account"])


class ConsentStatusSchema(BaseModel):
    ai_consent_given: bool
    ai_consent_given_at: str | None
    notice_version: str | None = None
    notice_hash: str | None = None
    locale: str | None = None


class ConsentGrantSchema(BaseModel):
    notice_version: str
    notice_hash: str
    locale: str


class DeleteConfirmSchema(BaseModel):
    confirm: str


def _consent_status(base: BasePatientProfile | None) -> dict:
    effective = base is not None and profile_has_current_consent(base)
    given_at = base.ai_consent_given_at if effective else None
    return {
        "ai_consent_given": effective,
        "ai_consent_given_at": given_at.isoformat() if given_at else None,
        "notice_version": base.ai_consent_notice_version if effective else None,
        "notice_hash": base.ai_consent_notice_hash if effective else None,
        "locale": base.ai_consent_notice_locale if effective else None,
    }


@router.get("/account/consent", response=ConsentStatusSchema)
def get_consent_status(request):
    try:
        base = BasePatientProfile.objects.get(patient=request.user)
    except BasePatientProfile.DoesNotExist:
        return _consent_status(None)
    return _consent_status(base)


@router.post("/account/consent", response=ConsentStatusSchema)
def give_consent(request, data: ConsentGrantSchema):
    """Bind explicit AI consent to the exact rendered notice the patient accepted."""
    try:
        claim = validate_notice_claim(
            version=data.notice_version,
            notice_hash=data.notice_hash,
            locale=data.locale,
        )
    except ValueError as exc:
        raise HttpError(422, str(exc)) from exc

    with transaction.atomic():
        base, _ = BasePatientProfile.objects.select_for_update().get_or_create(
            patient=request.user
        )
        if (
            profile_has_current_consent(base)
            and base.ai_consent_notice_version == claim.version
            and base.ai_consent_notice_hash == claim.notice_hash
            and base.ai_consent_notice_locale == claim.locale
        ):
            return _consent_status(base)

        now = timezone.now()
        AIConsentReceipt.objects.filter(
            patient=request.user,
            revoked_at__isnull=True,
        ).update(revoked_at=now)
        # Granular grants belong to one global-consent epoch. Re-consent requires
        # explicit re-grant rather than silently carrying an older media decision.
        AIMediaConsentGrant.objects.filter(
            patient=request.user,
            revoked_at__isnull=True,
        ).update(revoked_at=now)

        AIConsentReceipt.objects.create(
            patient=request.user,
            notice_version=claim.version,
            notice_hash=claim.notice_hash,
            notice_locale=claim.locale,
            granted_at=now,
        )
        base.ai_consent_given_at = now
        base.ai_consent_notice_version = claim.version
        base.ai_consent_notice_hash = claim.notice_hash
        base.ai_consent_notice_locale = claim.locale
        base.save(
            update_fields=[
                "ai_consent_given_at",
                "ai_consent_notice_version",
                "ai_consent_notice_hash",
                "ai_consent_notice_locale",
            ]
        )
        record_audit(request.user, "consent_given", request)

    return _consent_status(base)


@router.delete("/account/consent", response=ConsentStatusSchema)
def withdraw_consent(request):
    """Withdraw AI processing consent and every grant derived from that epoch."""
    now = timezone.now()
    try:
        with transaction.atomic():
            base = BasePatientProfile.objects.select_for_update().get(patient=request.user)
            had_consent = base.ai_consent_given_at is not None
            base.ai_consent_given_at = None
            base.ai_consent_notice_version = None
            base.ai_consent_notice_hash = None
            base.ai_consent_notice_locale = None
            base.save(
                update_fields=[
                    "ai_consent_given_at",
                    "ai_consent_notice_version",
                    "ai_consent_notice_hash",
                    "ai_consent_notice_locale",
                ]
            )
            AIConsentReceipt.objects.filter(
                patient=request.user,
                revoked_at__isnull=True,
            ).update(revoked_at=now)
            AIMediaConsentGrant.objects.filter(
                patient=request.user,
                revoked_at__isnull=True,
            ).update(revoked_at=now)
            if had_consent:
                record_audit(request.user, "consent_withdrawn", request)
    except BasePatientProfile.DoesNotExist:
        pass
    return _consent_status(None)


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
