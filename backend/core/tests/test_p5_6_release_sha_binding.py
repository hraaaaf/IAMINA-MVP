import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

CANDIDATE_SHA = "a" * 40
OTHER_SHA = "b" * 40


def test_consent_release_audit_requires_exact_candidate_sha(monkeypatch, capsys):
    monkeypatch.setattr(
        "core.management.commands.audit_pilot_consent_governance.consent_governance_payload",
        lambda **_: {"status": "approved", "blockers": []},
    )

    with pytest.raises(CommandError, match="exact candidate source commit SHA is required"):
        call_command("audit_pilot_consent_governance", "--require-approved")

    call_command(
        "audit_pilot_consent_governance",
        "--require-approved",
        "--expected-source-commit-sha",
        CANDIDATE_SHA,
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["audited_source_commit_sha"] == CANDIDATE_SHA


def test_release_audit_rejects_invalid_candidate_sha(monkeypatch):
    monkeypatch.setattr(
        "core.management.commands.audit_pilot_consent_governance.consent_governance_payload",
        lambda **_: {"status": "approved", "blockers": []},
    )

    with pytest.raises(CommandError, match="full 40-character Git SHA"):
        call_command(
            "audit_pilot_consent_governance",
            "--require-approved",
            "--expected-source-commit-sha",
            "abc123",
        )


@pytest.mark.parametrize(
    ("command_name", "payload_target"),
    [
        (
            "audit_pilot_data_residency",
            "core.management.commands.audit_pilot_data_residency.residency_readiness_payload",
        ),
        (
            "audit_safety_corpus_review",
            "core.management.commands.audit_safety_corpus_review.native_review_readiness_payload",
        ),
    ],
)
def test_manifest_backed_release_audits_reject_sha_mismatch(
    monkeypatch,
    command_name,
    payload_target,
):
    monkeypatch.setattr(
        payload_target,
        lambda **_: {
            "status": "approved",
            "blockers": [],
            "source_commit_sha": OTHER_SHA,
        },
    )

    with pytest.raises(CommandError, match="does not match the expected candidate SHA"):
        call_command(
            command_name,
            "--require-approved",
            "--expected-source-commit-sha",
            CANDIDATE_SHA,
        )


@pytest.mark.parametrize(
    ("command_name", "payload_target"),
    [
        (
            "audit_pilot_data_residency",
            "core.management.commands.audit_pilot_data_residency.residency_readiness_payload",
        ),
        (
            "audit_safety_corpus_review",
            "core.management.commands.audit_safety_corpus_review.native_review_readiness_payload",
        ),
    ],
)
def test_manifest_backed_release_audits_emit_bound_candidate_sha(
    monkeypatch,
    capsys,
    command_name,
    payload_target,
):
    monkeypatch.setattr(
        payload_target,
        lambda **_: {
            "status": "approved",
            "blockers": [],
            "source_commit_sha": CANDIDATE_SHA,
        },
    )

    call_command(
        command_name,
        "--require-approved",
        "--expected-source-commit-sha",
        CANDIDATE_SHA,
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["source_commit_sha"] == CANDIDATE_SHA
    assert payload["audited_source_commit_sha"] == CANDIDATE_SHA
