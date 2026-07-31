"""Native password recovery remains enumeration-safe and revokes old tokens."""

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
from core.native_auth import issue_native_token, resolve_native_token


@pytest.mark.django_db
def test_reset_request_does_not_disclose_account_existence(monkeypatch):
    sent = []
    monkeypatch.setattr(
        "core.api.v1.auth.send_mail",
        lambda **kwargs: sent.append(kwargs),
    )

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

    assert missing == existing
    assert len(sent) == 1


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
    assert resolve_native_token(old_token) is None


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
