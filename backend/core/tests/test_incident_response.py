import json
import os
import stat
from datetime import date, datetime, timezone

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from core.incident_response import (
    POLICY,
    SEV1,
    SEV2,
    create_incident_payload,
    policy_payload,
)


def test_incident_policy_review_expiry_fails_closed():
    with pytest.raises(ValueError, match="incident policy is stale"):
        POLICY.validate(today=POLICY.review_due_on.replace(year=POLICY.review_due_on.year + 1))


def test_policy_is_current_complete_and_machine_readable():
    POLICY.validate(today=date(2026, 8, 2))
    payload = policy_payload(today=date(2026, 8, 2))
    assert {rule["severity"] for rule in payload["severity_rules"]} == {
        "SEV1",
        "SEV2",
        "SEV3",
        "SEV4",
    }
    assert "clinical_safety_lead" in payload["required_roles"]
    assert "privacy_lead" in payload["required_roles"]


def test_patient_safety_incident_defaults_to_sev1():
    payload = create_incident_payload(
        category="patient_safety",
        summary="Potential unsafe clinical output detected in synthetic validation.",
        affected_systems=("clinical-summary",),
        opened_at=datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc),
    )
    assert payload["severity"] == SEV1
    assert payload["targets"]["clinical_safety_escalation"] is True
    assert payload["patient_safety_impact"] == "UNKNOWN"
    assert payload["notification_assessment"] == "PENDING"


def test_provider_outage_defaults_to_sev2():
    payload = create_incident_payload(
        category="provider_outage",
        summary="Synthetic provider requests exceed the availability threshold.",
        affected_systems=("ai-gateway",),
    )
    assert payload["severity"] == SEV2


@pytest.mark.parametrize(
    "summary",
    (
        "Contact patient@example.test immediately",
        "Call +212612345678",
        "patient_id=42 had a failure",
    ),
)
def test_incident_metadata_rejects_direct_identifiers(summary):
    with pytest.raises(ValueError, match="direct identifier"):
        create_incident_payload(
            category="other",
            summary=summary,
            affected_systems=("api",),
        )


@pytest.mark.skipif(os.name != "posix", reason="POSIX file permissions required")
def test_create_incident_command_writes_mode_0600(tmp_path):
    output = tmp_path / "incident.json"
    call_command(
        "create_incident_record",
        category="authentication_compromise",
        summary="Unexpected authentication-token validation pattern.",
        systems="auth-api,mobile-session",
        output=str(output),
    )

    payload = json.loads(output.read_text())
    assert payload["severity"] == SEV1
    assert payload["affected_systems"] == ["auth-api", "mobile-session"]
    assert stat.S_IMODE(output.stat().st_mode) == 0o600


@pytest.mark.skipif(os.name == "posix", reason="Windows-only fail-closed check")
def test_create_incident_command_refuses_insecure_export(tmp_path):
    output = tmp_path / "incident.json"
    with pytest.raises(CommandError, match="requires POSIX file permissions"):
        call_command(
            "create_incident_record",
            category="authentication_compromise",
            summary="Synthetic incident with no patient identifiers.",
            systems="auth-api",
            output=str(output),
        )
    assert not output.exists()
    assert list(tmp_path.iterdir()) == []


def test_create_incident_command_refuses_identifying_metadata(tmp_path):
    output = tmp_path / "incident.json"
    with pytest.raises(CommandError, match="direct identifier"):
        call_command(
            "create_incident_record",
            category="data_exposure",
            summary="Exposure involved user@example.test",
            systems="api",
            output=str(output),
        )
    assert not output.exists()
