from __future__ import annotations

import base64
import hashlib

from evaluation.baseer_numeric_benchmark import (
    BASEER_MODEL,
    BASEER_MODEL_REVISION,
    baseer_runtime_error_evidence,
    run_baseer_numeric_benchmark,
    run_baseer_numeric_benchmark_diagnostic,
)
from evaluation.misraj_dataset_preflight import summarize_misraj_viewer

_IMAGE_BYTES = b"baseer-c32-test-image"


def _payload() -> dict[str, object]:
    encoded = base64.b64encode(_IMAGE_BYTES).decode()
    return {
        "features": [{"name": "uuid"}, {"name": "markdown"}, {"name": "image"}],
        "num_rows_total": 400,
        "rows": [{
            "row": {
                "uuid": "expected-uuid",
                "markdown": "سكر ٥٤",
                "image": {"src": f"data:image/png;base64,{encoded}"},
            }
        }],
    }


def _source(payload: dict[str, object]) -> dict[str, object]:
    preflight = summarize_misraj_viewer(
        payload,
        expected_total_rows=400,
        expected_features=["uuid", "markdown", "image"],
        expected_first_uuid="expected-uuid",
    )
    return {
        "expected_total_rows": 400,
        "expected_features": ["uuid", "markdown", "image"],
        "expected_first_uuid": "expected-uuid",
        "expected_sample_fingerprint_sha256": preflight["sample_fingerprint_sha256"],
        "allowed_image_src_hosts": [],
        "expected_image_sha256_by_uuid": {
            "expected-uuid": hashlib.sha256(_IMAGE_BYTES).hexdigest()
        },
    }


def test_baseer_reuses_exact_numeric_safety_contract():
    payload = _payload()
    result = run_baseer_numeric_benchmark(
        payload, _source(payload), ocr_callable=lambda _: "سكر 54"
    )
    assert result["benchmark"] == "c32-misraj-baseer-ocr-exact-numeric-safety"
    assert result["engine"] == "baseer-ocr-v1.0"
    assert result["engine_config"]["model"] == BASEER_MODEL
    assert result["engine_config"]["model_revision"] == BASEER_MODEL_REVISION
    assert result["engine_config"]["device"] == "cpu"
    assert result["numeric_safe_cases"] == 1
    assert result["numeric_safety_floor_passed"] is True
    assert result["raw_ground_truth_emitted"] is False
    assert result["raw_ocr_text_emitted"] is False


def test_baseer_diagnostic_marks_pass():
    payload = _payload()
    result = run_baseer_numeric_benchmark_diagnostic(
        payload, _source(payload), ocr_callable=lambda _: "سكر 54"
    )
    assert result["execution_outcome"] == "pass"
    assert result["execution_phase"] == "complete"
    assert result["runtime_error_type"] is None


def test_baseer_diagnostic_preserves_negative_verdict():
    payload = _payload()
    result = run_baseer_numeric_benchmark_diagnostic(
        payload, _source(payload), ocr_callable=lambda _: "سكر 54 99"
    )
    assert result["execution_outcome"] == "verdict_reject"
    assert result["execution_phase"] == "complete"
    assert result["numeric_safe_cases"] == 0
    assert result["numeric_safety_floor_passed"] is False


def test_baseer_diagnostic_captures_model_init_failure_without_message():
    payload = _payload()

    def broken_factory():
        raise RuntimeError("secret runtime detail")

    result = run_baseer_numeric_benchmark_diagnostic(
        payload, _source(payload), model_factory=broken_factory
    )
    assert result["execution_outcome"] == "runtime_error"
    assert result["execution_phase"] == "model_init"
    assert result["runtime_error_type"] == "RuntimeError"
    assert "cases" not in result
    assert "secret runtime detail" not in str(result)
    assert result["raw_ground_truth_emitted"] is False
    assert result["raw_ocr_text_emitted"] is False


def test_baseer_diagnostic_captures_benchmark_failure_without_message():
    payload = _payload()

    def broken_ocr(_: bytes) -> str:
        raise ValueError("raw OCR detail must stay private")

    result = run_baseer_numeric_benchmark_diagnostic(
        payload, _source(payload), ocr_callable=broken_ocr
    )
    assert result["execution_outcome"] == "runtime_error"
    assert result["execution_phase"] == "benchmark"
    assert result["runtime_error_type"] == "ValueError"
    assert "cases" not in result
    assert "raw OCR detail must stay private" not in str(result)
    assert result["provider_api"] is False
    assert result["paid_inference"] is False


def test_runtime_error_evidence_rejects_unknown_phase():
    try:
        baseer_runtime_error_evidence(phase="mystery", exc=RuntimeError("x"))
    except ValueError as exc:
        assert str(exc) == "invalid C32 execution phase"
    else:
        raise AssertionError("unknown phase must fail closed")
