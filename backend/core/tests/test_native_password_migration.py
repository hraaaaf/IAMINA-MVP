"""Native password establishment and rotation safety tests."""

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser, User
from ninja.errors import HttpError

from core.api.v1.auth import SetPasswordRequest, set_native_password
from core.models import BasePatientProfile


def _request(user):
    return SimpleNamespace(user=user, session={})


def test_password_establishment_requires_authentication():
    with pytest.raises(HttpError) as exc:
        set_native_password(
            _request(AnonymousUser()),
            SetPasswordRequest(new_password="A-strong-passphrase-2026!"),
        )
    assert exc.value.status_code == 401


@pytest.mark.django_db
def test_firebase_only_user_can_establish_native_password(monkeypatch):
    user = User.objects.create_user(username="firebase-only", email="patient@example.test")
    BasePatientProfile.objects.create(patient=user, firebase_uid="firebase-uid")
    monkeypatch.setattr(
        "core.api.v1.auth.update_session_auth_hash",
        lambda request, value: None,
    )

    result = set_native_password(
        _request(user),
        SetPasswordRequest(new_password="A-strong-passphrase-2026!"),
    )

    user.refresh_from_db()
    assert result == {"detail": "Django password established"}
    assert user.check_password("A-strong-passphrase-2026!")
    assert user.base_profile.firebase_uid == "firebase-uid"


@pytest.mark.django_db
def test_native_password_rotation_requires_current_password(monkeypatch):
    user = User.objects.create_user(
        username="native",
        password="Current-passphrase-2026!",
    )
    monkeypatch.setattr(
        "core.api.v1.auth.update_session_auth_hash",
        lambda request, value: None,
    )

    with pytest.raises(HttpError) as missing:
        set_native_password(
            _request(user),
            SetPasswordRequest(new_password="Replacement-passphrase-2026!"),
        )
    assert missing.value.status_code == 401

    with pytest.raises(HttpError) as wrong:
        set_native_password(
            _request(user),
            SetPasswordRequest(
                current_password="wrong",
                new_password="Replacement-passphrase-2026!",
            ),
        )
    assert wrong.value.status_code == 401

    result = set_native_password(
        _request(user),
        SetPasswordRequest(
            current_password="Current-passphrase-2026!",
            new_password="Replacement-passphrase-2026!",
        ),
    )
    user.refresh_from_db()
    assert result == {"detail": "Django password established"}
    assert user.check_password("Replacement-passphrase-2026!")


@pytest.mark.django_db
def test_weak_native_password_fails_closed(monkeypatch):
    user = User.objects.create_user(username="firebase-only")
    monkeypatch.setattr(
        "core.api.v1.auth.update_session_auth_hash",
        lambda request, value: None,
    )

    with pytest.raises(HttpError) as exc:
        set_native_password(
            _request(user),
            SetPasswordRequest(new_password="123"),
        )
    assert exc.value.status_code == 400
    user.refresh_from_db()
    assert not user.has_usable_password()
