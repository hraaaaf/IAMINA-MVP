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


def test_local_only_release_ignores_disabled_network_provider_blockers():
    payload = release_scoped_consent_governance_payload(
        enabled_external_providers=(),
        today=TODAY,
    )

    assert payload["release_mode"] == "local_only"
    assert payload["enabled_external_providers"] == []
    assert payload["blockers"] == [GLOBAL_HEALTH_PROCESSING_BLOCKER]
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
