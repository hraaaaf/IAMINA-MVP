"""Versioned patient-consent notice contract.

The client must present one exact, fingerprinted notice before external AI
processing can be enabled.  Locale aliases are explicit and unknown claims fail
closed.  Hashes are SHA-256 fingerprints of the nine rendered consent strings
listed in ``NOTICE_FIELD_ORDER`` using ``key=value`` lines joined by ``\n``.
"""

from __future__ import annotations

from dataclasses import dataclass

NOTICE_VERSION = "2026-09-12.1"
NOTICE_FIELD_ORDER = (
    "consentTitle",
    "consentHeadline",
    "consentBody",
    "consentDataPoint1",
    "consentDataPoint2",
    "consentDataPoint3",
    "dataPrivacyNote",
    "consentAccept",
    "consentDeclineWithoutAI",
)

NOTICE_HASHES = {
    "fr": "2fc950fc5dadb4add4dc8ad344c48126f2b81bbfa18654762d3bc879f15459cb",
    "en": "2673ef01615fff6fde9fb88bbeb33dec87da3a0c417d4bb854c7fa34867bd706",
    "ar": "2351b0e1ea0930ba874d9f2242d3fc22fc38da9c43adc571942a0f94d0a57b0d",
    # The current Darija UI renders the same Arabic consent copy.
    "ar-MA": "2351b0e1ea0930ba874d9f2242d3fc22fc38da9c43adc571942a0f94d0a57b0d",
}


@dataclass(frozen=True, slots=True)
class ConsentNoticeClaim:
    version: str
    notice_hash: str
    locale: str


def normalize_notice_locale(locale: str) -> str:
    value = (locale or "").strip()
    if value in NOTICE_HASHES:
        return value
    language = value.split("-", 1)[0].lower()
    if language in NOTICE_HASHES:
        return language
    raise ValueError("unsupported consent notice locale")


def expected_notice_claim(locale: str) -> ConsentNoticeClaim:
    normalized = normalize_notice_locale(locale)
    return ConsentNoticeClaim(
        version=NOTICE_VERSION,
        notice_hash=NOTICE_HASHES[normalized],
        locale=normalized,
    )


def validate_notice_claim(*, version: str, notice_hash: str, locale: str) -> ConsentNoticeClaim:
    expected = expected_notice_claim(locale)
    if version != expected.version:
        raise ValueError("consent notice version mismatch")
    if notice_hash != expected.notice_hash:
        raise ValueError("consent notice hash mismatch")
    return expected


def profile_has_current_consent(profile) -> bool:
    """Return True only for a complete consent bound to the current notice."""
    if profile.ai_consent_given_at is None:
        return False
    try:
        claim = validate_notice_claim(
            version=profile.ai_consent_notice_version or "",
            notice_hash=profile.ai_consent_notice_hash or "",
            locale=profile.ai_consent_notice_locale or "",
        )
    except ValueError:
        return False
    return (
        profile.ai_consent_notice_version == claim.version
        and profile.ai_consent_notice_hash == claim.notice_hash
        and profile.ai_consent_notice_locale == claim.locale
    )
