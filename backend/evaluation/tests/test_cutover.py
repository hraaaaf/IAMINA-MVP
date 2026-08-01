import pytest

from evaluation.cutover import CutoverEvidence, authorize_cutover
from evaluation.decision import ProviderDecision


def _decision(selected="provider-a"):
    return ProviderDecision(
        modality="text",
        selected_provider=selected,
        ranked_providers=(selected,) if selected else (),
        rejected={},
    )


def _evidence(**overrides):
    values = {
        "benchmark_report_id": "report-2026-08-01",
        "dataset_version": "1.0",
        "processor_policy_approved": True,
        "human_safety_review_approved": True,
        "rollback_documented": True,
        "rejected_alternatives_documented": True,
    }
    values.update(overrides)
    return CutoverEvidence(**values)


def test_complete_evidence_authorizes_selected_provider():
    assert authorize_cutover(_decision(), _evidence()) == "provider-a"


def test_benchmark_without_processor_policy_fails_closed():
    with pytest.raises(ValueError, match="processor_policy"):
        authorize_cutover(
            _decision(),
            _evidence(processor_policy_approved=False),
        )


def test_no_selected_provider_fails_closed():
    with pytest.raises(ValueError, match="no eligible provider"):
        authorize_cutover(_decision(selected=None), _evidence())
