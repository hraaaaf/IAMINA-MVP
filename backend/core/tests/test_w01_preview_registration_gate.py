"""W01: deny account registration server-side in synthetic Preview."""

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User
from ninja.errors import HttpError

from core.api.v1.auth import (
    NativeRegisterRequest,
    _native_registration_allowed_in_environment,
    register_native,
)


@pytest.mark.django_db
def test_w01_preview_registration_is_forbidden_before_any_identity_write(monkeypatch):
    monkeypatch.setenv("VERCEL_ENV", "preview")
    monkeypatch.delenv("IAMINA_PREVIEW_ALLOW_REGISTRATION", raising=False)

    with pytest.raises(HttpError) as exc:
        register_native(
            SimpleNamespace(),
            NativeRegisterRequest(
                email="w01-new@example.invalid",
                password="Synthetic-Strong-Passphrase-2026!",
            ),
        )
    assert exc.value.status_code == 403
    assert User.objects.filter(email="w01-new@example.invalid").count() == 0


@pytest.mark.parametrize("env_key", ["VERCEL_ENV", "IAMINA_ENV"])
def test_preview_is_disabled_via_either_hosting_environment(monkeypatch, env_key):
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.delenv("IAMINA_ENV", raising=False)
    monkeypatch.delenv("IAMINA_PREVIEW_ALLOW_REGISTRATION", raising=False)
    monkeypatch.setenv(env_key, "preview")
    assert _native_registration_allowed_in_environment() is False


def test_non_preview_registration_remains_unchanged(monkeypatch):
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv("IAMINA_ENV", "production")
    monkeypatch.delenv("IAMINA_PREVIEW_ALLOW_REGISTRATION", raising=False)
    assert _native_registration_allowed_in_environment() is True


def test_explicit_preview_opt_in_is_possible_for_separate_positive_qa(monkeypatch):
    monkeypatch.setenv("VERCEL_ENV", "preview")
    monkeypatch.setenv("IAMINA_PREVIEW_ALLOW_REGISTRATION", "true")
    assert _native_registration_allowed_in_environment() is True
