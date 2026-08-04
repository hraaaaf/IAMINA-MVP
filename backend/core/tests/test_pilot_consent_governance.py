from datetime import date

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from core.ai_processor_policy import registered_processor_policies
from core.pilot_consent_governance import (
    APPROVED,
    CONSENT_MATRIX,
    PROCESSOR_EVIDENCE,
    ApprovalEvidence,
    consent_governance_payload,
    validate_consent_governance,
)

TODAY = date(2026, 8, 4)


def test_consent_matrix_covers_every_runtime_purpose_and_modality():
    expected = {
        (purpose, modality)
        for policy in registered_processor_policies().values()
        for purpose in policy.allowed_purposes
        for modality in policy.allowed_modalities
    }
    actual = {(item.purpose, item.modality) for item in CONSENT_MATRIX}

    validate_consent_governance(today=TODAY)
    assert actual == expected


def test_every_raw_media_path_requires_granular_consent():
    raw = [item for item in CONSENT_MATRIX if item.modality in {"audio", "image", "document"}]

    assert raw
    assert all(item.base_ai_consent_required for item in raw)
    assert all(item.raw_media_consent_required for item in raw)
    assert all(item.health_data_authorization_required for item in raw)
    assert all(item.foreign_transfer_gate_required for item in raw)
    assert all(item.processor_approval_required for item in raw)


def test_patient_consent_never_substitutes_for_external_approvals():
    payload = consent_governance_payload(today=TODAY)

    assert payload["status"] == "pending_external_approval"
    assert payload["blockers"]
    assert any("cndp_health_processing_authorization" in item for item in payload["blockers"])
    assert any("cndp_foreign_transfer_authorization" in item for item in payload["blockers"])
    assert any("contract_dpa" in item for item in payload["blockers"])


def test_real_pilot_gate_fails_while_external_evidence_is_pending():
    with pytest.raises(ValueError, match="not approved"):
        consent_governance_payload(today=TODAY, require_approved=True)


def test_local_fallbacks_are_not_foreign_processors():
    for provider in ("fallback", "quota-exhausted"):
        record = PROCESSOR_EVIDENCE[provider]
        assert record.external_egress is False
        assert record.blockers(today=TODAY) == ()


def test_external_runtime_provider_cannot_be_approved_ahead_of_governance():
    runtime = registered_processor_policies()
    for provider, record in PROCESSOR_EVIDENCE.items():
        if record.external_egress:
            assert runtime[provider].status != APPROVED
            assert record.blockers(today=TODAY)


def test_stale_approved_evidence_is_rejected():
    evidence = ApprovalEvidence(
        status=APPROVED,
        reference="restricted approval ledger ref",
        owner_role="Privacy Owner",
        reviewed_on=date(2026, 1, 1),
        review_due_on=date(2026, 7, 31),
    )

    with pytest.raises(ValueError, match="stale"):
        evidence.validate(label="provider.evidence", today=TODAY)


def test_audit_command_reports_pending_without_fabricating_approval(capsys):
    call_command("audit_pilot_consent_governance")
    output = capsys.readouterr().out

    assert '"status": "pending_external_approval"' in output
    assert '"non_claim"' in output


def test_audit_command_require_approved_is_fail_closed():
    with pytest.raises(CommandError, match="not approved"):
        call_command("audit_pilot_consent_governance", "--require-approved")
