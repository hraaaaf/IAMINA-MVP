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
    "fr": "6da07cc7cb585b7690e181563984806163ceb667682203afa39575b3221e5cbd",
    "en": "111609419beaef233463bc8d91a691468ab16ffe80b8f817ba51e8d0667cc65c",
    "ar": "dc7978b3b20548e1327c03110adb9fb092a9af27b0eab35151143f89897b897",
    # The current Darija UI renders the same Arabic consent copy.
    "ar-MA": "dc7978b3b20548e1327c03110adb9fb092a9af27b0eab35151143f89897b897",
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
