"""G7 candidate crash-window regression: strictly synthetic account erasure.

SystemExit models a Python-level unhandled abort at precise points, not
power loss, kernel termination, distributed transaction rollback or Firebase.
"""
import firebase_admin.auth
import pytest
from django.contrib.auth.models import User
from ninja.errors import HttpError

from core.api.v1 import account
from core.models import BasePatientProfile
from core.models.erasure_attempt import ErasureAttempt
from core.models.erasure_record import ErasureRecord


def synthetic_user(label):
    user = User.objects.create_user(
        username=f"w01-g7-crash-{label}",
        email=f"w01-g7-crash-{label}@example.invalid",
        password="OnlySyntheticPass!2026",
    )
    BasePatientProfile.objects.create(
        patient=user, firebase_uid=f"g7-synthetic-firebase-{label}"
    )
    return user


@pytest.mark.django_db
def test_abrupt_abort_during_hook_keeps_exclusive_in_progress_claim(monkeypatch):
    user = synthetic_user("hook")
    patient_id = user.pk
    events = []

    def abort_hook(pid, uid):
        events.append("hook")
        raise SystemExit("synthetic abrupt process abort")

    def unexpected_firebase(uid):
        pytest.fail("Abort during hook must precede Firebase")

    monkeypatch.setattr(account, "run_account_delete_hooks", abort_hook)
    monkeypatch.setattr(firebase_admin.auth, "delete_user", unexpected_firebase)

    with pytest.raises(SystemExit, match="synthetic abrupt process abort"):
        account._erase_account_data(user)

    intent = ErasureAttempt.objects.get(patient_id_snapshot=patient_id)
    assert intent.state == ErasureAttempt.State.IN_PROGRESS
    assert intent.firebase_uid_snapshot == "g7-synthetic-firebase-hook"
    assert User.objects.filter(pk=patient_id).exists()
    assert not ErasureRecord.objects.filter(patient_id_snapshot=patient_id).exists()

    # Another request must not run the hook again even if the process stopped
    # before it could convert IN_PROGRESS into REVIEW_REQUIRED.
    with pytest.raises(HttpError) as denied:
        account._erase_account_data(User.objects.get(pk=patient_id))
    assert denied.value.status_code == 503
    assert events == ["hook"]
    assert ErasureAttempt.objects.get(
        patient_id_snapshot=patient_id
    ).state == ErasureAttempt.State.IN_PROGRESS


@pytest.mark.django_db
def test_abrupt_abort_after_external_firebase_call_never_automatically_replays(
    monkeypatch,
):
    user = synthetic_user("firebase")
    patient_id = user.pk
    events = []
    monkeypatch.setattr(
        account, "run_account_delete_hooks",
        lambda pid, uid: events.append("hook"),
    )

    def abort_firebase(uid):
        events.append("firebase")
        raise SystemExit("synthetic crash after Firebase side effect")

    monkeypatch.setattr(firebase_admin.auth, "delete_user", abort_firebase)
    with pytest.raises(SystemExit, match="synthetic crash"):
        account._erase_account_data(user)

    assert events == ["hook", "firebase"]
    intent = ErasureAttempt.objects.get(patient_id_snapshot=patient_id)
    assert intent.state == ErasureAttempt.State.IN_PROGRESS
    assert User.objects.filter(pk=patient_id).exists()
    assert not ErasureRecord.objects.filter(patient_id_snapshot=patient_id).exists()

    # Explicit state diagnosis is needed; no automatic external replay.
    with pytest.raises(HttpError) as denied:
        account._erase_account_data(User.objects.get(pk=patient_id))
    assert denied.value.status_code == 503
    assert events == ["hook", "firebase"]
    assert ErasureAttempt.objects.get(
        patient_id_snapshot=patient_id
    ).state == ErasureAttempt.State.IN_PROGRESS
