"""Native password recovery remains enumeration-safe and revokes old tokens."""

import logging

import pytest
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from ninja.errors import HttpError

from core.api.v1.auth import (
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    confirm_password_reset,
    request_password_reset,
)
from core.native_auth import NativeTokenError, issue_native_token, verify_native_token


@pytest.mark.django_db
def test_reset_request_does_not_disclose_account_existence(monkeypatch):
    sent = []

    def _send_mail(**kwargs):
        sent.append(kwargs)
        return 1

    monkeypatch.setattr("core.api.v1.auth.send_mail", _send_mail)

    missing = request_password_reset(
        None,
        PasswordResetRequest(email="missing@example.test"),
    )
    user = User.objects.create_user(
        username="patient@example.test",
        email="patient@example.test",
        password="Current-passphrase-2026!",
    )
    existing = request_password_reset(
        None,
        PasswordResetRequest(email=user.email),
    )

    assert missing == existing == {
        "detail": "If the account exists, the recovery request was accepted"
    }
    assert len(sent) == 1
    assert sent[0]["fail_silently"] is False


@pytest.mark.django_db
def test_reset_request_hides_delivery_failure_without_logging_patient_data(
    monkeypatch,
    caplog,
):
    user = User.objects.create_user(
        username="patient@example.test",
        email="patient@example.test",
        password="Current-passphrase-2026!",
    )

    def _fail_send(**kwargs):
        raise RuntimeError("smtp unavailable")

    monkeypatch.setattr("core.api.v1.auth.send_mail", _fail_send)
    caplog.set_level(logging.ERROR, logger="core.api.v1.auth")

    missing = request_password_reset(
        None,
        PasswordResetRequest(email="missing@example.test"),
    )
    existing = request_password_reset(
        None,
        PasswordResetRequest(email=user.email),
    )

    assert missing == existing == {
        "detail": "If the account exists, the recovery request was accepted"
    }
    assert "Password reset email delivery failed: RuntimeError" in caplog.text
    assert user.email not in caplog.text
    assert "smtp unavailable" not in caplog.text


@pytest.mark.django_db
def test_reset_confirmation_changes_password_and_revokes_old_token():
    user = User.objects.create_user(
        username="patient@example.test",
        email="patient@example.test",
        password="Current-passphrase-2026!",
    )
    old_token = issue_native_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_token = default_token_generator.make_token(user)

    result = confirm_password_reset(
        None,
        PasswordResetConfirmRequest(
            uid=uid,
            token=reset_token,
            new_password="Replacement-passphrase-2026!",
        ),
    )

    user.refresh_from_db()
    assert result == {"detail": "Password reset completed"}
    assert user.check_password("Replacement-passphrase-2026!")
    with pytest.raises(NativeTokenError):
        verify_native_token(old_token)


@pytest.mark.django_db
def test_reset_confirmation_rejects_invalid_token():
    user = User.objects.create_user(
        username="patient",
        password="Current-passphrase-2026!",
    )
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    with pytest.raises(HttpError) as exc:
        confirm_password_reset(
            None,
            PasswordResetConfirmRequest(
                uid=uid,
                token="invalid",
                new_password="Replacement-passphrase-2026!",
            ),
        )

    assert exc.value.status_code == 400
