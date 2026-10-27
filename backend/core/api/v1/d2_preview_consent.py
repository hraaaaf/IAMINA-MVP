"""Authenticated D2 consent-only API. No producer, inbox, browser push or egress."""
from typing import Literal

from django.db import transaction
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel, ConfigDict

from amina.vercel_session_auth import check_iamina_csrf
from core.audit import record_audit
from core.consent_notice import profile_has_current_consent
from core.d2_preview_notice import expected_d2_notice, validate_d2_notice
from core.models import BasePatientProfile, D2PreviewConsentReceipt, D2InAppNotice

router = Router(tags=["d2-preview-consent"])
PATH = "/account/notification-preview-consent"


class D2GrantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    locale: str
    notice_version: str
    notice_hash: str
    acknowledgment: Literal["ENABLE_PREVIEW_ONLY"]


def _require_cookie_session_csrf(request):
    """Consent mutations with any cookie must prove CSRF, even in Ninja views.

    Django-Ninja wraps its endpoint as csrf_exempt, so Django's outer
    middleware does not enforce the token there. Bearer-only API callers
    remain stateless; mixed cookie+Authorization requests are ambiguous and
    fail closed, never falling back to a session identity.
    """
    if not request.COOKIES:
        return
    if request.META.get("HTTP_AUTHORIZATION", "").strip():
        raise HttpError(403, "Mixed cookie and Authorization not allowed")
    if check_iamina_csrf(request) is not None:
        raise HttpError(403, "CSRF check failed")


def _status(user, locale="fr"):
    try:
        requested_notice = expected_d2_notice(locale)
    except ValueError as exc:
        raise HttpError(422, str(exc)) from exc

    profile = BasePatientProfile.objects.filter(patient=user).first()
    active = D2PreviewConsentReceipt.objects.filter(
        patient=user, revoked_at__isnull=True,
    ).first()
    valid_receipt = False
    if active is not None:
        try:
            validate_d2_notice(
                version=active.notice_version, notice_hash=active.notice_hash,
                locale=active.notice_locale,
            )
            valid_receipt = True
        except ValueError:
            pass
    opted_in = bool(
        profile is not None
        and profile_has_current_consent(profile)
        and active is not None and valid_receipt
        and active.global_consent_epoch == profile.ai_consent_given_at
    )
    return {
        "purpose": "proactive_in_app_preview",
        "opted_in": opted_in,
        "delivery_enabled": False,
        "browser_push_enabled": False,
        "notice_version": requested_notice.version,
        "notice_hash": requested_notice.notice_hash,
        "locale": requested_notice.locale,
        "notice_text": requested_notice.text,
        "granted_at": active.granted_at.isoformat() if opted_in else None,
    }


@router.get(PATH)
def get_d2_preview_consent(request, locale: str = "fr"):
    return _status(request.user, locale)


@router.put(PATH)
@transaction.atomic
def grant_d2_preview_consent(request, data: D2GrantRequest):
    _require_cookie_session_csrf(request)
    try:
        notice = validate_d2_notice(
            version=data.notice_version, notice_hash=data.notice_hash,
            locale=data.locale,
        )
    except ValueError as exc:
        raise HttpError(422, str(exc)) from exc

    profile = BasePatientProfile.objects.select_for_update().filter(
        patient=request.user,
    ).first()
    if profile is None or not profile_has_current_consent(profile):
        raise HttpError(409, "Current global AI consent required before D2 preview consent")
    active = D2PreviewConsentReceipt.objects.filter(
        patient=request.user, revoked_at__isnull=True,
    ).first()
    if (
        active is not None
        and active.global_consent_epoch == profile.ai_consent_given_at
        and active.notice_version == notice.version
        and active.notice_hash == notice.notice_hash
        and active.notice_locale == notice.locale
    ):
        return _status(request.user, notice.locale)

    now = timezone.now()
    D2PreviewConsentReceipt.objects.filter(
        patient=request.user, revoked_at__isnull=True,
    ).update(revoked_at=now)
    D2PreviewConsentReceipt.objects.create(
        patient=request.user, notice_version=notice.version,
        notice_hash=notice.notice_hash, notice_locale=notice.locale,
        global_consent_epoch=profile.ai_consent_given_at, granted_at=now,
    )
    record_audit(request.user, "d2_preview_consent_given", request)
    return _status(request.user, notice.locale)


@router.delete(PATH)
@transaction.atomic
def revoke_d2_preview_consent(request):
    _require_cookie_session_csrf(request)
    BasePatientProfile.objects.select_for_update().filter(patient=request.user).first()
    revoked = D2PreviewConsentReceipt.objects.filter(
        patient=request.user, revoked_at__isnull=True,
    ).update(revoked_at=timezone.now())
    # A revoked preview grant cannot leave patient-visible derived notices behind.
    D2InAppNotice.objects.filter(patient=request.user).delete()
    if revoked:
        record_audit(request.user, "d2_preview_consent_withdrawn", request)
    return _status(request.user)
