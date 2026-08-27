from types import SimpleNamespace

import pytest

from core.auth_migration import FirebaseMigrationError, verify_firebase_token
from core.firebase_migration_policy import firebase_migration_enabled
from diabetes.api.v1.security import HybridBearerAuth


def test_firebase_migration_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_FIREBASE_MIGRATION", raising=False)
    assert firebase_migration_enabled() is False


def test_firebase_migration_requires_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("ENABLE_FIREBASE_MIGRATION", "true")
    assert firebase_migration_enabled() is True


def test_disabled_migration_rejects_token_before_provider_call(monkeypatch):
    monkeypatch.delenv("ENABLE_FIREBASE_MIGRATION", raising=False)

    with pytest.raises(FirebaseMigrationError, match="firebase_migration_disabled"):
        verify_firebase_token("legacy-token")


def test_generic_bearer_does_not_touch_firebase_when_disabled(monkeypatch):
    monkeypatch.delenv("ENABLE_FIREBASE_MIGRATION", raising=False)
    monkeypatch.setattr(
        "diabetes.api.v1.security.verify_firebase_token",
        lambda _token: pytest.fail("Firebase verifier must not run while disabled"),
    )

    request = SimpleNamespace(user=None)
    result = HybridBearerAuth().authenticate(request, "legacy-firebase-token")

    assert result is None
    assert request.user is None
