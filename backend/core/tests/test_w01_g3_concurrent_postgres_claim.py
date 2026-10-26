"""W01 G3: PostgreSQL two-connection erasure claim race, synthetic only.

The first DELETE pauses *after* committing its exclusive SQL claim. A second
request on a separate Django connection must fail before any external effect.
No credentials, live Firebase request, or production database are used.
"""
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from django.contrib.auth.models import User
from django.db import connections
from ninja.errors import HttpError

from core.api.v1 import account
from core.models import BasePatientProfile
from core.models.erasure_attempt import ErasureAttempt
from core.models.erasure_record import ErasureRecord


@pytest.mark.django_db(transaction=True)
def test_two_postgres_connections_allow_only_one_erasure_claim(monkeypatch):
    if connections["default"].vendor != "postgresql":
        pytest.skip("Two-connection locking proof requires PostgreSQL")

    user = User.objects.create_user(
        username="w01-g3-pg-race",
        email="w01-g3-pg-race@example.invalid",
        password="OnlySyntheticPass!2026",
    )
    patient_id = user.pk
    BasePatientProfile.objects.create(
        patient=user, firebase_uid="firebase-synthetic-pg-race"
    )
    hook_entered = Event()
    release_first_hook = Event()
    hook_calls = []
    firebase_calls = []
    audit_calls = []

    def guarded_hook(pid, uid):
        hook_calls.append((pid, uid))
        hook_entered.set()
        if not release_first_hook.wait(timeout=20):
            raise RuntimeError("synthetic first DELETE was not released")

    monkeypatch.setattr(account, "run_account_delete_hooks", guarded_hook)
    monkeypatch.setattr(
        account.firebase_admin.auth,
        "delete_user",
        lambda uid: firebase_calls.append(uid),
    )
    monkeypatch.setattr(
        account,
        "record_audit_required",
        lambda *args, **kwargs: audit_calls.append("committed"),
    )

    def first_request():
        try:
            account._erase_account_data(User.objects.get(pk=patient_id))
        finally:
            # Django DB connections are thread-local: do not leak one to CI.
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as executor:
        first = executor.submit(first_request)
        try:
            assert hook_entered.wait(timeout=15), "First DELETE never held its claim"
            assert ErasureAttempt.objects.get(
                patient_id_snapshot=patient_id
            ).state == ErasureAttempt.State.IN_PROGRESS
            with pytest.raises(HttpError) as denied:
                account._erase_account_data(User.objects.get(pk=patient_id))
            assert denied.value.status_code == 503
            assert hook_calls == [(patient_id, "firebase-synthetic-pg-race")]
            assert firebase_calls == []
        finally:
            release_first_hook.set()
        first.result(timeout=25)

    assert not User.objects.filter(pk=patient_id).exists()
    assert len(hook_calls) == 1
    assert firebase_calls == ["firebase-synthetic-pg-race"]
    assert audit_calls == ["committed"]
    assert ErasureRecord.objects.filter(patient_id_snapshot=patient_id).count() == 1
    assert ErasureAttempt.objects.get(
        patient_id_snapshot=patient_id
    ).state == ErasureAttempt.State.COMPLETED


@pytest.mark.django_db
def test_review_required_rejects_repeat_without_hooks_or_firebase(monkeypatch):
    user = User.objects.create_user(
        username="w01-g3-review", password="OnlySyntheticPass!2026"
    )
    patient_id = user.pk
    BasePatientProfile.objects.create(
        patient=user, firebase_uid="firebase-synthetic-review"
    )
    ErasureAttempt.objects.create(
        patient_id_snapshot=patient_id,
        firebase_uid_snapshot="firebase-synthetic-review",
        state=ErasureAttempt.State.REVIEW_REQUIRED,
    )

    def unexpected_effect(*args, **kwargs):
        pytest.fail("REVIEW_REQUIRED must not run hooks or Firebase")

    monkeypatch.setattr(account, "run_account_delete_hooks", unexpected_effect)
    monkeypatch.setattr(
        account.firebase_admin.auth, "delete_user", unexpected_effect
    )

    with pytest.raises(HttpError) as denied:
        account._erase_account_data(user)
    assert denied.value.status_code == 503
    assert User.objects.filter(pk=patient_id).exists()
    assert ErasureAttempt.objects.get(
        patient_id_snapshot=patient_id
    ).state == ErasureAttempt.State.REVIEW_REQUIRED
