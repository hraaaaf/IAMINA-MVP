"""Sovereign IAMINA bearer issuance, verification and revocation tests."""

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User

from core.models import BasePatientProfile
from core.native_auth import (
    NativeTokenError,
    issue_native_token,
    revoke_native_tokens,
    verify_native_token,
)
from diabetes.api.v1.security import HybridBearerAuth


@pytest.mark.django_db
def test_native_token_round_trip_and_hybrid_bearer_resolution():
    user = User.objects.create_user(username="native", is_active=True)
    BasePatientProfile.objects.create(patient=user)
    token = issue_native_token(user)

    assert token.startswith("iamina.")
    assert verify_native_token(token).pk == user.pk

    request = SimpleNamespace(user=None)
    resolved = HybridBearerAuth().authenticate(request, token)
    assert resolved.pk == user.pk
    assert request.user.pk == user.pk


@pytest.mark.django_db
def test_native_token_revocation_invalidates_every_prior_token():
    user = User.objects.create_user(username="native")
    profile = BasePatientProfile.objects.create(patient=user)
    first = issue_native_token(user)
    second = issue_native_token(user)

    revoke_native_tokens(user)
    profile.refresh_from_db()
    assert profile.auth_token_version == 1

    for token in (first, second):
        with pytest.raises(NativeTokenError):
            verify_native_token(token)

    replacement = issue_native_token(user)
    assert verify_native_token(replacement).pk == user.pk


@pytest.mark.django_db
def test_native_token_fails_closed_for_tamper_unknown_or_inactive_user():
    user = User.objects.create_user(username="native")
    BasePatientProfile.objects.create(patient=user)
    token = issue_native_token(user)

    with pytest.raises(NativeTokenError):
        verify_native_token(token + "tamper")

    user.is_active = False
    user.save(update_fields=["is_active"])
    with pytest.raises(NativeTokenError):
        verify_native_token(token)

    request = SimpleNamespace(user=None)
    assert HybridBearerAuth().authenticate(request, token) is None


def test_non_iamina_token_is_not_accepted_by_native_verifier():
    with pytest.raises(NativeTokenError):
        verify_native_token("firebase-looking-token")
