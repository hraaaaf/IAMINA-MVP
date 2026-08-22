from __future__ import annotations

from copy import deepcopy
from datetime import date
from unittest.mock import patch

import pytest

from evaluation.frug5_observed_evidence import (
    ObservedEvidenceError,
    build_observed_frug5_report,
    load_observed_evidence,
)


def test_observed_live_companion_metrics_are_reconstructed_without_guessing():
    report = build_observed_frug5_report(today=date(2026, 8, 22))

    metrics = report["metrics"]
    assert metrics["interactions"] == 8
    assert metrics["route_counts"] == {"safety": 2, "zero_model": 2, "llm": 4}
    assert metrics["llm_call_rate_per_interaction"] == 0.5
    assert metrics["zero_model_rate_per_interaction"] == 0.25
    assert metrics["safety_rate_per_interaction"] == 0.25
    assert metrics["llm_success_events"] == 4
    assert metrics["llm_error_events"] == 0

    distributions = metrics["conversation"]["distributions"]
    assert distributions["input_tokens"] == {
        "samples": 4,
        "coverage": 1.0,
        "p50": 867,
        "p95": 886,
    }
    assert distributions["output_tokens"] == {
        "samples": 4,
        "coverage": 1.0,
        "p50": 70,
        "p95": 76,
    }
    assert distributions["cached_input_tokens"] == {
        "samples": 0,
        "coverage": 0.0,
        "p50": None,
        "p95": None,
    }
    assert distributions["total_tokens"] == {
        "samples": 4,
        "coverage": 1.0,
        "p50": 929,
        "p95": 962,
    }
    assert metrics["token_totals"] == {
        "input_tokens": 3484,
        "output_tokens": 278,
        "cached_input_tokens": None,
        "total_tokens": 3762,
    }


def test_observed_cost_uses_controlled_price_and_repo_rounding_contract():
    report = build_observed_frug5_report(today=date(2026, 8, 22))

    cost = report["observed_provider_cost"]
    assert cost["status"] == (
        "priced_from_provider_reported_usage_not_billing_reconciled"
    )
    assert cost["per_call_microusd"] == [167, 173, 174, 179]
    assert cost["total_microusd"] == 693
    assert cost["per_llm_answer_microusd"] == 173.25


def test_quota_limited_baseline_remains_unavailable_and_throttle_is_retained():
    report = build_observed_frug5_report(today=date(2026, 8, 22))

    assert report["baseline_comparison"] == {
        "complete": False,
        "status": "quota_limited",
        "input_token_p50": None,
        "input_token_p95": None,
        "p95_reduction_ratio": None,
    }
    assert report["provider_throttle"] == {
        "observed": True,
        "status_code": 429,
        "dimension": "tokens_per_minute",
        "limit": 8000,
        "used_before_rejected_request": 7661,
        "rejected_request_tokens": 1178,
        "automatic_retry": False,
    }


def test_proof_boundaries_prevent_synthetic_run_from_becoming_real_traffic_claim():
    report = build_observed_frug5_report(today=date(2026, 8, 22))

    assert report["traffic"]["synthetic"] is True
    assert report["traffic"]["patient_data"] is False
    assert report["proof_boundaries"] == {
        "production_or_beta_traffic": False,
        "provider_billing_reconciliation": False,
        "native_speaker_quality_certification": False,
        "patient_egress_approval": False,
        "accepted_safe_answer_cost_available": False,
    }


def test_tampered_baseline_precision_fails_closed():
    evidence = deepcopy(load_observed_evidence())
    evidence["baseline_comparison"]["input_token_p95"] = 999

    with patch(
        "evaluation.frug5_observed_evidence.load_observed_evidence",
        return_value=evidence,
    ):
        with pytest.raises(ObservedEvidenceError, match="must remain unavailable"):
            build_observed_frug5_report(today=date(2026, 8, 22))


def test_retained_evidence_has_no_prompt_response_or_identity_payload_keys():
    evidence = load_observed_evidence()
    forbidden = {
        "patient_id",
        "user_id",
        "prompt",
        "response",
        "message",
        "raw_text",
        "document_text",
        "filename",
        "object_key",
        "email",
        "phone",
        "first_name",
        "last_name",
    }

    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                assert key not in forbidden
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(evidence)
