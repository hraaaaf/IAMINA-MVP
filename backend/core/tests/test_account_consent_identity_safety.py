"""Identity-safety regression tests for account consent operations."""

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User

from core.api.v1.account import ConsentGrantSchema, give_consent
from core.consent_notice import expected_notice_claim
from core.models import BasePatientProfile


@pytest.mark.django_db
def test_consent_profile_creation_does_not_invent_demographics(monkeypatch):
    user = User.objects.create_user(username="consent-patient")
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
    assert response["ai_consent_given"] is True
    assert profile.ai_consent_given_at is not None
    assert profile.ai_consent_notice_version == claim.version
    assert profile.ai_consent_notice_hash == claim.notice_hash
    assert profile.ai_consent_notice_locale == claim.locale
    assert profile.date_of_birth is None
    assert profile.gender is None
    assert profile.weight is None
    assert profile.height is None
