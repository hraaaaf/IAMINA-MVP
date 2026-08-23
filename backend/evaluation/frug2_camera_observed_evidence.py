"""Validate retained FRUG-2 real-camera OCR evidence without retaining raw media."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_EVIDENCE_FILENAME = "frug2_camera_observed_2026-08-23.json"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_FIXTURE_IDS = frozenset(
    {
        "arabic_typed",
        "french_handwritten_medical",
        "french_handwritten_echo",
        "lab_structured",
        "glucometer",
    }
)


class CameraEvidenceError(ValueError):
    """Raised when retained FRUG-2 camera evidence overclaims or is malformed."""


def _fixture_path() -> Path:
    return Path(__file__).parent / "fixtures" / _EVIDENCE_FILENAME


def load_camera_evidence() -> dict[str, Any]:
    payload = json.loads(_fixture_path().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CameraEvidenceError("camera evidence must be a JSON object")
    return payload


def build_camera_evidence_report() -> dict[str, Any]:
    evidence = load_camera_evidence()
    if evidence.get("schema_version") != 1:
        raise CameraEvidenceError("unsupported camera evidence schema")

    source = evidence.get("source")
    if not isinstance(source, dict):
        raise CameraEvidenceError("camera evidence source is missing")
    if source.get("patient_data") is not False:
        raise CameraEvidenceError("camera evidence must remain non-patient")
    if source.get("raw_media_retained_in_repo") is not False:
        raise CameraEvidenceError(
            "raw camera media must not be retained by this evidence"
        )
    if source.get("scope") != "controlled_user_supplied_false_documents":
        raise CameraEvidenceError("unexpected camera evidence scope")

    fixtures = evidence.get("fixtures")
    if not isinstance(fixtures, list) or len(fixtures) != 5:
        raise CameraEvidenceError(
            "exactly five controlled camera fixtures are required"
        )

    ids: set[str] = set()
    hashes: set[str] = set()
    passed = 0
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            raise CameraEvidenceError("every camera fixture must be an object")
        fixture_id = fixture.get("fixture_id")
        digest = fixture.get("sha256")
        if not isinstance(fixture_id, str) or fixture_id in ids:
            raise CameraEvidenceError("fixture ids must be unique strings")
        ids.add(fixture_id)
        if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
            raise CameraEvidenceError(f"{fixture_id}: invalid sha256")
        if digest in hashes:
            raise CameraEvidenceError("duplicate camera evidence content hash")
        hashes.add(digest)

        critical = fixture.get("critical_tokens")
        matched = fixture.get("matched_critical_tokens")
        if not isinstance(critical, list) or not critical:
            raise CameraEvidenceError(
                f"{fixture_id}: critical tokens are required"
            )
        if not isinstance(matched, list):
            raise CameraEvidenceError(
                f"{fixture_id}: matched tokens must be a list"
            )
        if not set(matched).issubset(set(critical)):
            raise CameraEvidenceError(
                f"{fixture_id}: matched tokens must be critical tokens"
            )
        expected_pass = set(matched) == set(critical)
        if fixture.get("critical_gate_passed") is not expected_pass:
            raise CameraEvidenceError(
                f"{fixture_id}: critical gate does not reconcile"
            )
        if expected_pass:
            passed += 1

    if ids != _REQUIRED_FIXTURE_IDS:
        raise CameraEvidenceError(
            "controlled camera fixture set changed unexpectedly"
        )

    aggregate = evidence.get("aggregate")
    if not isinstance(aggregate, dict):
        raise CameraEvidenceError("camera aggregate is missing")
    failed = len(fixtures) - passed
    if aggregate.get("fixtures") != len(fixtures):
        raise CameraEvidenceError("fixture count does not reconcile")
    if aggregate.get("generic_local_critical_pass") != passed:
        raise CameraEvidenceError("critical pass count does not reconcile")
    if aggregate.get("generic_local_critical_fail") != failed:
        raise CameraEvidenceError("critical fail count does not reconcile")
    rate = aggregate.get("generic_local_critical_pass_rate")
    if rate != passed / len(fixtures):
        raise CameraEvidenceError("critical pass rate does not reconcile")

    boundaries = evidence.get("proof_boundaries")
    if not isinstance(boundaries, dict):
        raise CameraEvidenceError("proof boundaries are missing")
    for field in (
        "production_or_beta_route_mix",
        "full_arabic_document_local_primary_qualified",
        "handwriting_local_primary_qualified",
        "generic_tesseract_glucometer_qualified",
        "runtime_local_executor_implemented_by_this_evidence",
        "raw_media_retained_in_repo",
    ):
        if boundaries.get(field) is not False:
            raise CameraEvidenceError(f"unsupported proof claim: {field}")

    fixture_by_id = {
        fixture["fixture_id"]: fixture for fixture in fixtures
    }
    if fixture_by_id["arabic_typed"]["critical_gate_passed"] is not True:
        raise CameraEvidenceError(
            "Arabic printed camera candidate evidence regressed"
        )
    if fixture_by_id["lab_structured"]["critical_gate_passed"] is not True:
        raise CameraEvidenceError(
            "structured lab camera candidate evidence regressed"
        )
    for fixture_id in (
        "french_handwritten_medical",
        "french_handwritten_echo",
        "glucometer",
    ):
        if fixture_by_id[fixture_id]["critical_gate_passed"] is not False:
            raise CameraEvidenceError(
                f"{fixture_id}: generic local OCR must not be promoted "
                "from this corpus"
            )

    return {
        "source": source,
        "aggregate": aggregate,
        "fixtures": fixtures,
        "proof_boundaries": boundaries,
        "routing_implications": {
            "printed_arabic": (
                "candidate passes pinned critical tokens, but one fixture "
                "is insufficient to qualify full Arabic documents as local primary"
            ),
            "structured_latin_lab": (
                "candidate passes pinned numbers and units; runtime local executor "
                "qualification remains a separate gate"
            ),
            "medical_handwriting": (
                "generic local OCR fails pinned critical numbers; keep "
                "governed/manual handling and fail closed where unavailable"
            ),
            "glucometer": (
                "generic document OCR fails pinned display tokens; keep the "
                "specialized on-device glucometer lane"
            ),
        },
    }
