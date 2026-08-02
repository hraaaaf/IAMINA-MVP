import json
import stat
from datetime import datetime, timezone

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command

from core.data_portability import build_patient_export
from core.models import AuditLog


@pytest.mark.django_db
def test_export_contains_only_subject_owned_records_and_no_password_hash():
    subject = User.objects.create_user(
        username="subject",
        email="subject@example.test",
        password="not-exported-password",
    )
    other = User.objects.create_user(
        username="other",
        email="other@example.test",
        password="other-password",
    )
    own_log = AuditLog.objects.create(
        actor=subject,
        action="view",
        resource_type="Synthetic",
        resource_id="subject-record",
    )
    AuditLog.objects.create(
        actor=other,
        action="view",
        resource_type="Synthetic",
        resource_id="other-record",
    )

    bundle = build_patient_export(
        subject,
        generated_at=datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc),
    )

    assert "password" not in bundle["data"]["account"]
    logs = bundle["data"]["records"]["core.auditlog"]
    assert [record["id"] for record in logs] == [own_log.id]
    assert logs[0]["resource_id"] == "subject-record"
    assert "other-record" not in json.dumps(bundle)


@pytest.mark.django_db
def test_export_fingerprint_is_stable_across_generation_times():
    user = User.objects.create_user(username="stable", password="not-exported")
    first = build_patient_export(
        user,
        generated_at=datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc),
    )
    second = build_patient_export(
        user,
        generated_at=datetime(2026, 8, 2, 11, 0, tzinfo=timezone.utc),
    )

    assert first["generated_at"] != second["generated_at"]
    assert first["sha256"] == second["sha256"]


@pytest.mark.django_db
def test_management_command_writes_mode_0600_and_audits(tmp_path):
    user = User.objects.create_user(username="portable", password="not-exported")
    output = tmp_path / "patient-export.json"

    call_command(
        "export_patient_data",
        user_id=user.id,
        output=str(output),
    )

    payload = json.loads(output.read_text())
    assert payload["subject"] == {"user_id": user.id}
    assert len(payload["sha256"]) == 64
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    audit = AuditLog.objects.get(
        actor=user,
        action="export",
        resource_type="PatientDataExport",
    )
    assert audit.metadata["sha256"] == payload["sha256"]


@pytest.mark.django_db
def test_management_command_refuses_overwrite_without_explicit_flag(tmp_path):
    user = User.objects.create_user(username="overwrite", password="not-exported")
    output = tmp_path / "patient-export.json"
    output.write_text("existing")

    with pytest.raises(Exception, match="Output already exists"):
        call_command(
            "export_patient_data",
            user_id=user.id,
            output=str(output),
        )

    assert output.read_text() == "existing"
