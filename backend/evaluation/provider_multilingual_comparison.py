"""Bounded multi-provider conversation benchmark for IAMINA issue #509.

The benchmark reuses the retained ten-locale synthetic Companion corpus. Missing
credentials are reported as unavailable, never as zero-cost or failed quality.
Each attempted provider gets exactly one request per case and no hidden retry.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from time import perf_counter
from typing import Any, Mapping

from evaluation.frug5_multilingual_quality_benchmark import (
    CASES,
    MAX_OUTPUT_TOKENS_PER_CASE,
    SYSTEM_PROMPT,
    _case_prompt,
    machine_review,
    strict_response_format,
)

PRICE_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "provider_comparison_prices_2026-08-26.json"
)
SPEND_CEILING_MICROUSD_PER_PROVIDER = 20_000
NEW_PROVIDER_IDS = frozenset({"deepinfra", "together", "cloudflare"})
CONTROL_PROVIDER_ID = "groq"


class BenchmarkConfigurationError(RuntimeError):
    """Raised when the controlled benchmark cannot run truthfully."""


@dataclass(frozen=True, slots=True)
class ProviderSpec:
    provider_id: str
    model: str
    base_url: str
    api_key_envs: tuple[str, ...]
    input_microusd_per_million: int
    output_microusd_per_million: int
    cached_input_microusd_per_million: int | None
    evidence_reference: str
    verified_on: str
    account_id_env: str | None = None

    def validate(self) -> None:
        if not self.provider_id or not self.model or not self.base_url:
            raise BenchmarkConfigurationError("provider identity/base URL must be explicit")
        if not self.api_key_envs:
            raise BenchmarkConfigurationError(f"{self.provider_id}: API key env is required")
        if self.input_microusd_per_million < 0 or self.output_microusd_per_million < 0:
            raise BenchmarkConfigurationError(f"{self.provider_id}: negative price")
        if (
            self.cached_input_microusd_per_million is not None
            and self.cached_input_microusd_per_million < 0
        ):
            raise BenchmarkConfigurationError(f"{self.provider_id}: negative cached price")
        if not self.evidence_reference.startswith("https://"):
            raise BenchmarkConfigurationError(f"{self.provider_id}: controlled price source missing")


def load_provider_specs() -> tuple[ProviderSpec, ...]:
    raw = json.loads(PRICE_FIXTURE_PATH.read_text(encoding="utf-8"))
    if raw.get("verified_on") != "2026-08-26":
        raise BenchmarkConfigurationError("provider price fixture verification date drifted")
    specs: list[ProviderSpec] = []
    for provider_id, row in raw["providers"].items():
        spec = ProviderSpec(
            provider_id=provider_id,
            model=row["model"],
            base_url=row["base_url"],
            api_key_envs=tuple(row["api_key_envs"]),
            input_microusd_per_million=int(row["input_microusd_per_million"]),
            output_microusd_per_million=int(row["output_microusd_per_million"]),
            cached_input_microusd_per_million=(
                int(row["cached_input_microusd_per_million"])
                if row.get("cached_input_microusd_per_million") is not None
                else None
            ),
            evidence_reference=row["evidence_reference"],
            verified_on=raw["verified_on"],
            account_id_env=row.get("account_id_env"),
        )
        spec.validate()
        specs.append(spec)
    ids = {spec.provider_id for spec in specs}
    required = NEW_PROVIDER_IDS | {CONTROL_PROVIDER_ID}
    if ids != required:
        raise BenchmarkConfigurationError(
            f"provider fixture mismatch: expected {sorted(required)}, got {sorted(ids)}"
        )
    return tuple(specs)


def resolve_credentials(
    spec: ProviderSpec,
    env: Mapping[str, str] | None = None,
) -> tuple[str | None, str | None, str | None]:
    source = os.environ if env is None else env
    api_key = next(
        (source.get(name, "").strip() for name in spec.api_key_envs if source.get(name, "").strip()),
        None,
    )
    if api_key is None:
        return None, None, "missing_api_key"

    base_url = spec.base_url
    if spec.account_id_env:
        account_id = source.get(spec.account_id_env, "").strip()
        if not account_id:
            return None, None, "missing_account_id"
        base_url = base_url.replace("{account_id}", account_id)
    return api_key, base_url, None


def latency_summary(latencies_ms: list[int]) -> dict[str, int | float | None]:
    if not latencies_ms:
        return {"successful_calls": 0, "p50_ms": None, "p95_ms": None}
    ordered = sorted(latencies_ms)
    p95_index = max(0, math.ceil(len(ordered) * 0.95) - 1)
    return {
        "successful_calls": len(ordered),
        "p50_ms": round(float(median(ordered)), 1),
        "p95_ms": ordered[p95_index],
    }


def _usage_row(response) -> dict[str, int | None]:
    usage = getattr(response, "usage", None)
    if usage is None:
        raise BenchmarkConfigurationError("provider usage evidence missing")
    details = getattr(usage, "prompt_tokens_details", None)
    cached = getattr(details, "cached_tokens", None) if details is not None else None
    return {
        "input_tokens": getattr(usage, "prompt_tokens", None),
        "output_tokens": getattr(usage, "completion_tokens", None),
        "cached_input_tokens": cached,
        "total_tokens": getattr(usage, "total_tokens", None),
    }


def list_price_equivalent_microusd(
    spec: ProviderSpec,
    usage: Mapping[str, int | None],
) -> int:
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    cached_tokens = usage.get("cached_input_tokens")
    if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
        raise BenchmarkConfigurationError(f"{spec.provider_id}: provider token counts missing")
    if input_tokens < 0 or output_tokens < 0:
        raise BenchmarkConfigurationError(f"{spec.provider_id}: invalid negative token count")

    cached = cached_tokens if isinstance(cached_tokens, int) and cached_tokens >= 0 else 0
    cached = min(cached, input_tokens)
    uncached = input_tokens - cached
    cached_rate = spec.cached_input_microusd_per_million
    if cached_rate is None:
        uncached = input_tokens
        cached = 0
        cached_rate = 0

    numerator = (
        uncached * spec.input_microusd_per_million
        + cached * cached_rate
        + output_tokens * spec.output_microusd_per_million
    )
    return math.ceil(numerator / 1_000_000)


def projected_spend_microusd(spec: ProviderSpec) -> int:
    total = 0
    for case in CASES:
        input_upper_bound = len((SYSTEM_PROMPT + _case_prompt(case)).encode("utf-8"))
        total += math.ceil(
            (
                input_upper_bound * spec.input_microusd_per_million
                + MAX_OUTPUT_TOKENS_PER_CASE * spec.output_microusd_per_million
            )
            / 1_000_000
        )
    return total


def _error_status(exc: Exception) -> int | None:
    value = getattr(exc, "status_code", None)
    return value if isinstance(value, int) else None


def _run_provider(spec: ProviderSpec, api_key: str, base_url: str) -> dict[str, Any]:
    from openai import OpenAI

    projected = projected_spend_microusd(spec)
    if projected > SPEND_CEILING_MICROUSD_PER_PROVIDER:
        raise BenchmarkConfigurationError(
            f"{spec.provider_id}: projected spend {projected} exceeds ceiling"
        )

    client = OpenAI(base_url=base_url, api_key=api_key, timeout=30.0, max_retries=0)
    rows: list[dict[str, Any]] = []
    latencies: list[int] = []
    total_cost = 0
    machine_passed = True
    try:
        for case in CASES:
            started = perf_counter()
            try:
                response = client.chat.completions.create(
                    model=spec.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": _case_prompt(case)},
                    ],
                    max_tokens=MAX_OUTPUT_TOKENS_PER_CASE,
                    response_format=strict_response_format(),
                )
                latency_ms = max(0, round((perf_counter() - started) * 1000))
                parsed = json.loads(response.choices[0].message.content or "")
                reply = parsed.get("reply") if isinstance(parsed, dict) else None
                usage = _usage_row(response)
                cost = list_price_equivalent_microusd(spec, usage)
                checks = machine_review(case, reply)
                passed = all(checks.values())
                machine_passed = machine_passed and passed
                latencies.append(latency_ms)
                total_cost += cost
                rows.append(
                    {
                        "case_id": case.case_id,
                        "locale": case.locale,
                        "provider_reply": reply,
                        "latency_ms": latency_ms,
                        "usage": usage,
                        "list_price_equivalent_microusd": cost,
                        "machine_checks": checks,
                        "machine_passed": passed,
                        "error_type": None,
                        "error_status": None,
                    }
                )
            except Exception as exc:
                machine_passed = False
                rows.append(
                    {
                        "case_id": case.case_id,
                        "locale": case.locale,
                        "provider_reply": None,
                        "latency_ms": max(0, round((perf_counter() - started) * 1000)),
                        "usage": None,
                        "list_price_equivalent_microusd": None,
                        "machine_checks": None,
                        "machine_passed": False,
                        "error_type": type(exc).__name__,
                        "error_status": _error_status(exc),
                    }
                )
                break
    finally:
        client.close()

    if total_cost > SPEND_CEILING_MICROUSD_PER_PROVIDER:
        raise BenchmarkConfigurationError(f"{spec.provider_id}: actual spend exceeded ceiling")
    completed = sum(1 for row in rows if row["usage"] is not None)
    return {
        "provider": spec.provider_id,
        "model": spec.model,
        "status": "completed" if completed == len(CASES) else "failed",
        "planned_calls": len(CASES),
        "completed_calls": completed,
        "failed_calls": len(CASES) - completed,
        "no_retries": True,
        "strict_json_schema_requested": True,
        "price_evidence_reference": spec.evidence_reference,
        "projected_max_microusd": projected,
        "list_price_equivalent_microusd": total_cost if completed else None,
        "latency": latency_summary(latencies),
        "machine_gate": {
            "passed": machine_passed and completed == len(CASES),
            "required_case_ids": [case.case_id for case in CASES],
        },
        "case_results": rows,
    }


def historical_mistral_reference() -> dict[str, Any]:
    return {
        "provider": "mistral",
        "model": "mistral-small-2603",
        "live_rerun": False,
        "retained_run": 32832569387,
        "completed_calls": 10,
        "machine_safe_calls": 10,
        "list_price_equivalent_microusd": 253,
        "artifact_id": 9557345417,
        "boundary": "retained prior evidence; human dialect review not certified",
    }


def run_benchmark(*, output_path: Path) -> dict[str, Any]:
    if os.environ.get("LLM_PROVIDER_BENCHMARK_NETWORK_AUTHORIZED", "").lower() != "true":
        raise BenchmarkConfigurationError("network benchmark is not explicitly authorized")

    provider_results: list[dict[str, Any]] = []
    for spec in load_provider_specs():
        api_key, base_url, skip_reason = resolve_credentials(spec)
        if skip_reason:
            provider_results.append(
                {
                    "provider": spec.provider_id,
                    "model": spec.model,
                    "status": "skipped",
                    "reason": skip_reason,
                    "machine_gate": {"passed": None},
                }
            )
            continue
        provider_results.append(_run_provider(spec, api_key, base_url))

    attempted_new = [
        result
        for result in provider_results
        if result["provider"] in NEW_PROVIDER_IDS and result["status"] != "skipped"
    ]
    meaningful = bool(attempted_new)
    attempted_failures = [
        result
        for result in provider_results
        if result["status"] == "failed" or result["machine_gate"].get("passed") is False
    ]
    report = {
        "benchmark": "iamina-llm-provider-comparison-v1",
        "synthetic": True,
        "patient_data": False,
        "same_ten_locale_corpus": True,
        "no_retries": True,
        "new_provider_comparison_executed": meaningful,
        "provider_results": provider_results,
        "historical_reference": historical_mistral_reference(),
        "proof_boundaries": {
            "production_or_beta_traffic": False,
            "native_speaker_certified": False,
            "provider_billing_reconciled": False,
            "patient_egress_approved": False,
            "missing_credentials_inferred_as_zero": False,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if not meaningful:
        return {**report, "exit_code": 2}
    if attempted_failures:
        return {**report, "exit_code": 1}
    return {**report, "exit_code": 0}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_benchmark(output_path=args.output)
    print(
        json.dumps(
            {
                "new_provider_comparison_executed": report[
                    "new_provider_comparison_executed"
                ],
                "providers": [
                    {
                        "provider": result["provider"],
                        "status": result["status"],
                        "machine_passed": result["machine_gate"].get("passed"),
                    }
                    for result in report["provider_results"]
                ],
            },
            ensure_ascii=False,
        )
    )
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
