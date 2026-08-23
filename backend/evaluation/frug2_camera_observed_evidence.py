"""Validate retained, content-free FRUG-2 camera OCR evidence."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_EVIDENCE_FILENAME = "frug2_camera_observed_2026-08-23.json"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_KEYS = frozenset({"raw_text", "ocr_text", "patient_name", "name", "prompt", "response"})


class CameraObservedEvidenceError(ValueError):
    """Raised when retained camera evidence overclaims or contains raw content."""


def _fixture_path() -> Path:
    return Path(__file__).parent / "fixtures" / _EVIDENCE_FILENAME


def load_camera_observed_evidence() -> dict[str, Any]:
    payload = json.loads(_fixture_path().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CameraObservedEvidenceError("camera evidence must be an object")
    _reject_forbidden_keys(payload)
    _validate(payload)
    return payload


def build_camera_observed_summary() -> dict[str, Any]:
    evidence = load_camera_observed_evidence()
    cases = evidence["cases"]
    return {
        "source": evidence["source"],
        "engine": evidence["engine"],
        "aggregate": evidence["aggregate"],
        "case_results": {
            case["fixture_id"]: {
                "critical_token_recall": case["critical_token_recall"],
                "generic_local_result": case["generic_local_result"],
            }
            for case in cases
        },
        "policy_conclusion": evidence["policy_conclusion"],
        "proof_boundaries": evidence["proof_boundaries"],
    }


def _validate(evidence: dict[str, Any]) -> None:
    if evidence.get("schema_version") != 1:
        raise CameraObservedEvidenceError("unsupported camera evidence schema")
    traffic = evidence.get("traffic")
    if not isinstance(traffic, dict) or traffic.get("patient_data") is not False:
        raise CameraObservedEvidenceError("camera evidence must remain non-patient")
    source = evidence.get("source")
    if not isinstance(source, dict) or source.get("fixture_content_retained_in_repo") is not False:
        raise CameraObservedEvidenceError("raw camera fixtures must not be retained in repo")
    cases = evidence.get("cases")
    if not isinstance(cases, list) or len(cases) != 5:
        raise CameraObservedEvidenceError("exactly five controlled camera cases are required")
    seen: set[str] = set()
    pass_count = 0
    fail_count = 0
    for case in cases:
        if not isinstance(case, dict):
            raise CameraObservedEvidenceError("every camera case must be an object")
        fixture_id = case.get("fixture_id")
        if not isinstance(fixture_id, str) or not fixture_id or fixture_id in seen:
            raise CameraObservedEvidenceError("fixture ids must be unique non-empty strings")
        seen.add(fixture_id)
        digest = case.get("fixture_sha256")
        if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
            raise CameraObservedEvidenceError(f"{fixture_id}: invalid SHA-256")
        required = case.get("required_exact_tokens")
        found = case.get("found_exact_tokens")
        if not isinstance(required, list) or not required or not isinstance(found, list):
            raise CameraObservedEvidenceError(f"{fixture_id}: exact-token evidence is incomplete")
        if not set(found).issubset(set(required)):
            raise CameraObservedEvidenceError(f"{fixture_id}: found tokens must be pinned tokens")
        recall = case.get("critical_token_recall")
        expected_recall = len(found) / len(required)
        if not isinstance(recall, (int, float)) or abs(float(recall) - expected_recall) > 1e-12:
            raise CameraObservedEvidenceError(f"{fixture_id}: token recall does not reconcile")
        result = case.get("generic_local_result")
        expected_result = "critical_tokens_pass" if len(found) == len(required) else "critical_tokens_fail"
        if result != expected_result:
            raise CameraObservedEvidenceError(f"{fixture_id}: local result does not reconcile")
        pass_count += int(result == "critical_tokens_pass")
        fail_count += int(result == "critical_tokens_fail")
    aggregate = evidence.get("aggregate")
    if not isinstance(aggregate, dict):
        raise CameraObservedEvidenceError("aggregate is missing")
    expected = {
        "cases": len(cases),
        "generic_local_critical_pass_cases": pass_count,
        "generic_local_critical_fail_cases": fail_count,
    }
    for key, value in expected.items():
        if aggregate.get(key) != value:
            raise CameraObservedEvidenceError(f"aggregate mismatch: {key}")
    policy = evidence.get("policy_conclusion")
    if not isinstance(policy, dict):
        raise CameraObservedEvidenceError("policy conclusion is missing")
    for key in (
        "full_arabic_local_primary_qualified",
        "free_handwriting_generic_local_primary_qualified",
        "generic_document_ocr_replaces_glucometer_lane",
    ):
        if policy.get(key) is not False:
            raise CameraObservedEvidenceError(f"unsupported promotion claim: {key}")
    boundaries = evidence.get("proof_boundaries")
    if not isinstance(boundaries, dict):
        raise CameraObservedEvidenceError("proof boundaries are missing")
    for key in (
        "production_or_beta_route_mix",
        "patient_data",
        "raw_fixture_content_retained",
        "runtime_lane_promoted_by_this_evidence",
        "cloud_provider_accuracy_measured",
    ):
        if boundaries.get(key) is not False:
            raise CameraObservedEvidenceError(f"unsupported proof claim: {key}")


def _reject_forbidden_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in _FORBIDDEN_KEYS:
                raise CameraObservedEvidenceError(f"forbidden raw-content key: {key}")
            _reject_forbidden_keys(child)
    elif isinstance(value, list):
        for child in value:
            _reject_forbidden_keys(child)
