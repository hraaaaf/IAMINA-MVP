"""W01 G3: redacted, read-only erasure backlog inspection."""
import json
from io import StringIO

import pytest
from django.core.management import call_command
from django.db import connection

from core.models.erasure_attempt import ErasureAttempt


@pytest.mark.django_db
def test_backlog_report_counts_states_without_exposing_identities(monkeypatch):
    secret = "private-synthetic-firebase-uid-6f52"
    entries = [
        (100021, secret, ErasureAttempt.State.PENDING),
        (100022, "different-synthetic-uid", ErasureAttempt.State.IN_PROGRESS),
        (100023, secret, ErasureAttempt.State.REVIEW_REQUIRED),
        (100024, "", ErasureAttempt.State.COMPLETED),
    ]
    for patient_id, uid, state in entries:
        ErasureAttempt.objects.create(
            patient_id_snapshot=patient_id,
            firebase_uid_snapshot=uid,
            state=state,
        )

    # Any mutation path must be unreachable from this read-only command.
    def deny_mutation(*args, **kwargs):
        pytest.fail("Backlog inspection attempted a database mutation")

    monkeypatch.setattr(ErasureAttempt.objects, "update", deny_mutation)
    monkeypatch.setattr(ErasureAttempt.objects, "delete", deny_mutation)
    out = StringIO()
    with connection.execute_wrapper(
        lambda execute, sql, params, many, context: (
            execute(sql, params, many, context)
            if sql.lstrip().upper().startswith("SELECT")
            else deny_mutation(sql)
        )
    ):
        call_command("erasure_backlog_report", stdout=out)
    payload = json.loads(out.getvalue())
    assert payload == {
        "action": "READ_ONLY_ERASURE_BACKLOG",
        "pending": 1,
        "in_progress": 1,
        "review_required": 1,
        "completed": 1,
        "unresolved_total": 3,
    }
    assert secret not in out.getvalue()
    assert "100021" not in out.getvalue()
    assert "100023" not in out.getvalue()
    assert ErasureAttempt.objects.count() == 4


@pytest.mark.django_db
def test_backlog_report_empty_database():
    out = StringIO()
    call_command("erasure_backlog_report", stdout=out)
    payload = json.loads(out.getvalue())
    assert payload["unresolved_total"] == 0
    assert payload["review_required"] == 0
    assert payload["in_progress"] == 0
    assert payload["pending"] == 0
