"""Fail-closed Morocco pilot data-residency and foreign-transfer gate.

Deployment regions are runtime facts. They must come from a restricted, reviewed
manifest and must never be inferred from connection URLs or provider defaults.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from core.ai_processor_policy import APPROVED, registered_processor_policies

PILOT_COUNTRY = "MA"
SCHEMA_VERSION = "2026-08-04.1"

_CORE_FLOW_IDS = frozenset(
    {
        "application_runtime",
        "primary_database",
        "redis_cache",
        "password_reset_email",
        "firebase_migration_bridge",
        "patient_export_staging",
    }
)

_REQUIRED_ENABLED_FLOWS = frozenset(
    {
        "application_runtime",
        "primary_database",
        "password_reset_email",
    }
)

_FLOW_KEYS = frozenset(
    {
        "flow_id",
        "enabled",
        "disabled_reason",
        "processor",
        "service",
        "data_categories",
        "stores_data",
        "storage_countries",
        "storage_regions",
        "processing_countries",
        "processing_regions",
        "cross_border_from_ma",
        "cndp_health_processing_reference",
        "cndp_foreign_transfer_reference",
        "contract_reference",
        "retention_reference",
        "owner_role",
        "reviewed_on",
        "review_due_on",
    }
)

_MANIFEST_KEYS = frozenset(
    {
        "schema_version",
        "pilot_country",
        "controller_reference",
        "source_commit_sha",
        "privacy_approval_reference",
        "security_approval_reference",
        "reviewed_on",
        "review_due_on",
        "flows",
    }
)

_SECRET_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        r"\bsk-[A-Za-z0-9_-]{12,}\b",
        r"\bAIza[0-9A-Za-z_-]{20,}\b",
        r"(?:postgres|postgresql|redis)://[^\s:@]+:[^\s@]+@",
        r"\b(?:password|api[_-]?key|access[_-]?token|secret)\s*[=:]",
    )
)


@dataclass(frozen=True, slots=True)
class ResidencyFlow:
    flow_id: str
    enabled: bool
    disabled_reason: str
    processor: str
    service: str
    data_categories: tuple[str, ...]
    stores_data: bool
    storage_countries: tuple[str, ...]
    storage_regions: tuple[str, ...]
    processing_countries: tuple[str, ...]
    processing_regions: tuple[str, ...]
    cross_border_from_ma: bool
    cndp_health_processing_reference: str
    cndp_foreign_transfer_reference: str
    contract_reference: str
    retention_reference: str
    owner_role: str
    reviewed_on: date | None
    review_due_on: date | None

    @property
    def contains_health_data(self) -> bool:
        return "health_data" in self.data_categories

    def validate(self, *, today: date) -> None:
        if not self.flow_id.strip():
            raise ValueError("residency flow id is required")
        if not self.enabled:
            if not self.disabled_reason.strip():
                raise ValueError(f"disabled flow {self.flow_id} has no rationale")
            return

        required_text = {
            "processor": self.processor,
            "service": self.service,
            "contract_reference": self.contract_reference,
            "retention_reference": self.retention_reference,
            "owner_role": self.owner_role,
        }
        missing = sorted(name for name, value in required_text.items() if not value.strip())
        if missing:
            raise ValueError(f"flow {self.flow_id} lacks metadata: {missing}")
        if not self.data_categories:
            raise ValueError(f"flow {self.flow_id} has no data categories")
        if not self.processing_countries or not self.processing_regions:
            raise ValueError(f"flow {self.flow_id} lacks exact processing locations")
        if self.stores_data and (not self.storage_countries or not self.storage_regions):
            raise ValueError(f"flow {self.flow_id} lacks exact storage locations")
        if not self.stores_data and (self.storage_countries or self.storage_regions):
            raise ValueError(f"non-storing flow {self.flow_id} declares storage locations")
        if self.reviewed_on is None or self.review_due_on is None:
            raise ValueError(f"flow {self.flow_id} lacks review dates")
        if self.reviewed_on > today:
            raise ValueError(f"flow {self.flow_id} review date is in the future")
        if self.review_due_on < today:
            raise ValueError(f"flow {self.flow_id} evidence is stale")

        all_countries = set(self.processing_countries) | set(self.storage_countries)
        for country in all_countries:
            if not re.fullmatch(r"[A-Z]{2}", country):
                raise ValueError(f"flow {self.flow_id} has invalid country code {country!r}")
        foreign = sorted(country for country in all_countries if country != PILOT_COUNTRY)
        if self.cross_border_from_ma != bool(foreign):
            raise ValueError(
                f"flow {self.flow_id} cross-border flag disagrees with countries {foreign}"
            )
        if foreign and not self.cndp_foreign_transfer_reference.strip():
            raise ValueError(
                f"flow {self.flow_id} transfers abroad without CNDP transfer evidence"
            )
        if not foreign and self.cndp_foreign_transfer_reference.strip() not in {
            "",
            "not_applicable_local_only",
        }:
            raise ValueError(
                f"local-only flow {self.flow_id} has inconsistent transfer evidence"
            )
        if self.contains_health_data and not self.cndp_health_processing_reference.strip():
            raise ValueError(
                f"health-data flow {self.flow_id} lacks CNDP treatment authorization"
            )


@dataclass(frozen=True, slots=True)
class DeploymentResidencyManifest:
    schema_version: str
    pilot_country: str
    controller_reference: str
    source_commit_sha: str
    privacy_approval_reference: str
    security_approval_reference: str
    reviewed_on: date
    review_due_on: date
    flows: tuple[ResidencyFlow, ...]

    def validate(self, *, today: date) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("unsupported residency manifest schema version")
        if self.pilot_country != PILOT_COUNTRY:
            raise ValueError("residency manifest is not for the Morocco pilot")
        required = {
            "controller_reference": self.controller_reference,
            "source_commit_sha": self.source_commit_sha,
            "privacy_approval_reference": self.privacy_approval_reference,
            "security_approval_reference": self.security_approval_reference,
        }
        missing = sorted(name for name, value in required.items() if not value.strip())
        if missing:
            raise ValueError(f"residency manifest lacks approval metadata: {missing}")
        if not re.fullmatch(r"[0-9a-f]{40}", self.source_commit_sha):
            raise ValueError("residency manifest source_commit_sha must be a full Git SHA")
        if self.reviewed_on > today:
            raise ValueError("residency manifest review date is in the future")
        if self.review_due_on < today:
            raise ValueError("residency manifest is stale")

        expected = required_flow_ids()
        flow_map: dict[str, ResidencyFlow] = {}
        for flow in self.flows:
            if flow.flow_id in flow_map:
                raise ValueError(f"duplicate residency flow: {flow.flow_id}")
            flow.validate(today=today)
            flow_map[flow.flow_id] = flow

        if set(flow_map) != expected:
            missing_flows = sorted(expected - set(flow_map))
            extra_flows = sorted(set(flow_map) - expected)
            raise ValueError(
                f"residency flow drift; missing={missing_flows}, extra={extra_flows}"
            )
        disabled_required = sorted(
            flow_id
            for flow_id in _REQUIRED_ENABLED_FLOWS
            if not flow_map[flow_id].enabled
        )
        if disabled_required:
            raise ValueError(f"required production flows are disabled: {disabled_required}")

        policies = registered_processor_policies()
        for provider, policy in policies.items():
            if not policy.external_egress:
                continue
            flow = flow_map[f"ai_provider:{provider}"]
            if policy.status == APPROVED and not flow.enabled:
                raise ValueError(
                    f"approved runtime provider {provider} is disabled in residency manifest"
                )
            if flow.enabled and policy.status != APPROVED:
                raise ValueError(
                    f"unapproved runtime provider {provider} is enabled in residency manifest"
                )


def required_flow_ids() -> set[str]:
    external_ai = {
        f"ai_provider:{provider}"
        for provider, policy in registered_processor_policies().items()
        if policy.external_egress
    }
    return set(_CORE_FLOW_IDS) | external_ai


def _parse_date(value: object, *, field: str, allow_none: bool = False) -> date | None:
    if value in {None, ""} and allow_none:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO date") from exc


def _string_tuple(value: object, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{field} must be a list of strings")
    return tuple(item.strip() for item in value if item.strip())


def _require_exact_keys(payload: dict, expected: frozenset[str], *, label: str) -> None:
    actual = set(payload)
    if actual != set(expected):
        missing = sorted(set(expected) - actual)
        extra = sorted(actual - set(expected))
        raise ValueError(f"{label} keys invalid; missing={missing}, extra={extra}")


def _reject_secret_material(value: object, *, path: str = "manifest") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(fragment in lowered for fragment in ("password", "secret", "api_key", "token")):
                raise ValueError(f"secret-like key prohibited at {path}.{key}")
            _reject_secret_material(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_secret_material(item, path=f"{path}[{index}]")
    elif isinstance(value, str):
        if any(pattern.search(value) for pattern in _SECRET_PATTERNS):
            raise ValueError(f"secret-like value prohibited at {path}")


def _parse_flow(payload: object, *, index: int) -> ResidencyFlow:
    if not isinstance(payload, dict):
        raise ValueError(f"flows[{index}] must be an object")
    _require_exact_keys(payload, _FLOW_KEYS, label=f"flows[{index}]")
    return ResidencyFlow(
        flow_id=str(payload["flow_id"]).strip(),
        enabled=bool(payload["enabled"]),
        disabled_reason=str(payload["disabled_reason"]).strip(),
        processor=str(payload["processor"]).strip(),
        service=str(payload["service"]).strip(),
        data_categories=_string_tuple(
            payload["data_categories"], field=f"flows[{index}].data_categories"
        ),
        stores_data=bool(payload["stores_data"]),
        storage_countries=_string_tuple(
            payload["storage_countries"], field=f"flows[{index}].storage_countries"
        ),
        storage_regions=_string_tuple(
            payload["storage_regions"], field=f"flows[{index}].storage_regions"
        ),
        processing_countries=_string_tuple(
            payload["processing_countries"], field=f"flows[{index}].processing_countries"
        ),
        processing_regions=_string_tuple(
            payload["processing_regions"], field=f"flows[{index}].processing_regions"
        ),
        cross_border_from_ma=bool(payload["cross_border_from_ma"]),
        cndp_health_processing_reference=str(
            payload["cndp_health_processing_reference"]
        ).strip(),
        cndp_foreign_transfer_reference=str(
            payload["cndp_foreign_transfer_reference"]
        ).strip(),
        contract_reference=str(payload["contract_reference"]).strip(),
        retention_reference=str(payload["retention_reference"]).strip(),
        owner_role=str(payload["owner_role"]).strip(),
        reviewed_on=_parse_date(
            payload["reviewed_on"], field=f"flows[{index}].reviewed_on", allow_none=True
        ),
        review_due_on=_parse_date(
            payload["review_due_on"],
            field=f"flows[{index}].review_due_on",
            allow_none=True,
        ),
    )


def load_residency_manifest(path: str | os.PathLike[str]) -> DeploymentResidencyManifest:
    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise ValueError("residency manifest file does not exist")
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("residency manifest is unreadable or invalid JSON") from exc
    if not isinstance(raw, dict):
        raise ValueError("residency manifest root must be an object")
    _reject_secret_material(raw)
    _require_exact_keys(raw, _MANIFEST_KEYS, label="manifest")
    flows_raw = raw["flows"]
    if not isinstance(flows_raw, list):
        raise ValueError("manifest.flows must be a list")
    return DeploymentResidencyManifest(
        schema_version=str(raw["schema_version"]),
        pilot_country=str(raw["pilot_country"]),
        controller_reference=str(raw["controller_reference"]).strip(),
        source_commit_sha=str(raw["source_commit_sha"]).strip(),
        privacy_approval_reference=str(raw["privacy_approval_reference"]).strip(),
        security_approval_reference=str(raw["security_approval_reference"]).strip(),
        reviewed_on=_parse_date(raw["reviewed_on"], field="manifest.reviewed_on"),
        review_due_on=_parse_date(raw["review_due_on"], field="manifest.review_due_on"),
        flows=tuple(_parse_flow(item, index=index) for index, item in enumerate(flows_raw)),
    )


def residency_readiness_payload(
    *,
    manifest_path: str | os.PathLike[str] | None = None,
    today: date | None = None,
    require_approved: bool = False,
) -> dict[str, object]:
    current = today or date.today()
    selected_path = manifest_path or os.environ.get("PILOT_RESIDENCY_MANIFEST_PATH", "")
    if not selected_path:
        blockers = ["restricted_deployment_manifest_missing"]
        if require_approved:
            raise ValueError("pilot data residency is not approved: " + blockers[0])
        return {
            "schema_version": SCHEMA_VERSION,
            "pilot_country": PILOT_COUNTRY,
            "status": "pending_deployment_manifest",
            "required_flows": sorted(required_flow_ids()),
            "blockers": blockers,
            "non_claim": (
                "Repository configuration does not prove production storage, processing "
                "or transfer locations."
            ),
        }

    manifest = load_residency_manifest(selected_path)
    manifest.validate(today=current)
    flow_rows = []
    foreign_countries: set[str] = set()
    for flow in sorted(manifest.flows, key=lambda item: item.flow_id):
        countries = set(flow.processing_countries) | set(flow.storage_countries)
        foreign_countries.update(country for country in countries if country != PILOT_COUNTRY)
        flow_rows.append(
            {
                **asdict(flow),
                "reviewed_on": flow.reviewed_on.isoformat() if flow.reviewed_on else None,
                "review_due_on": flow.review_due_on.isoformat() if flow.review_due_on else None,
            }
        )

    payload = {
        "schema_version": manifest.schema_version,
        "pilot_country": manifest.pilot_country,
        "status": "approved",
        "controller_reference": manifest.controller_reference,
        "source_commit_sha": manifest.source_commit_sha,
        "reviewed_on": manifest.reviewed_on.isoformat(),
        "review_due_on": manifest.review_due_on.isoformat(),
        "foreign_destination_countries": sorted(foreign_countries),
        "flows": flow_rows,
        "blockers": [],
        "non_claim": (
            "Manifest validation proves recorded deployment evidence, not legal advice "
            "or regulator acceptance beyond the referenced approvals."
        ),
    }
    if require_approved:
        return payload
    return payload
