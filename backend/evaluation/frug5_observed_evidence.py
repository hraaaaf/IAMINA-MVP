"""Deterministic FRUG-5 report from one retained, content-free live provider run.

The source fixture is a transcription of privacy-safe ``iamina.cost`` events and
the aggregate 429 throttle facts from GitHub Actions run 32602461710. No prompt,
response, patient identifier, provider credential, or organization identifier is
retained here. Missing baseline/billing evidence stays unavailable.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any

from llm.cost_metrics import aggregate_cost_events
from llm.pricing import TextTokenPrice

_EVIDENCE_FILENAME = "frug5_companion_observed_2026-08-22.json"
_PRICE_FILENAME = "frug7_groq_text_price.json"
_FORBIDDEN_CONTENT_KEYS = frozenset(
    {
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
)


class ObservedEvidenceError(ValueError):
    """Raised when retained FRUG-5 evidence cannot support a truthful report."""


def _fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


def load_observed_evidence() -> dict[str, Any]:
    payload = json.loads(
        (_fixtures_dir() / _EVIDENCE_FILENAME).read_text(encoding="utf-8")
    )
    if not isinstance(payload, dict):
        raise ObservedEvidenceError("FRUG-5 evidence must be a JSON object")
    _reject_content_keys(payload)
    return payload


def load_observed_price(*, today: date) -> TextTokenPrice:
    raw = json.loads((_fixtures_dir() / _PRICE_FILENAME).read_text(encoding="utf-8"))
    price = TextTokenPrice(
        provider=raw["provider"],
        model=raw["model"],
        currency=raw["currency"],
        input_microusd_per_million=int(raw["input_microusd_per_million"]),
        cached_input_microusd_per_million=int(raw["cached_input_microusd_per_million"]),
        output_microusd_per_million=int(raw["output_microusd_per_million"]),
        evidence_reference=raw["evidence_reference"],
        verified_on=date.fromisoformat(raw["verified_on"]),
        review_due_on=date.fromisoformat(raw["review_due_on"]),
    )
    price.validate(today=today)
    return price


def build_observed_frug5_report(*, today: date) -> dict[str, Any]:
    """Aggregate the verified live run without inventing baseline or billing data."""
    evidence = load_observed_evidence()
    _validate_evidence_header(evidence)

    events = evidence.get("events")
    if not isinstance(events, list):
        raise ObservedEvidenceError("FRUG-5 evidence events must be a list")
    if not all(isinstance(event, dict) for event in events):
        raise ObservedEvidenceError("every FRUG-5 evidence event must be an object")

    aggregate = aggregate_cost_events(events)
    successful_usage = [
        event
        for event in events
        if event.get("event") == "llm_usage" and event.get("status") == "success"
    ]
    if aggregate["interactions"] <= 0:
        raise ObservedEvidenceError("observed interaction denominator is missing")
    if aggregate["llm_success_events"] != len(successful_usage):
        raise ObservedEvidenceError("LLM success aggregation does not reconcile")

    price = load_observed_price(today=today)
    provider = evidence["provider"]
    if price.provider != provider["id"] or price.model != provider["model"]:
        raise ObservedEvidenceError("controlled price does not match observed provider/model")

    costs = [_usage_cost_microusd(event, price) for event in successful_usage]
    token_totals = _token_totals(successful_usage)

    baseline = evidence.get("baseline_comparison")
    if not isinstance(baseline, dict):
        raise ObservedEvidenceError("baseline comparison metadata is missing")
    if baseline.get("complete") is not False or baseline.get("status") != "quota_limited":
        raise ObservedEvidenceError("incomplete live baseline must remain quota_limited")
    for field in ("input_token_p50", "input_token_p95", "p95_reduction_ratio"):
        if baseline.get(field) is not None:
            raise ObservedEvidenceError(f"{field} must remain unavailable")

    throttle = evidence.get("provider_throttle")
    _validate_throttle(throttle)

    proof_boundaries = evidence.get("proof_boundaries")
    if not isinstance(proof_boundaries, dict):
        raise ObservedEvidenceError("proof boundaries are missing")
    for field in (
        "production_or_beta_traffic",
        "provider_billing_reconciliation",
        "native_speaker_quality_certification",
        "patient_egress_approval",
        "accepted_safe_answer_cost_available",
    ):
        if proof_boundaries.get(field) is not False:
            raise ObservedEvidenceError(f"unsupported proof claim: {field}")

    return {
        "source": evidence["source"],
        "traffic": evidence["traffic"],
        "provider": {
            **provider,
            "pricing_evidence_reference": price.evidence_reference,
            "pricing_verified_on": price.verified_on.isoformat(),
            "pricing_review_due_on": price.review_due_on.isoformat(),
        },
        "metrics": {
            "interactions": aggregate["interactions"],
            "route_counts": aggregate["route_counts"],
            "llm_call_rate_per_interaction": aggregate[
                "llm_call_rate_per_interaction"
            ],
            "zero_model_rate_per_interaction": aggregate[
                "zero_model_rate_per_interaction"
            ],
            "safety_rate_per_interaction": aggregate["safety_rate_per_interaction"],
            "llm_success_events": aggregate["llm_success_events"],
            "llm_error_events": aggregate["llm_error_events"],
            "conversation": aggregate["by_workload"].get("conversation"),
            "token_totals": token_totals,
        },
        "observed_provider_cost": {
            "status": "priced_from_provider_reported_usage_not_billing_reconciled",
            "total_microusd": sum(costs),
            "per_llm_answer_microusd": (
                sum(costs) / len(costs) if costs else None
            ),
            "per_call_microusd": costs,
        },
        "baseline_comparison": baseline,
        "provider_throttle": throttle,
        "proof_boundaries": proof_boundaries,
    }


def _usage_cost_microusd(
    event: Mapping[str, Any],
    price: TextTokenPrice,
) -> int:
    input_tokens = _required_non_negative_int(event.get("input_tokens"), "input_tokens")
    output_tokens = _required_non_negative_int(
        event.get("output_tokens"), "output_tokens"
    )
    return price.worst_case_microusd(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


def _token_totals(events: list[dict[str, Any]]) -> dict[str, int | None]:
    input_total = sum(
        _required_non_negative_int(event.get("input_tokens"), "input_tokens")
        for event in events
    )
    output_total = sum(
        _required_non_negative_int(event.get("output_tokens"), "output_tokens")
        for event in events
    )
    total_total = sum(
        _required_non_negative_int(event.get("total_tokens"), "total_tokens")
        for event in events
    )
    cached_values = [event.get("cached_input_tokens") for event in events]
    cached_total = (
        sum(_required_non_negative_int(value, "cached_input_tokens") for value in cached_values)
        if all(value is not None for value in cached_values)
        else None
    )
    return {
        "input_tokens": input_total,
        "output_tokens": output_total,
        "cached_input_tokens": cached_total,
        "total_tokens": total_total,
    }


def _validate_evidence_header(evidence: Mapping[str, Any]) -> None:
    if evidence.get("schema_version") != 1:
        raise ObservedEvidenceError("unsupported FRUG-5 evidence schema")
    source = evidence.get("source")
    traffic = evidence.get("traffic")
    provider = evidence.get("provider")
    if not isinstance(source, dict) or not isinstance(traffic, dict) or not isinstance(provider, dict):
        raise ObservedEvidenceError("FRUG-5 evidence header is incomplete")
    if source.get("workflow_run_id") != 32602461710:
        raise ObservedEvidenceError("unexpected source workflow run")
    if traffic.get("synthetic") is not True or traffic.get("patient_data") is not False:
        raise ObservedEvidenceError("observed traffic must remain synthetic and non-patient")
    if provider.get("id") != "groq" or provider.get("model") != "openai/gpt-oss-120b":
        raise ObservedEvidenceError("unexpected observed provider/model")


def _validate_throttle(throttle: Any) -> None:
    if not isinstance(throttle, dict):
        raise ObservedEvidenceError("provider throttle evidence is missing")
    expected = {
        "observed": True,
        "status_code": 429,
        "dimension": "tokens_per_minute",
        "limit": 8000,
        "automatic_retry": False,
    }
    for key, value in expected.items():
        if throttle.get(key) != value:
            raise ObservedEvidenceError(f"unexpected throttle evidence: {key}")
    used = _required_non_negative_int(
        throttle.get("used_before_rejected_request"),
        "used_before_rejected_request",
    )
    requested = _required_non_negative_int(
        throttle.get("rejected_request_tokens"),
        "rejected_request_tokens",
    )
    if used < throttle["limit"] and used + requested <= throttle["limit"]:
        raise ObservedEvidenceError("throttle evidence does not cross the observed limit")


def _required_non_negative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ObservedEvidenceError(f"{field} must be a non-negative integer")
    return value


def _reject_content_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in _FORBIDDEN_CONTENT_KEYS:
                raise ObservedEvidenceError(f"forbidden content key in retained evidence: {key}")
            _reject_content_keys(child)
    elif isinstance(value, list):
        for child in value:
            _reject_content_keys(child)
