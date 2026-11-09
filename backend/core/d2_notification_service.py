"""D2 authoritative non-clinical events only; no LLM, push or patient text."""
from __future__ import annotations

import hashlib
import hmac
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.models.d2_notification import (
    D2Notification,
    D2NotificationPreference,
    D2ProactiveEmissionReceipt,
)

NOTICE_VERSION = "d2.inapp.proactivity.2026-11-08.v1"
NOTICES = {
    "fr": "IAMINA peut proposer au maximum deux informations non medicales en sept jours, et une par jour. Desactivez cette option a tout moment. Aucun rappel de traitement ni notification push.",
    "en": "IAMINA may offer at most two non-medical updates in seven days, and one per day. You can turn this off at any time. No treatment reminders or push notifications.",
    "ar": "يمكن لإيامينا اقتراح إشعارين غير طبيين كحد أقصى خلال سبعة أيام، وإشعار واحد في اليوم. يمكنك إيقاف ذلك في أي وقت. دون تذكيرات علاجية أو إشعارات فورية.",
}
TTL = timedelta(days=7)
CAP_WEEK = 2
CAP_DAY = 1
MAX_INBOX = 40

# Verified producer code and authoritative immutable server record identifier.
EVENT_SOURCES = {
    "ai_consent_given": "consent_receipt",
    "ai_consent_withdrawn": "consent_receipt",
}
PROACTIVE_SOURCES = {
    "language_pref_available": "locale_preference",
}


def notice_contract(locale: str) -> dict[str, str]:
    lang = locale.split("-", 1)[0].lower()
    if lang not in NOTICES:
        lang = "fr"
    text = NOTICES[lang]
    return {
        "locale": lang, "notice_version": NOTICE_VERSION,
        "notice_text": text,
        "notice_digest": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def _key(patient_id: int, code: str, source_pk: int) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        f"d2|{patient_id}|{code}|{source_pk}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _valid_preference(pref: D2NotificationPreference | None) -> bool:
    if pref is None or pref.proactive_opt_in is not True or pref.granted_at is None:
        return False
    return any(
        pref.notice_version == NOTICE_VERSION
        and pref.notice_digest == notice_contract(locale)["notice_digest"]
        for locale in NOTICES
    )


@transaction.atomic
def record_verified_event(*, patient_id: int, code: str, source: str, source_pk: int):
    """Only call after a real account-consent receipt change was committed here.

    A source identifier is never accepted from a user-facing API. The receiver
    proves the receipt belongs to this patient and its state matches the event.
    """
    if type(patient_id) is not int or patient_id <= 0:
        raise ValueError("Invalid patient identity")
    if type(source_pk) is not int or source_pk <= 0:
        raise ValueError("Invalid source identity")
    if EVENT_SOURCES.get(code) != source:
        raise ValueError("Unrecognized D2 event source")
    from core.models import AIConsentReceipt

    receipt = AIConsentReceipt.objects.filter(pk=source_pk, patient_id=patient_id).first()
    if receipt is None:
        raise ValueError("Unverified patient-owned consent receipt")
    if code == "ai_consent_given" and receipt.revoked_at is not None:
        raise ValueError("Consent receipt already revoked")
    if code == "ai_consent_withdrawn" and receipt.revoked_at is None:
        raise ValueError("No verified withdrawal")
    now = timezone.now()
    key = _key(patient_id, code, source_pk)
    # No destructive quota for factual account/security events.
    notice, created = D2Notification.objects.get_or_create(
        patient_id=patient_id,
        event_key=key,
        defaults={
            "kind": "event", "code": code, "created_at": now,
            "expires_at": now + TTL,
        },
    )
    # Hard account-bound cap: only code-only in-app rows are removed here;
    # underlying authoritative account receipts remain intact.
    old_ids = list(
        D2Notification.objects.filter(patient_id=patient_id)
        .order_by("-created_at", "-id")
        .values_list("pk", flat=True)[MAX_INBOX:]
    )
    if old_ids:
        D2Notification.objects.filter(patient_id=patient_id, pk__in=old_ids).delete()
    return notice, created


@transaction.atomic
def maybe_record_language_preference(*, patient_id: int):
    """One factual, optional, non-clinical in-app hint, only after explicit opt-in."""
    if type(patient_id) is not int or patient_id <= 0:
        return None
    pref = D2NotificationPreference.objects.select_for_update().filter(
        patient_id=patient_id,
    ).first()
    if not _valid_preference(pref):
        return None
    from core.models import BasePatientProfile
    from core.models.locale import PatientLocalePreference

    profile = BasePatientProfile.objects.filter(patient_id=patient_id).first()
    if profile is None:
        return None
    locale = PatientLocalePreference.objects.filter(profile=profile).first()
    if locale is None or locale.ui_language_provenance == "user_confirmed":
        return None
    now = timezone.now()
    key = _key(patient_id, "language_pref_available", locale.pk)
    if D2Notification.objects.filter(patient_id=patient_id, event_key=key).exists():
        return None
    cutoff_week = now - timedelta(days=7)
    cutoff_day = now - timedelta(hours=24)
    # A revoked notice must disappear immediately, but deleting it must NOT
    # reset anti-spam limits. Minimal HMAC+time receipts remain for seven days,
    # with no rendered content and no clinical fields.
    recent = D2ProactiveEmissionReceipt.objects.filter(
        patient_id=patient_id, emitted_at__gt=cutoff_week,
    )
    if recent.filter(event_key=key).exists():
        return None
    if recent.count() >= CAP_WEEK or recent.filter(emitted_at__gt=cutoff_day).exists():
        return None
    if D2Notification.objects.filter(
        patient_id=patient_id, expires_at__gt=now,
    ).count() >= MAX_INBOX:
        return None
    # Reuse of an identical source is permitted only once its receipt is
    # older than the rolling seven-day suppression window.
    D2ProactiveEmissionReceipt.objects.filter(
        patient_id=patient_id, event_key=key, emitted_at__lte=cutoff_week,
    ).delete()
    notice = D2Notification.objects.create(
        patient_id=patient_id,
        event_key=key,
        kind="proactive",
        code="language_pref_available",
        created_at=now,
        expires_at=now + TTL,
    )
    D2ProactiveEmissionReceipt.objects.create(
        patient_id=patient_id, event_key=key, emitted_at=now,
    )
    return notice
