import json
import stat
from datetime import datetime, timezone
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from core.pilot_lifecycle import (
    NOT_APPLICABLE,
    PASS,
    build_cohort_checklist,
    checklist_registry_payload,
    validate_completed_checklist,
    validated_checklist_registry,
)


def _completed_payload():
    payload = build_cohort_checklist(
        "PILOT_001",
        generated_at=datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc),
    )
    for item in payload["items"]:
        item["status"] = PASS
        item["evidence_reference"] = f"EVIDENCE:{item['item_id']}"
        item["reviewed_by_role"] = item["owner_role"]
        item["reviewed_at"] = "2026-08-02T12:30:00+00:00"
    payload["status"] = PASS
    return payload


def test_registry_has_all_four_phases_and_blocking_items():
    items = validated_checklist_registry()
    phases = {item.phase for item in items}
    assert phases == {"onboarding", "monitoring", "escalation", "exit"}
    assert all(any(item.phase == phase and item.blocking for item in items) for phase in phases)
    payload = checklist_registry_payload()
    assert payload["schema_version"] == "1.0"
    assert len(payload["items"]) == len(items)


def test_cohort_identifier_must_be_opaque():
    with pytest.raises(ValueError, match="opaque uppercase identifier"):
        build_cohort_checklist("patient@example.test")


def test_completed_checklist_requires_all_blocking_evidence():
    payload = _completed_payload()
    validate_completed_checklist(payload)

    payload["items"][0]["status"] = "PENDING"
    payload["items"][0]["evidence_reference"] = None
    with pytest.raises(ValueError, match="remains pending"):
        validate_completed_checklist(payload)


def test_blocking_item_cannot_be_not_applicable():
    payload = _completed_payload()
    blocking = next(item for item in payload["items"] if item["blocking"])
    blocking["status"] = NOT_APPLICABLE
    blocking["evidence_reference"] = None
    blocking["not_applicable_rationale"] = "This condition was reviewed and judged outside scope."
    with pytest.raises(ValueError, match="cannot be not applicable"):
        validate_completed_checklist(payload)


def test_pass_requires_owner_role_and_opaque_evidence_reference():
    payload = _completed_payload()
    item = payload["items"][0]
    item["reviewed_by_role"] = "wrong_role"
    with pytest.raises(ValueError, match="owner role"):
        validate_completed_checklist(payload)

    item["reviewed_by_role"] = item["owner_role"]
    item["evidence_reference"] = "participant@example.test"
    with pytest.raises(ValueError, match="evidence reference"):
        validate_completed_checklist(payload)


def test_create_checklist_command_writes_mode_0600(tmp_path):
    output = tmp_path / "pilot-checklist.json"
    call_command(
        "create_pilot_checklist",
        cohort_id="PILOT_002",
        output=str(output),
    )

    payload = json.loads(output.read_text())
    assert payload["cohort_id"] == "PILOT_002"
    assert payload["status"] == "PENDING"
    assert stat.S_IMODE(output.stat().st_mode) == 0o600


def test_validate_checklist_command_fails_pending_and_passes_completed(tmp_path):
    path = tmp_path / "pilot-checklist.json"
    pending = build_cohort_checklist("PILOT_003")
    path.write_text(json.dumps(pending))

    with pytest.raises(CommandError, match="remains pending"):
        call_command("validate_pilot_checklist", file=str(path))

    completed = _completed_payload()
    completed["cohort_id"] = "PILOT_003"
    path.write_text(json.dumps(completed))
    output = StringIO()
    call_command("validate_pilot_checklist", file=str(path), stdout=output)
    assert "Checklist validated" in output.getvalue()
