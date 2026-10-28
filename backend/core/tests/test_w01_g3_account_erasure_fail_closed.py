"""W01 G3: account erasure must never report success if Firebase cleanup failed.

Synthetic Django ORM tests only. No Firebase app, credentials, Redis or cloud.
The cross-service commit-after-Firebase failure window remains a separate gate.
"""
from types import SimpleNamespace

import firebase_admin.auth
import pytest
from django.contrib.auth.models import User
from django.test import Client
from ninja.errors import HttpError

from core.api.v1 import account
from core.models import BasePatientProfile
from core.models.erasure_attempt import ErasureAttempt
from core.models.erasure_record import ErasureRecord
from core.native_auth import issue_native_token


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
    intent = ErasureAttempt.objects.get(patient_id_snapshot=user.pk)
    assert intent.state == ErasureAttempt.State.REVIEW_REQUIRED
    assert intent.firebase_uid_snapshot == "firebase-failed"
    assert isolated_erasure == ["hooks", "firebase"]


@pytest.mark.django_db
def test_firebase_identity_already_absent_is_idempotent(monkeypatch, isolated_erasure):
    user = _linked_user("missing")
    def already_gone(uid):
        isolated_erasure.append("firebase")
        raise firebase_admin.auth.UserNotFoundError("synthetic uid not found")
    monkeypatch.setattr(account.firebase_admin.auth, "delete_user", already_gone)

    patient_id = user.pk
    result = account.delete_account(_request(user), account.DeleteConfirmSchema(confirm="DELETE MY ACCOUNT"))

    assert result["detail"] == "Account and all associated data deleted."
    assert not User.objects.filter(pk=patient_id).exists()
    receipt = ErasureRecord.objects.get(patient_id_snapshot=patient_id)
    assert receipt.completed_at is not None
    intent = ErasureAttempt.objects.get(patient_id_snapshot=patient_id)
    assert intent.state == ErasureAttempt.State.COMPLETED
    assert intent.firebase_uid_snapshot == ""
    assert intent.completed_at is not None
    assert isolated_erasure == ["hooks", "firebase", "audit", "logout"]


@pytest.mark.django_db
def test_native_user_requires_no_firebase_admin_call(monkeypatch, isolated_erasure):
    user = User.objects.create_user(username="g3-native", password="SyntheticOnlyPass!1")
    def never_firebase(uid):
        pytest.fail("Native identity must not invoke Firebase")
    monkeypatch.setattr(account.firebase_admin.auth, "delete_user", never_firebase)

    patient_id = user.pk
    result = account.delete_account(_request(user), account.DeleteConfirmSchema(confirm="DELETE MY ACCOUNT"))

    assert result["detail"] == "Account and all associated data deleted."
    assert not User.objects.filter(pk=patient_id).exists()
    receipt = ErasureRecord.objects.get(patient_id_snapshot=patient_id)
    assert receipt.completed_at is not None
    intent = ErasureAttempt.objects.get(patient_id_snapshot=patient_id)
    assert intent.state == ErasureAttempt.State.COMPLETED
    assert intent.firebase_uid_snapshot == ""
    assert intent.completed_at is not None
    assert isolated_erasure == ["hooks", "audit", "logout"]


@pytest.mark.django_db
def test_native_app_erasure_rejects_old_bearer_and_cookie_without_affecting_b(
    isolated_erasure,
):
    """Ephemeral Django test DB: stale A credentials fail closed after app erase.

    This is NOT replay of an actual hosted Preview token or proof that all
    django_session rows have been physically removed.
    """
    a = User.objects.create_user(
        username="w01-revocation-a@example.invalid",
        email="w01-revocation-a@example.invalid",
        password="SyntheticOnlyPass!2026",
    )
    b = User.objects.create_user(
        username="w01-revocation-b@example.invalid",
        email="w01-revocation-b@example.invalid",
        password="SyntheticOnlyPass!2026",
    )
    token_a = issue_native_token(a)
    token_b = issue_native_token(b)
    a_id = a.pk
    b_id = b.pk

    cookie_a = Client()
    cookie_a.force_login(a)
    cookie_b = Client()
    cookie_b.force_login(b)
    direct = Client()

    def bearer(token):
        return direct.get(
            "/api/v1/auth/me",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

    assert bearer(token_a).status_code == 200
    assert bearer(token_b).status_code == 200
    assert cookie_a.get("/api/v1/auth/me").status_code == 200
    assert cookie_b.get("/api/v1/auth/me").status_code == 200

    result = account.delete_account(
        _request(a), account.DeleteConfirmSchema(confirm="DELETE MY ACCOUNT")
    )
    assert result["detail"] == "Account and all associated data deleted."
    assert not User.objects.filter(pk=a_id).exists()
    assert not BasePatientProfile.objects.filter(patient_id=a_id).exists()
    assert User.objects.filter(pk=b_id).exists()

    # Preserve the old cookie on purpose (the test fixture bypasses logout).
    # Authentication must still reject deleted A, not just a cleared browser.
    assert bearer(token_a).status_code == 401
    assert cookie_a.get("/api/v1/auth/me").status_code == 401
    assert bearer(token_b).status_code == 200
    assert cookie_b.get("/api/v1/auth/me").status_code == 200



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
    intent = ErasureAttempt.objects.get(patient_id_snapshot=user.pk)
    assert intent.state == ErasureAttempt.State.REVIEW_REQUIRED
    assert intent.firebase_uid_snapshot == "firebase-hookfailed"
    assert isolated_erasure == []


@pytest.mark.django_db
def test_sql_receipt_failure_keeps_durable_intent_and_retry_recovers(
    monkeypatch, isolated_erasure
):
    """Crash after Firebase, before SQL commit: no success, recoverable intent."""
    user = _linked_user("sqlrollback")
    patient_id = user.pk
    remote_calls = []
    monkeypatch.setattr(
        account.firebase_admin.auth, "delete_user",
        lambda uid: remote_calls.append(uid),
    )
    create_receipt = ErasureRecord.objects.create
    def fail_receipt(**kwargs):
        raise RuntimeError("synthetic SQL receipt failure")
    monkeypatch.setattr(ErasureRecord.objects, "create", fail_receipt)

    with pytest.raises(HttpError) as failure:
        account.delete_account(
            _request(user),
            account.DeleteConfirmSchema(confirm="DELETE MY ACCOUNT"),
        )
    assert failure.value.status_code == 500
    assert remote_calls == ["firebase-sqlrollback"]
    assert User.objects.filter(pk=patient_id).exists()
    assert not ErasureRecord.objects.filter(patient_id_snapshot=patient_id).exists()
    intent = ErasureAttempt.objects.get(patient_id_snapshot=patient_id)
    assert intent.state == ErasureAttempt.State.REVIEW_REQUIRED
    assert intent.firebase_uid_snapshot == "firebase-sqlrollback"

    # An ordinary retry must NOT execute hooks or Firebase twice.
    with pytest.raises(HttpError) as denied:
        account.delete_account(
            _request(User.objects.get(pk=patient_id)),
            account.DeleteConfirmSchema(confirm="DELETE MY ACCOUNT"),
        )
    assert denied.value.status_code == 503
    assert remote_calls == ["firebase-sqlrollback"]

    # Synthetic-only test simulates explicit off-line operator adjudication.
    # There is deliberately no automatic recovery or hosted unlock endpoint.
    ErasureAttempt.objects.filter(
        patient_id_snapshot=patient_id,
        state=ErasureAttempt.State.REVIEW_REQUIRED,
    ).update(state=ErasureAttempt.State.PENDING)
    monkeypatch.setattr(ErasureRecord.objects, "create", create_receipt)
    def already_removed(uid):
        raise firebase_admin.auth.UserNotFoundError("synthetic already absent")
    monkeypatch.setattr(account.firebase_admin.auth, "delete_user", already_removed)
    recovered_user = User.objects.get(pk=patient_id)
    account._erase_account_data(recovered_user)
    assert not User.objects.filter(pk=patient_id).exists()
    receipt = ErasureRecord.objects.get(patient_id_snapshot=patient_id)
    assert receipt.completed_at is not None
    intent.refresh_from_db()
    assert intent.state == ErasureAttempt.State.COMPLETED
    assert intent.firebase_uid_snapshot == ""
    assert intent.completed_at is not None


@pytest.mark.django_db
def test_sql_audit_failure_after_firebase_keeps_pending_intent(monkeypatch, isolated_erasure):
    user = _linked_user("auditrollback")
    patient_id = user.pk
    calls = []
    monkeypatch.setattr(
        account.firebase_admin.auth, "delete_user",
        lambda uid: calls.append(uid),
    )
    def fail_audit(*args, **kwargs):
        raise RuntimeError("synthetic audit unavailable")
    monkeypatch.setattr(account, "record_audit_required", fail_audit)

    with pytest.raises(HttpError) as failure:
        account.delete_account(
            _request(user),
            account.DeleteConfirmSchema(confirm="DELETE MY ACCOUNT"),
        )
    assert failure.value.status_code == 500
    assert calls == ["firebase-auditrollback"]
    assert User.objects.filter(pk=patient_id).exists()
    assert not ErasureRecord.objects.filter(patient_id_snapshot=patient_id).exists()
    assert ErasureAttempt.objects.get(patient_id_snapshot=patient_id).state == (
        ErasureAttempt.State.REVIEW_REQUIRED
    )


@pytest.mark.django_db
def test_mismatched_pending_intent_blocks_before_any_cleanup_hook(
    monkeypatch, isolated_erasure
):
    user = _linked_user("mismatch")
    patient_id = user.pk
    ErasureAttempt.objects.create(
        patient_id_snapshot=patient_id,
        firebase_uid_snapshot="another-synthetic-identity",
    )
    monkeypatch.setattr(
        account.firebase_admin.auth, "delete_user",
        lambda uid: pytest.fail("Mismatched identity reached Firebase"),
    )

    with pytest.raises(HttpError) as denied:
        account.delete_account(
            _request(user),
            account.DeleteConfirmSchema(confirm="DELETE MY ACCOUNT"),
        )

    assert denied.value.status_code == 503
    assert User.objects.filter(pk=patient_id).exists()
    assert not ErasureRecord.objects.filter(patient_id_snapshot=patient_id).exists()
    assert isolated_erasure == []


@pytest.mark.django_db
def test_completed_intent_blocks_hook_reexecution(
    monkeypatch, isolated_erasure
):
    user = _linked_user("completed")
    patient_id = user.pk
    ErasureAttempt.objects.create(
        patient_id_snapshot=patient_id,
        firebase_uid_snapshot="",
        state=ErasureAttempt.State.COMPLETED,
    )
    monkeypatch.setattr(
        account.firebase_admin.auth, "delete_user",
        lambda uid: pytest.fail("Completed attempt reached Firebase"),
    )

    with pytest.raises(HttpError) as denied:
        account.delete_account(
            _request(user),
            account.DeleteConfirmSchema(confirm="DELETE MY ACCOUNT"),
        )

    assert denied.value.status_code == 503
    assert User.objects.filter(pk=patient_id).exists()
    assert not ErasureRecord.objects.filter(patient_id_snapshot=patient_id).exists()
    assert isolated_erasure == []


@pytest.mark.django_db
def test_in_progress_intent_blocks_duplicate_before_hooks_and_firebase(
    monkeypatch, isolated_erasure
):
    user = _linked_user("inflight")
    patient_id = user.pk
    ErasureAttempt.objects.create(
        patient_id_snapshot=patient_id,
        firebase_uid_snapshot="firebase-inflight",
        state=ErasureAttempt.State.IN_PROGRESS,
    )
    monkeypatch.setattr(
        account.firebase_admin.auth, "delete_user",
        lambda uid: pytest.fail("In-progress claim reached Firebase"),
    )
    with pytest.raises(HttpError) as denied:
        account.delete_account(
            _request(user),
            account.DeleteConfirmSchema(confirm="DELETE MY ACCOUNT"),
        )
    assert denied.value.status_code == 503
    assert isolated_erasure == []
    assert User.objects.filter(pk=patient_id).exists()


@pytest.mark.django_db
def test_reentrant_second_delete_is_rejected_before_external_effects(
    monkeypatch, isolated_erasure
):
    """Deterministic interleaving, not a two-connection PostgreSQL stress test."""
    user = _linked_user("reentrant")
    patient_id = user.pk
    external_calls = []
    attempted_second = []
    def hook_with_second_delete(pk, uid):
        isolated_erasure.append("hook")
        with pytest.raises(HttpError) as denied:
            account._erase_account_data(User.objects.get(pk=pk))
        attempted_second.append(denied.value.status_code)
    monkeypatch.setattr(account, "run_account_delete_hooks", hook_with_second_delete)
    monkeypatch.setattr(
        account.firebase_admin.auth, "delete_user",
        lambda uid: external_calls.append(uid),
    )
    result = account.delete_account(
        _request(user),
        account.DeleteConfirmSchema(confirm="DELETE MY ACCOUNT"),
    )
    assert result["detail"] == "Account and all associated data deleted."
    assert attempted_second == [503]
    assert external_calls == ["firebase-reentrant"]
    assert isolated_erasure == ["hook", "audit", "logout"]
    assert not User.objects.filter(pk=patient_id).exists()
    assert ErasureAttempt.objects.get(
        patient_id_snapshot=patient_id
    ).state == ErasureAttempt.State.COMPLETED
