"""Sovereign Django authentication lifecycle regression tests."""

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser, User
from ninja.errors import HttpError

from core.api.v1.auth import (
    NativeLoginRequest,
    NativeRegisterRequest,
    current_identity,
    login_native,
    logout_native,
    register_native,
)
from core.models import BasePatientProfile


class SessionRequest(SimpleNamespace):
    session = {}


def _request(user=None):
    return SessionRequest(user=user or AnonymousUser())


@pytest.mark.django_db
def test_native_registration_creates_only_identity_and_empty_base_profile(monkeypatch):
    request = _request()
    monkeypatch.setattr("core.api.v1.auth.login", lambda req, user, backend: setattr(req, "user", user))
    monkeypatch.setattr("core.api.v1.auth.track", lambda *args, **kwargs: None)

    result = register_native(
        request,
        NativeRegisterRequest(
            email=" Patient@Example.test ",
            password="A-strong-passphrase-2026!",
            first_name=" Patient ",
        ),
    )

    user = User.objects.get(pk=result["user"]["id"])
    profile = BasePatientProfile.objects.get(patient=user)
    assert user.email == "patient@example.test"
    assert user.username == "patient@example.test"
    assert profile.firebase_uid is None
    assert profile.date_of_birth is None
    assert profile.gender is None
    assert request.user == user


@pytest.mark.django_db
def test_native_registration_rejects_case_insensitive_duplicate(monkeypatch):
    User.objects.create_user(
        username="existing",
        email="existing@example.test",
        password="A-strong-passphrase-2026!",
    )
    monkeypatch.setattr("core.api.v1.auth.track", lambda *args, **kwargs: None)

    with pytest.raises(HttpError) as exc:
        register_native(
            _request(),
            NativeRegisterRequest(
                email="EXISTING@example.test",
                password="Another-strong-passphrase-2026!",
            ),
        )
    assert exc.value.status_code == 409


@pytest.mark.django_db
def test_native_login_uses_email_but_authenticates_canonical_username(monkeypatch):
    user = User.objects.create_user(
        username="stable-internal-name",
        email="login@example.test",
        password="A-strong-passphrase-2026!",
    )
    request = _request()
    monkeypatch.setattr("core.api.v1.auth.login", lambda req, value, backend: setattr(req, "user", value))
    monkeypatch.setattr("core.api.v1.auth.track", lambda *args, **kwargs: None)

    result = login_native(
        request,
        NativeLoginRequest(email="LOGIN@example.test", password="A-strong-passphrase-2026!"),
    )
    assert result["user"]["id"] == user.id
    assert request.user == user


@pytest.mark.django_db
def test_native_login_fails_closed_on_ambiguous_email():
    User.objects.create_user(username="one", email="duplicate@example.test", password="x")
    User.objects.create_user(username="two", email="DUPLICATE@example.test", password="x")

    with pytest.raises(HttpError) as exc:
        login_native(
            _request(),
            NativeLoginRequest(email="duplicate@example.test", password="x"),
        )
    assert exc.value.status_code == 401


def test_current_identity_requires_authentication():
    with pytest.raises(HttpError) as exc:
        current_identity(_request())
    assert exc.value.status_code == 401


@pytest.mark.django_db
def test_logout_clears_session_through_django(monkeypatch):
    request = _request(User.objects.create_user(username="logout-user"))
    called = []
    monkeypatch.setattr("core.api.v1.auth.logout", lambda req: called.append(req))
    assert logout_native(request) == {"detail": "Signed out"}
    assert called == [request]
