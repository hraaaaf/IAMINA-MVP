"""G3: password recovery cannot resurrect a patient under erasure.

No emails are actually sent; all identities are synthetic and ORM-local.
"""
import json

import pytest
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.test import Client
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from core.models import BasePatientProfile
from core.models.erasure_attempt import ErasureAttempt


@pytest.mark.django_db
@pytest.mark.parametrize(
    "state",
    [
        ErasureAttempt.State.PENDING,
        ErasureAttempt.State.IN_PROGRESS,
        ErasureAttempt.State.REVIEW_REQUIRED,
    ],
)
def test_preexisting_password_reset_link_is_denied_after_erasure_claim(
    state, monkeypatch
):
    user = User.objects.create_user(
        username=f"reset-lock-{state}",
        email=f"reset-lock-{state}@example.invalid",
        password="SyntheticBeforeReset!2026",
    )
    BasePatientProfile.objects.create(patient=user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    old_token = default_token_generator.make_token(user)
    ErasureAttempt.objects.create(
        patient_id_snapshot=user.pk, state=state
    )

    def never_send(*args, **kwargs):
        pytest.fail("Password recovery email must not be sent during erasure")

    monkeypatch.setattr("core.api.v1.auth.send_mail", never_send)
    client = Client()
    requested = client.post(
        "/api/v1/auth/password/reset/request",
        data=json.dumps({"email": user.email}),
        content_type="application/json",
    )
    assert requested.status_code == 200
    assert requested.json()["detail"] == (
        "If the account exists, the recovery request was accepted"
    )

    rejected = client.post(
        "/api/v1/auth/password/reset/confirm",
        data=json.dumps({
            "uid": uid,
            "token": old_token,
            "new_password": "SyntheticAfterReset!2026",
        }),
        content_type="application/json",
    )
    assert rejected.status_code == 400
    user.refresh_from_db()
    assert user.check_password("SyntheticBeforeReset!2026")
    assert not user.check_password("SyntheticAfterReset!2026")
    assert ErasureAttempt.objects.get(
        patient_id_snapshot=user.pk
    ).state == state


@pytest.mark.django_db
def test_normal_reset_outside_erasure_is_not_blocked(monkeypatch):
    user = User.objects.create_user(
        username="reset-lock-control",
        email="reset-lock-control@example.invalid",
        password="SyntheticBeforeReset!2026",
    )
    BasePatientProfile.objects.create(patient=user)
    called = []

    def mail_stub(**kwargs):
        called.append(kwargs["recipient_list"])
        return 1

    monkeypatch.setattr("core.api.v1.auth.send_mail", mail_stub)
    response = Client().post(
        "/api/v1/auth/password/reset/request",
        data=json.dumps({"email": user.email}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert called == [[user.email]]
