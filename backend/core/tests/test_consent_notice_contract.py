import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User
from ninja.errors import HttpError

from core.api.v1.account import (
    ConsentGrantSchema,
    get_consent_status,
    give_consent,
    withdraw_consent,
)
from core.consent_notice import (
    NOTICE_FIELD_ORDER,
    NOTICE_HASHES,
    NOTICE_VERSION,
    expected_notice_claim,
    profile_has_current_consent,
    validate_notice_claim,
)
from core.models import AIConsentReceipt, BasePatientProfile


REPO_ROOT = Path(__file__).resolve().parents[3]


def _arb_hash(locale: str) -> str:
    data = json.loads(
        (REPO_ROOT / "frontend" / "lib" / "l10n" / f"app_{locale}.arb").read_text(
            encoding="utf-8"
        )
    )
    serialized = "\n".join(f"{key}={data[key]}" for key in NOTICE_FIELD_ORDER)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def test_notice_registry_matches_exact_rendered_arb_copy():
    assert NOTICE_HASHES["fr"] == _arb_hash("fr")
    assert NOTICE_HASHES["en"] == _arb_hash("en")
    assert NOTICE_HASHES["ar"] == _arb_hash("ar")
    assert NOTICE_HASHES["ar-MA"] == NOTICE_HASHES["ar"]


def test_notice_claim_is_exact_and_unknown_or_modified_claims_fail_closed():
    claim = expected_notice_claim("fr-FR")
    assert claim.version == NOTICE_VERSION
    assert claim.locale == "fr"

    with pytest.raises(ValueError, match="version mismatch"):
        validate_notice_claim(
            version="legacy",
            notice_hash=claim.notice_hash,
            locale="fr",
        )
    with pytest.raises(ValueError, match="hash mismatch"):
        validate_notice_claim(
            version=claim.version,
            notice_hash="0" * 64,
            locale="fr",
        )
    with pytest.raises(ValueError, match="unsupported"):
        validate_notice_claim(
            version=claim.version,
            notice_hash=claim.notice_hash,
            locale="xx",
        )


def test_timestamp_without_notice_evidence_is_not_current_consent():
    profile = SimpleNamespace(
        ai_consent_given_at=object(),
        ai_consent_notice_version=None,
        ai_consent_notice_hash=None,
        ai_consent_notice_locale=None,
    )
    assert profile_has_current_consent(profile) is False


@pytest.mark.django_db
def test_account_consent_creates_exact_receipt_and_withdrawal_revokes_it(monkeypatch):
    user = User.objects.create_user(username="versioned-consent-patient")
    request = SimpleNamespace(user=user)
    monkeypatch.setattr("core.api.v1.account.record_audit", lambda *args, **kwargs: None)
    claim = expected_notice_claim("fr")

    response = give_consent(
        request,
        ConsentGrantSchema(
            notice_version=claim.version,
            notice_hash=claim.notice_hash,
            locale=claim.locale,
        ),
    )

    profile = BasePatientProfile.objects.get(patient=user)
    receipt = AIConsentReceipt.objects.get(patient=user)
    assert response["ai_consent_given"] is True
    assert response["notice_version"] == claim.version
    assert response["notice_hash"] == claim.notice_hash
    assert response["locale"] == claim.locale
    assert profile_has_current_consent(profile) is True
    assert receipt.notice_version == claim.version
    assert receipt.notice_hash == claim.notice_hash
    assert receipt.notice_locale == claim.locale
    assert receipt.revoked_at is None

    withdrawn = withdraw_consent(request)
    receipt.refresh_from_db()
    profile.refresh_from_db()
    assert withdrawn["ai_consent_given"] is False
    assert receipt.revoked_at is not None
    assert profile_has_current_consent(profile) is False
    assert get_consent_status(request)["ai_consent_given"] is False


@pytest.mark.django_db
def test_account_consent_rejects_modified_notice_without_writing_state(monkeypatch):
    user = User.objects.create_user(username="modified-consent-patient")
    request = SimpleNamespace(user=user)
    monkeypatch.setattr("core.api.v1.account.record_audit", lambda *args, **kwargs: None)
    claim = expected_notice_claim("en")

    with pytest.raises(HttpError) as exc_info:
        give_consent(
            request,
            ConsentGrantSchema(
                notice_version=claim.version,
                notice_hash="f" * 64,
                locale=claim.locale,
            ),
        )

    assert exc_info.value.status_code == 422
    assert AIConsentReceipt.objects.filter(patient=user).count() == 0
    assert BasePatientProfile.objects.filter(patient=user).count() == 0
