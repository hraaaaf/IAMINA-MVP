"""W01 G3: account erasure must never report success if Firebase cleanup failed.

Synthetic Django ORM tests only. No Firebase app, credentials, Redis or cloud.
The cross-service commit-after-Firebase failure window remains a separate gate.
"""
from types import SimpleNamespace

import firebase_admin.auth
import pytest
from django.contrib.auth.models import User
from ninja.errors import HttpError

from core.api.v1 import account
from core.models import BasePatientProfile
from core.models.erasure_record import ErasureRecord


@pytest.fixture
def isolated_erasure(monkeypatch):
    events = []
    monkeypatch.setattr(account, "run_account_delete_hooks", lambda *args: events.append("hooks"))
    monkeypatch.setattr(account, "record_audit_required", lambda *args, **kwargs: events.append("audit"))
    monkeypatch.setattr(account, "logout", lambda req: events.append("logout"))
    return events


def _request(user):
    return SimpleNamespace(user=user, session={})


def _linked_user(label):
    user = User.objects.create_user(
        username=f"g3-{label}", email=f"g3-{label}@example.invalid", password="SyntheticOnlyPass!1"
    )
    BasePatientProfile.objects.create(patient=user, firebase_uid=f"firebase-{label}")
    return user


@pytest.mark.django_db
def test_firebase_transport_failure_blocks_success_and_keeps_sql_user(monkeypatch, isolated_erasure):
    user = _linked_user("failed")
    def unavailable(uid):
        isolated_erasure.append("firebase")
        raise RuntimeError("synthetic upstream service unavailable")
    monkeypatch.setattr(account.firebase_admin.auth, "delete_user", unavailable)

    with pytest.raises(HttpError) as caught:
        account.delete_account(_request(user), account.DeleteConfirmSchema(confirm="DELETE MY ACCOUNT"))

    assert caught.value.status_code == 503
    assert "service unavailable" not in str(caught.value)
    assert User.objects.filter(pk=user.pk).exists()
    assert BasePatientProfile.objects.filter(patient_id=user.pk).exists()
    assert not ErasureRecord.objects.filter(patient_id_snapshot=user.pk).exists()
    assert isolated_erasure == ["hooks", "firebase"]


@pytest.mark.django_db
def test_firebase_identity_already_absent_is_idempotent(monkeypatch, isolated_erasure):
    user = _linked_user("missing")
    def already_gone(uid):
        isolated_erasure.append("firebase")
        raise firebase_admin.auth.UserNotFoundError("synthetic uid not found")
    monkeypatch.setattr(account.firebase_admin.auth, "delete_user", already_gone)

    result = account.delete_account(_request(user), account.DeleteConfirmSchema(confirm="DELETE MY ACCOUNT"))

    assert result["detail"] == "Account and all associated data deleted."
    assert not User.objects.filter(pk=user.pk).exists()
    receipt = ErasureRecord.objects.get(patient_id_snapshot=user.pk)
    assert receipt.completed_at is not None
    assert isolated_erasure == ["hooks", "firebase", "audit", "logout"]


@pytest.mark.django_db
def test_native_user_requires_no_firebase_admin_call(monkeypatch, isolated_erasure):
    user = User.objects.create_user(username="g3-native", password="SyntheticOnlyPass!1")
    def never_firebase(uid):
        pytest.fail("Native identity must not invoke Firebase")
    monkeypatch.setattr(account.firebase_admin.auth, "delete_user", never_firebase)

    result = account.delete_account(_request(user), account.DeleteConfirmSchema(confirm="DELETE MY ACCOUNT"))

    assert result["detail"] == "Account and all associated data deleted."
    assert not User.objects.filter(pk=user.pk).exists()
    receipt = ErasureRecord.objects.get(patient_id_snapshot=user.pk)
    assert receipt.completed_at is not None
    assert isolated_erasure == ["hooks", "audit", "logout"]


@pytest.mark.django_db
def test_cleanup_hook_failure_prevents_firebase_and_sql_deletion(monkeypatch, isolated_erasure):
    user = _linked_user("hookfailed")
    monkeypatch.setattr(
        account, "run_account_delete_hooks",
        lambda *args: (_ for _ in ()).throw(RuntimeError("synthetic hook failure")),
    )
    def never_firebase(uid):
        pytest.fail("Hook failure must stop before Firebase")
    monkeypatch.setattr(account.firebase_admin.auth, "delete_user", never_firebase)

    with pytest.raises(HttpError) as caught:
        account.delete_account(_request(user), account.DeleteConfirmSchema(confirm="DELETE MY ACCOUNT"))

    assert caught.value.status_code == 500
    assert User.objects.filter(pk=user.pk).exists()
    assert not ErasureRecord.objects.filter(patient_id_snapshot=user.pk).exists()
    assert isolated_erasure == []
