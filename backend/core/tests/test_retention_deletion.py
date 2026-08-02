import json
import os
from datetime import datetime, timedelta, timezone
from io import StringIO

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone as django_timezone

from core.models import AuditLog
from core.retention_policy import (
    NOT_PERSISTED,
    retention_schedule_payload,
    validated_retention_schedule,
)


def test_retention_schedule_is_current_unique_and_machine_readable():
    rules = validated_retention_schedule(today=django_timezone.localdate())
    assert len({rule.dataset for rule in rules}) == len(rules)
    raw_media = next(rule for rule in rules if rule.dataset == "raw_ai_media_in_application")
    assert raw_media.trigger == NOT_PERSISTED
    assert raw_media.retention_days == 0
    payload = retention_schedule_payload(today=django_timezone.localdate())
    assert payload["schema_version"] == "1.0"
    assert len(payload["rules"]) == len(rules)


@pytest.mark.django_db
def test_deletion_is_dry_run_by_default():
    user = User.objects.create_user(username="dry-run", password="not-exported")
    output = StringIO()

    call_command(
        "delete_patient_data",
        user_id=user.id,
        requested_at=django_timezone.localdate() - timedelta(days=31),
        approval_reference="REQ-DRY-RUN",
        export_sha256="a" * 64,
        legal_hold_status="CLEARED",
        stdout=output,
    )

    assert User.objects.filter(pk=user.id).exists()
    assert json.loads(output.getvalue())["action"] == "DRY_RUN"


@pytest.mark.django_db
def test_deletion_blocks_active_legal_hold():
    user = User.objects.create_user(username="held", password="not-exported")

    with pytest.raises(CommandError, match="legal-hold"):
        call_command(
            "delete_patient_data",
            user_id=user.id,
            requested_at=django_timezone.localdate() - timedelta(days=31),
            approval_reference="REQ-HELD",
            export_sha256="b" * 64,
            legal_hold_status="ACTIVE",
        )

    assert User.objects.filter(pk=user.id).exists()


@pytest.mark.django_db
def test_deletion_blocks_during_grace_period():
    user = User.objects.create_user(username="grace", password="not-exported")

    with pytest.raises(CommandError, match="grace period"):
        call_command(
            "delete_patient_data",
            user_id=user.id,
            requested_at=django_timezone.localdate() - timedelta(days=10),
            approval_reference="REQ-GRACE",
            export_sha256="c" * 64,
            legal_hold_status="CLEARED",
        )


@pytest.mark.django_db
def test_execute_requires_exact_confirmation_and_retains_anonymous_audit():
    user = User.objects.create_user(username="delete-me", password="not-exported")
    AuditLog.objects.create(
        actor=user,
        action="view",
        resource_type="Synthetic",
        resource_id="owned-record",
    )
    command_options = {
        "user_id": user.id,
        "requested_at": django_timezone.localdate() - timedelta(days=31),
        "approval_reference": "REQ-APPROVED",
        "export_sha256": "d" * 64,
        "legal_hold_status": "CLEARED",
        "execute": True,
    }

    with pytest.raises(CommandError, match="requires --confirm"):
        call_command("delete_patient_data", confirm="wrong", **command_options)

    output = StringIO()
    call_command(
        "delete_patient_data",
        confirm=f"DELETE-PATIENT-{user.id}",
        stdout=output,
        **command_options,
    )

    assert not User.objects.filter(pk=user.id).exists()
    deletion_log = AuditLog.objects.get(
        actor=None,
        action="delete",
        resource_type="PatientAccount",
        resource_id=str(user.id),
    )
    assert deletion_log.metadata["approval_reference"] == "REQ-APPROVED"
    assert AuditLog.objects.filter(resource_id="owned-record", actor=None).exists()
    assert json.loads(output.getvalue())["action"] == "EXECUTE"


def test_export_staging_purge_is_dry_run_then_execute(tmp_path):
    old_file = tmp_path / "iamina-patient-1.json"
    new_file = tmp_path / "iamina-patient-2.json"
    ignored = tmp_path / "other.json"
    old_file.write_text("old")
    new_file.write_text("new")
    ignored.write_text("ignored")
    old_timestamp = (datetime.now(timezone.utc) - timedelta(days=8)).timestamp()
    os.utime(old_file, (old_timestamp, old_timestamp))

    dry_output = StringIO()
    call_command(
        "purge_export_staging",
        directory=str(tmp_path),
        stdout=dry_output,
    )
    assert json.loads(dry_output.getvalue())["candidate_count"] == 1
    assert old_file.exists()

    execute_output = StringIO()
    call_command(
        "purge_export_staging",
        directory=str(tmp_path),
        execute=True,
        stdout=execute_output,
    )
    assert not old_file.exists()
    assert new_file.exists()
    assert ignored.exists()
