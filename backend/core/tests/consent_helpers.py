from __future__ import annotations

from django.utils import timezone

from core.consent_notice import expected_notice_claim
from core.models import BasePatientProfile


def grant_current_ai_consent(user, *, locale: str = "fr", **profile_defaults):
    """Persist one exact current AI-consent proof for test fixtures."""
    claim = expected_notice_claim(locale)
    defaults = {
        **profile_defaults,
        "ai_consent_given_at": timezone.now(),
        "ai_consent_notice_version": claim.version,
        "ai_consent_notice_hash": claim.notice_hash,
        "ai_consent_notice_locale": claim.locale,
    }
    profile, _ = BasePatientProfile.objects.update_or_create(
        patient=user,
        defaults=defaults,
    )
    return profile
