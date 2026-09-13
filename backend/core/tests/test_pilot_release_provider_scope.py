import json
from datetime import date

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from core.pilot_release_provider_scope import (
    GLOBAL_HEALTH_PROCESSING_BLOCKER,
    release_scoped_consent_governance_payload,
)

TODAY = date(2026, 8, 4)
SOURCE_SHA = "e8955e9793fd35d8f605b5ec444136131b4653b2"


def test_local_only_release_ignores_disabled_network_provider_blockers():
    payload = release_scoped_consent_governance_payload(
        enabled_external_providers=(),
        today=TODAY,
    )

    assert payload["release_mode"] == "local_only"
    assert payload["enabled_external_providers"] == []
    assert payload["blockers"] == [GLOBAL_HEALTH_PROCESSING_BLOCKER]
    assert payload["global_health_processing_references"] == []
    assert not any("gemini.contract_dpa" in item for item in payload["blockers"])
    assert not any("groq.processing_regions" in item for item in payload["blockers"])
    assert all(
        row["release_enabled"] is False
        for row in payload["processors"]
        if row["external_egress"]
    )


def test_local_only_release_still_fails_closed_on_global_health_authorization():
    with pytest.raises(ValueError, match="cndp_health_processing_authorization"):
        release_scoped_consent_governance_payload(
            enabled_external_providers=(),
            today=TODAY,
            require_approved=True,
        )


def test_validated_health_reference_clears_only_global_local_only_blocker():
    payload = release_scoped_consent_governance_payload(
        enabled_external_providers=(),
        global_health_processing_references=("restricted-cndp-health-ref",),
        today=TODAY,
        require_approved=True,
    )

    assert payload["status"] == "approved"
    assert payload["blockers"] == []
    assert payload["global_health_processing_references"] == [
        "restricted-cndp-health-ref"
    ]


def test_enabled_network_provider_restores_its_processor_blockers():
    payload = release_scoped_consent_governance_payload(
        enabled_external_providers=("gemini",),
        today=TODAY,
    )

    assert payload["release_mode"] == "external_processors_enabled"
    assert payload["enabled_external_providers"] == ["gemini"]
    assert any("gemini.contract_dpa" in item for item in payload["blockers"])
    assert any("gemini.processing_regions" in item for item in payload["blockers"])
    gemini = next(row for row in payload["processors"] if row["provider"] == "gemini")
    groq = next(row for row in payload["processors"] if row["provider"] == "groq")
    assert gemini["release_enabled"] is True
    assert groq["release_enabled"] is False


def test_release_scope_rejects_unknown_or_local_provider_as_external():
    with pytest.raises(ValueError, match="unknown"):
        release_scoped_consent_governance_payload(
            enabled_external_providers=("not-a-provider",),
            today=TODAY,
        )
    with pytest.raises(ValueError, match="local providers"):
        release_scoped_consent_governance_payload(
            enabled_external_providers=("fallback",),
            today=TODAY,
        )


def test_local_only_audit_command_reports_only_release_applicable_blocker(capsys):
    call_command("audit_pilot_consent_governance", "--local-only")
    payload = json.loads(capsys.readouterr().out)

    assert payload["release_mode"] == "local_only"
    assert payload["blockers"] == [GLOBAL_HEALTH_PROCESSING_BLOCKER]
    gemini = next(row for row in payload["processors"] if row["provider"] == "gemini")
    assert gemini["release_enabled"] is False
    assert any("gemini.contract_dpa" in item for item in gemini["blockers"])


def test_local_only_audit_require_approved_remains_fail_closed():
    with pytest.raises(CommandError, match="cndp_health_processing_authorization"):
        call_command(
            "audit_pilot_consent_governance",
            "--local-only",
            "--require-approved",
        )


def _approved_residency_payload(source_sha=SOURCE_SHA):
    return {
        "status": "approved",
        "source_commit_sha": source_sha,
        "flows": [
            {
                "enabled": True,
                "data_categories": ["account_data", "health_data"],
                "cndp_health_processing_reference": "restricted-cndp-health-ref",
            }
        ],
    }


def test_local_only_audit_can_bind_validated_residency_health_evidence(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "core.management.commands.audit_pilot_consent_governance.residency_readiness_payload",
        lambda **kwargs: _approved_residency_payload(),
    )

    call_command(
        "audit_pilot_consent_governance",
        "--local-only",
        "--residency-manifest",
        "/restricted/iamina/pilot-residency.json",
        "--require-approved",
        "--expected-source-commit-sha",
        SOURCE_SHA,
    )
    payload = json.loads(capsys.readouterr().out)

    assert payload["status"] == "approved"
    assert payload["blockers"] == []
    assert payload["source_commit_sha"] == SOURCE_SHA
    assert payload["audited_source_commit_sha"] == SOURCE_SHA
    assert payload["global_health_processing_references"] == [
        "restricted-cndp-health-ref"
    ]


def test_local_only_audit_rejects_residency_manifest_for_wrong_candidate(monkeypatch):
    monkeypatch.setattr(
        "core.management.commands.audit_pilot_consent_governance.residency_readiness_payload",
        lambda **kwargs: _approved_residency_payload("a" * 40),
    )

    with pytest.raises(CommandError, match="source_commit_sha does not match"):
        call_command(
            "audit_pilot_consent_governance",
            "--local-only",
            "--residency-manifest",
            "/restricted/iamina/pilot-residency.json",
            "--require-approved",
            "--expected-source-commit-sha",
            SOURCE_SHA,
        )


def test_residency_manifest_flag_requires_local_only():
    with pytest.raises(CommandError, match="requires --local-only"):
        call_command(
            "audit_pilot_consent_governance",
            "--residency-manifest",
            "/restricted/iamina/pilot-residency.json",
        )
