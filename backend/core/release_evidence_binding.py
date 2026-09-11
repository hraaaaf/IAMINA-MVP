"""Exact-candidate binding for restricted P5-6 release evidence.

Restricted manifests remain outside Git. The release audit must receive the exact
candidate Git SHA explicitly and reject evidence created for any other candidate.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path

from core.ai_processor_policy import APPROVED, registered_processor_policies

PILOT_COUNTRY = "MA"
CONSENT_RELEASE_SCHEMA_VERSION = "2026-09-11.1"

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_REFERENCE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{2,255}$")

_CONSENT_MANIFEST_KEYS = frozenset(
    {
        "schema_version",
        "pilot_country",
        "source_commit_sha",
        "controller_reference",
        "patient_notice_reference",
        "base_ai_consent_reference",
        "raw_media_consent_reference",
        "health_data_authorization_reference",
        "privacy_approval_reference",
        "security_approval_reference",
        "reviewed_on",
        "review_due_on",
        "external_processor_approvals",
    }
)

_PROCESSOR_APPROVAL_KEYS = frozenset(
    {
        "provider",
        "processor_identity_reference",
        "contract_dpa_reference",
        "subprocessor_register_reference",
        "processing_regions_reference",
        "retention_and_deletion_reference",
        "training_use_reference",
        "security_review_reference",
        "privacy_review_reference",
        "cndp_health_processing_authorization_reference",
        "cndp_foreign_transfer_authorization_reference",
    }
)


def _require_exact_keys(payload: dict, expected: frozenset[str], *, label: str) -> None:
    actual = set(payload)
    if actual != set(expected):
        missing = sorted(set(expected) - actual)
        extra = sorted(actual - set(expected))
        raise ValueError(f"{label} keys invalid; missing={missing}, extra={extra}")


def _validate_reference(value: object, *, label: str) -> str:
    reference = str(value).strip()
    if not _REFERENCE_RE.fullmatch(reference):
        raise ValueError(f"{label} must be an opaque evidence reference")
    return reference


def _parse_date(value: object, *, label: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO date") from exc


def resolve_expected_source_sha(explicit: str | None = None) -> str:
    """Resolve and validate the exact candidate SHA used by all P5-6 audits."""
    value = (explicit or os.environ.get("PILOT_RELEASE_SOURCE_SHA", "")).strip()
    if not value:
        raise ValueError(
            "expected release source SHA is required via --expected-source-sha "
            "or PILOT_RELEASE_SOURCE_SHA"
        )
    if not _SHA_RE.fullmatch(value):
        raise ValueError("expected release source SHA must be a full lowercase Git SHA")
    return value


def require_matching_source_sha(
    payload: dict[str, object],
    *,
    expected_source_sha: str | None,
    gate: str,
) -> str:
    """Fail closed when approved evidence is not bound to the audited candidate."""
    expected = resolve_expected_source_sha(expected_source_sha)
    actual = str(payload.get("source_commit_sha", "")).strip()
    if not _SHA_RE.fullmatch(actual):
        raise ValueError(f"{gate} approved evidence lacks a valid source_commit_sha")
    if actual != expected:
        raise ValueError(
            f"{gate} source_commit_sha mismatch: evidence={actual}, expected={expected}"
        )
    return expected


def _approved_external_provider_names() -> set[str]:
    approved: set[str] = set()
    for provider, policy in registered_processor_policies().items():
        if not policy.external_egress or policy.status != APPROVED:
            continue
        policy.validate()
        approved.add(provider)
    return approved


def _load_json_object(path: str | os.PathLike[str]) -> dict:
    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise ValueError("consent governance approval manifest file does not exist")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            "consent governance approval manifest is unreadable or invalid JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError("consent governance approval manifest root must be an object")
    return payload


def consent_release_approval_payload(
    *,
    manifest_path: str | os.PathLike[str] | None = None,
    expected_source_sha: str | None = None,
    today: date | None = None,
) -> dict[str, object]:
    """Validate restricted consent/processor approvals for one exact candidate."""
    current = today or date.today()
    expected = resolve_expected_source_sha(expected_source_sha)
    selected_path = manifest_path or os.environ.get(
        "PILOT_CONSENT_GOVERNANCE_MANIFEST_PATH",
        "",
    )
    if not selected_path:
        raise ValueError("restricted consent governance approval manifest is required")

    raw = _load_json_object(selected_path)
    _require_exact_keys(raw, _CONSENT_MANIFEST_KEYS, label="consent approval manifest")

    if raw["schema_version"] != CONSENT_RELEASE_SCHEMA_VERSION:
        raise ValueError("unsupported consent approval manifest schema version")
    if raw["pilot_country"] != PILOT_COUNTRY:
        raise ValueError("consent approval manifest is not for the Morocco pilot")

    source_commit_sha = str(raw["source_commit_sha"]).strip()
    require_matching_source_sha(
        {"source_commit_sha": source_commit_sha},
        expected_source_sha=expected,
        gate="consent governance",
    )

    core_references = {
        name: _validate_reference(raw[name], label=name)
        for name in (
            "controller_reference",
            "patient_notice_reference",
            "base_ai_consent_reference",
            "raw_media_consent_reference",
            "health_data_authorization_reference",
            "privacy_approval_reference",
            "security_approval_reference",
        )
    }

    reviewed_on = _parse_date(raw["reviewed_on"], label="reviewed_on")
    review_due_on = _parse_date(raw["review_due_on"], label="review_due_on")
    if reviewed_on > current:
        raise ValueError("consent approval review date is in the future")
    if review_due_on < current:
        raise ValueError("consent approval manifest is stale")
    if review_due_on < reviewed_on:
        raise ValueError("consent approval due date precedes review date")

    approvals_raw = raw["external_processor_approvals"]
    if not isinstance(approvals_raw, list):
        raise ValueError("external_processor_approvals must be a list")

    processor_rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, item in enumerate(approvals_raw):
        if not isinstance(item, dict):
            raise ValueError(f"external_processor_approvals[{index}] must be an object")
        _require_exact_keys(
            item,
            _PROCESSOR_APPROVAL_KEYS,
            label=f"external_processor_approvals[{index}]",
        )
        provider = str(item["provider"]).strip()
        if not provider:
            raise ValueError(f"external_processor_approvals[{index}].provider is required")
        if provider in seen:
            raise ValueError(f"duplicate external processor approval: {provider}")
        seen.add(provider)
        row = {"provider": provider}
        for key in sorted(_PROCESSOR_APPROVAL_KEYS - {"provider"}):
            row[key] = _validate_reference(
                item[key],
                label=f"{provider}.{key}",
            )
        processor_rows.append(row)

    expected_providers = _approved_external_provider_names()
    if seen != expected_providers:
        missing = sorted(expected_providers - seen)
        extra = sorted(seen - expected_providers)
        raise ValueError(
            "consent approval provider drift; "
            f"missing={missing}, extra={extra}"
        )

    return {
        "schema_version": CONSENT_RELEASE_SCHEMA_VERSION,
        "pilot_country": PILOT_COUNTRY,
        "status": "approved_for_candidate",
        "source_commit_sha": source_commit_sha,
        **core_references,
        "reviewed_on": reviewed_on.isoformat(),
        "review_due_on": review_due_on.isoformat(),
        "approved_external_processors": sorted(seen),
        "external_processor_approvals": sorted(
            processor_rows,
            key=lambda row: row["provider"],
        ),
        "blockers": [],
        "non_claim": (
            "Restricted manifest validation proves recorded candidate-bound approvals; "
            "it does not replace legal, CNDP, clinical or human release authority."
        ),
    }
