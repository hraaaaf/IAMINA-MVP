import json
from copy import deepcopy
from datetime import date

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from core.pilot_data_residency import (
    SCHEMA_VERSION,
    load_residency_manifest,
    required_flow_ids,
    residency_readiness_payload,
)

TODAY = date(2026, 8, 4)
SOURCE_SHA = "e8955e9793fd35d8f605b5ec444136131b4653b2"


def _flow(
    flow_id,
    *,
    enabled=True,
    health_data=True,
    stores_data=True,
    countries=("MA",),
    regions=("ma-rabat-1",),
    transfer_reference="",
):
    if not enabled:
        return {
            "flow_id": flow_id,
            "enabled": False,
            "disabled_reason": "Explicitly disabled for the pilot deployment",
            "processor": "",
            "service": "",
            "data_categories": [],
            "stores_data": False,
            "storage_countries": [],
            "storage_regions": [],
            "processing_countries": [],
            "processing_regions": [],
            "cross_border_from_ma": False,
            "cndp_health_processing_reference": "",
            "cndp_foreign_transfer_reference": "",
            "contract_reference": "",
            "retention_reference": "",
            "owner_role": "",
            "reviewed_on": None,
            "review_due_on": None,
        }

    categories = ["account_data"]
    if health_data:
        categories.append("health_data")
    foreign = any(country != "MA" for country in countries)
    return {
        "flow_id": flow_id,
        "enabled": True,
        "disabled_reason": "",
        "processor": "Approved pilot processor",
        "service": f"Pilot service for {flow_id}",
        "data_categories": categories,
        "stores_data": stores_data,
        "storage_countries": list(countries) if stores_data else [],
        "storage_regions": list(regions) if stores_data else [],
        "processing_countries": list(countries),
        "processing_regions": list(regions),
        "cross_border_from_ma": foreign,
        "cndp_health_processing_reference": (
            "restricted-cndp-health-approval-ref" if health_data else ""
        ),
        "cndp_foreign_transfer_reference": transfer_reference,
        "contract_reference": "restricted-contract-ref",
        "retention_reference": "retention-policy-2026-08",
        "owner_role": "IAmina Privacy Owner",
        "reviewed_on": "2026-08-04",
        "review_due_on": "2026-11-04",
    }


def _manifest():
    flows = {
        "application_runtime": _flow(
            "application_runtime",
            stores_data=False,
        ),
        "primary_database": _flow("primary_database"),
        "redis_cache": _flow("redis_cache", enabled=False),
        "password_reset_email": _flow(
            "password_reset_email",
            health_data=False,
        ),
        "firebase_migration_bridge": _flow(
            "firebase_migration_bridge",
            enabled=False,
        ),
        "patient_export_staging": _flow(
            "patient_export_staging",
            enabled=False,
        ),
        "ai_provider:gemini": _flow("ai_provider:gemini", enabled=False),
        "ai_provider:kimi": _flow("ai_provider:kimi", enabled=False),
        "ai_provider:claude": _flow("ai_provider:claude", enabled=False),
    }
    assert set(flows) == required_flow_ids()
    return {
        "schema_version": SCHEMA_VERSION,
        "pilot_country": "MA",
        "controller_reference": "restricted-controller-registration-ref",
        "source_commit_sha": SOURCE_SHA,
        "privacy_approval_reference": "restricted-privacy-approval-ref",
        "security_approval_reference": "restricted-security-approval-ref",
        "reviewed_on": "2026-08-04",
        "review_due_on": "2026-11-04",
        "flows": list(flows.values()),
    }


def _write_manifest(tmp_path, payload):
    path = tmp_path / "pilot-residency.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_missing_manifest_is_pending_and_real_pilot_gate_fails():
    payload = residency_readiness_payload(today=TODAY)

    assert payload["status"] == "pending_deployment_manifest"
    assert payload["required_flows"] == sorted(required_flow_ids())
    with pytest.raises(ValueError, match="not approved"):
        residency_readiness_payload(today=TODAY, require_approved=True)


def test_complete_local_only_manifest_passes(tmp_path):
    path = _write_manifest(tmp_path, _manifest())

    payload = residency_readiness_payload(
        manifest_path=path,
        today=TODAY,
        require_approved=True,
    )

    assert payload["status"] == "approved"
    assert payload["foreign_destination_countries"] == []
    assert payload["source_commit_sha"] == SOURCE_SHA


def test_foreign_destination_without_cndp_transfer_reference_is_rejected(tmp_path):
    payload = _manifest()
    database = next(item for item in payload["flows"] if item["flow_id"] == "primary_database")
    database.update(
        {
            "storage_countries": ["FR"],
            "storage_regions": ["europe-west9"],
            "processing_countries": ["FR"],
            "processing_regions": ["europe-west9"],
            "cross_border_from_ma": True,
            "cndp_foreign_transfer_reference": "",
        }
    )
    path = _write_manifest(tmp_path, payload)

    with pytest.raises(ValueError, match="without CNDP transfer evidence"):
        residency_readiness_payload(manifest_path=path, today=TODAY)


def test_cross_border_flag_must_match_recorded_countries(tmp_path):
    payload = _manifest()
    runtime = next(
        item for item in payload["flows"] if item["flow_id"] == "application_runtime"
    )
    runtime["cross_border_from_ma"] = True
    runtime["cndp_foreign_transfer_reference"] = "restricted-transfer-ref"
    path = _write_manifest(tmp_path, payload)

    with pytest.raises(ValueError, match="flag disagrees"):
        residency_readiness_payload(manifest_path=path, today=TODAY)


def test_unapproved_network_ai_provider_cannot_be_enabled(tmp_path):
    payload = _manifest()
    flows = payload["flows"]
    index = next(i for i, item in enumerate(flows) if item["flow_id"] == "ai_provider:gemini")
    flows[index] = _flow(
        "ai_provider:gemini",
        countries=("FR",),
        regions=("europe-west9",),
        transfer_reference="restricted-transfer-ref",
    )
    path = _write_manifest(tmp_path, payload)

    with pytest.raises(ValueError, match="unapproved runtime provider gemini"):
        residency_readiness_payload(manifest_path=path, today=TODAY)


def test_manifest_must_cover_every_known_flow_exactly(tmp_path):
    payload = _manifest()
    payload["flows"] = payload["flows"][:-1]
    path = _write_manifest(tmp_path, payload)

    with pytest.raises(ValueError, match="residency flow drift"):
        residency_readiness_payload(manifest_path=path, today=TODAY)


def test_health_data_flow_requires_health_processing_authorization(tmp_path):
    payload = _manifest()
    database = next(item for item in payload["flows"] if item["flow_id"] == "primary_database")
    database["cndp_health_processing_reference"] = ""
    path = _write_manifest(tmp_path, payload)

    with pytest.raises(ValueError, match="lacks CNDP treatment authorization"):
        residency_readiness_payload(manifest_path=path, today=TODAY)


def test_secret_material_is_rejected_before_manifest_use(tmp_path):
    payload = deepcopy(_manifest())
    payload["api_key"] = "sk-this-must-never-be-in-the-manifest"
    path = _write_manifest(tmp_path, payload)

    with pytest.raises(ValueError, match="secret-like key"):
        load_residency_manifest(path)


def test_stale_manifest_is_rejected(tmp_path):
    payload = _manifest()
    payload["review_due_on"] = "2026-08-03"
    path = _write_manifest(tmp_path, payload)

    with pytest.raises(ValueError, match="manifest is stale"):
        residency_readiness_payload(manifest_path=path, today=TODAY)


def test_audit_command_default_reports_missing_manifest(monkeypatch, capsys):
    monkeypatch.delenv("PILOT_RESIDENCY_MANIFEST_PATH", raising=False)
    call_command("audit_pilot_data_residency")

    assert '"status": "pending_deployment_manifest"' in capsys.readouterr().out


def test_audit_command_require_approved_fails_without_manifest(monkeypatch):
    monkeypatch.delenv("PILOT_RESIDENCY_MANIFEST_PATH", raising=False)

    with pytest.raises(CommandError, match="not approved"):
        call_command("audit_pilot_data_residency", "--require-approved")
