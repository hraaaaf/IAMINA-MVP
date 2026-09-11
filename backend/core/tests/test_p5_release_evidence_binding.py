import json
from datetime import date

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from core.management.commands import audit_pilot_data_residency as residency_command
from core.management.commands import audit_safety_corpus_review as safety_command
from core.release_evidence_binding import (
    CONSENT_RELEASE_SCHEMA_VERSION,
    consent_release_approval_payload,
    require_matching_source_sha,
)

SOURCE_SHA = "1" * 40
OTHER_SHA = "2" * 40
TODAY = date(2026, 9, 11)


def _consent_manifest(*, source_sha=SOURCE_SHA, processors=None):
    return {
        "schema_version": CONSENT_RELEASE_SCHEMA_VERSION,
        "pilot_country": "MA",
        "source_commit_sha": source_sha,
        "controller_reference": "CTRL-MA-001",
        "patient_notice_reference": "PATIENT-NOTICE-001",
        "base_ai_consent_reference": "BASE-AI-CONSENT-001",
        "raw_media_consent_reference": "RAW-MEDIA-CONSENT-001",
        "health_data_authorization_reference": "CNDP-HEALTH-001",
        "privacy_approval_reference": "PRIVACY-APPROVAL-001",
        "security_approval_reference": "SECURITY-APPROVAL-001",
        "reviewed_on": "2026-09-11",
        "review_due_on": "2026-12-31",
        "external_processor_approvals": processors or [],
    }


def _processor_approval(provider):
    return {
        "provider": provider,
        "processor_identity_reference": f"{provider}-IDENTITY-001",
        "contract_dpa_reference": f"{provider}-DPA-001",
        "subprocessor_register_reference": f"{provider}-SUBPROCESSORS-001",
        "processing_regions_reference": f"{provider}-REGIONS-001",
        "retention_and_deletion_reference": f"{provider}-RETENTION-001",
        "training_use_reference": f"{provider}-TRAINING-001",
        "security_review_reference": f"{provider}-SECURITY-001",
        "privacy_review_reference": f"{provider}-PRIVACY-001",
        "cndp_health_processing_authorization_reference": f"{provider}-CNDP-HEALTH-001",
        "cndp_foreign_transfer_authorization_reference": f"{provider}-CNDP-TRANSFER-001",
    }


def _write_json(tmp_path, name, payload):
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_matching_source_sha_is_required_for_candidate_release_evidence():
    with pytest.raises(ValueError, match="expected release source SHA is required"):
        require_matching_source_sha(
            {"source_commit_sha": SOURCE_SHA},
            expected_source_sha=None,
            gate="test gate",
        )

    with pytest.raises(ValueError, match="source_commit_sha mismatch"):
        require_matching_source_sha(
            {"source_commit_sha": SOURCE_SHA},
            expected_source_sha=OTHER_SHA,
            gate="test gate",
        )

    assert (
        require_matching_source_sha(
            {"source_commit_sha": SOURCE_SHA},
            expected_source_sha=SOURCE_SHA,
            gate="test gate",
        )
        == SOURCE_SHA
    )


def test_local_only_consent_release_manifest_passes_for_exact_candidate(tmp_path):
    path = _write_json(tmp_path, "consent.json", _consent_manifest())

    payload = consent_release_approval_payload(
        manifest_path=path,
        expected_source_sha=SOURCE_SHA,
        today=TODAY,
    )

    assert payload["status"] == "approved_for_candidate"
    assert payload["source_commit_sha"] == SOURCE_SHA
    assert payload["approved_external_processors"] == []


def test_consent_release_manifest_rejects_wrong_candidate_sha(tmp_path):
    path = _write_json(tmp_path, "consent.json", _consent_manifest())

    with pytest.raises(ValueError, match="source_commit_sha mismatch"):
        consent_release_approval_payload(
            manifest_path=path,
            expected_source_sha=OTHER_SHA,
            today=TODAY,
        )


def test_consent_release_manifest_rejects_unapproved_external_provider(tmp_path):
    path = _write_json(
        tmp_path,
        "consent.json",
        _consent_manifest(processors=[_processor_approval("groq")]),
    )

    with pytest.raises(ValueError, match="provider drift"):
        consent_release_approval_payload(
            manifest_path=path,
            expected_source_sha=SOURCE_SHA,
            today=TODAY,
        )


def test_consent_audit_require_approved_is_candidate_bound(tmp_path, capsys):
    path = _write_json(tmp_path, "consent.json", _consent_manifest())

    call_command(
        "audit_pilot_consent_governance",
        "--manifest",
        str(path),
        "--expected-source-sha",
        SOURCE_SHA,
        "--require-approved",
    )

    output = capsys.readouterr().out
    assert '"status": "approved_for_candidate"' in output
    assert f'"source_commit_sha": "{SOURCE_SHA}"' in output

    with pytest.raises(CommandError, match="source_commit_sha mismatch"):
        call_command(
            "audit_pilot_consent_governance",
            "--manifest",
            str(path),
            "--expected-source-sha",
            OTHER_SHA,
            "--require-approved",
        )


def test_residency_audit_enforces_exact_candidate_sha(monkeypatch, capsys):
    monkeypatch.setattr(
        residency_command,
        "residency_readiness_payload",
        lambda **kwargs: {"status": "approved", "source_commit_sha": SOURCE_SHA},
    )

    call_command(
        "audit_pilot_data_residency",
        "--manifest",
        "/restricted/test.json",
        "--expected-source-sha",
        SOURCE_SHA,
        "--require-approved",
    )
    assert f'"source_commit_sha": "{SOURCE_SHA}"' in capsys.readouterr().out

    with pytest.raises(CommandError, match="source_commit_sha mismatch"):
        call_command(
            "audit_pilot_data_residency",
            "--manifest",
            "/restricted/test.json",
            "--expected-source-sha",
            OTHER_SHA,
            "--require-approved",
        )


def test_safety_audit_enforces_exact_candidate_sha(monkeypatch, capsys):
    monkeypatch.setattr(
        safety_command,
        "native_review_readiness_payload",
        lambda **kwargs: {"status": "approved", "source_commit_sha": SOURCE_SHA},
    )

    call_command(
        "audit_safety_corpus_review",
        "--manifest",
        "/restricted/test.json",
        "--expected-source-sha",
        SOURCE_SHA,
        "--require-approved",
    )
    assert f'"source_commit_sha": "{SOURCE_SHA}"' in capsys.readouterr().out

    with pytest.raises(CommandError, match="source_commit_sha mismatch"):
        call_command(
            "audit_safety_corpus_review",
            "--manifest",
            "/restricted/test.json",
            "--expected-source-sha",
            OTHER_SHA,
            "--require-approved",
        )


def test_release_sha_can_come_from_environment(monkeypatch):
    monkeypatch.setenv("PILOT_RELEASE_SOURCE_SHA", SOURCE_SHA)
    assert (
        require_matching_source_sha(
            {"source_commit_sha": SOURCE_SHA},
            expected_source_sha=None,
            gate="test gate",
        )
        == SOURCE_SHA
    )
