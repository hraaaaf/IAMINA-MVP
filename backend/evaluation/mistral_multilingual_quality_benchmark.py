"""Bounded free-tier multilingual quality benchmark for Mistral Small 4.

The benchmark reuses IAMINA's existing ten-locale synthetic Companion corpus so
results remain comparable with the prior Groq/GPT-OSS sample. No patient data,
no retries, and no production routing decision are permitted here.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from datetime import date
from pathlib import Path
from statistics import median
from time import perf_counter
from typing import Any

from evaluation.frug5_multilingual_quality_benchmark import (
    CASES,
    MAX_OUTPUT_TOKENS_PER_CASE,
    SYSTEM_PROMPT,
    _case_prompt,
    machine_review,
    strict_response_format,
)
from evaluation.provider_benchmark_preflight import ProviderBenchmarkPreflight

PROVIDER = "mistral"
MODEL = "mistral-small-2603"
DATASET_ID = "iamina-free-llm-mistral-small4-v1"
SPEND_CEILING_MICROUSD = 5_000
TIMEOUT_SECONDS = 30.0


class BenchmarkConfigurationError(RuntimeError):
    """Raised when benchmark evidence/configuration cannot support a truthful run."""


def _price_fixture_path() -> Path:
    return Path(__file__).parent / "fixtures" / "mistral_small4_text_price.json"


def load_controlled_price(*, today: date):
    from llm.pricing import TextTokenPrice

    raw = json.loads(_price_fixture_path().read_text(encoding="utf-8"))
    price = TextTokenPrice(
        provider=raw["provider"],
        model=raw["model"],
        currency=raw["currency"],
        input_microusd_per_million=int(raw["input_microusd_per_million"]),
        cached_input_microusd_per_million=(
            int(raw["cached_input_microusd_per_million"])
            if raw["cached_input_microusd_per_million"] is not None
            else None
        ),
        output_microusd_per_million=int(raw["output_microusd_per_million"]),
        evidence_reference=raw["evidence_reference"],
        verified_on=date.fromisoformat(raw["verified_on"]),
        review_due_on=date.fromisoformat(raw["review_due_on"]),
    )
    price.validate(today=today)
    if price.provider != PROVIDER or price.model != MODEL:
        raise BenchmarkConfigurationError(
            "controlled pricing does not match Mistral benchmark provider/model"
        )
    return price


def projected_spend_microusd(price) -> int:
    total = 0
    for case in CASES:
        input_upper_bound = len((SYSTEM_PROMPT + _case_prompt(case)).encode("utf-8"))
        total += price.worst_case_microusd(
            input_tokens=input_upper_bound,
            output_tokens=MAX_OUTPUT_TOKENS_PER_CASE,
        )
    return total


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


def _build_provider():
    from llm.lowcost_openai_compatible import OpenAICompatibleLowCostProvider

    return OpenAICompatibleLowCostProvider(
        provider_id=PROVIDER,
        settings_prefix="MISTRAL",
        default_base_url="https://api.mistral.ai/v1",
        default_model=MODEL,
        timeout_seconds=TIMEOUT_SECONDS,
        processor_policy_key="mistral",
    )


def _invoke_case(provider, case):
    return provider.client.chat.completions.create(
        model=provider.model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _case_prompt(case)},
        ],
        max_tokens=MAX_OUTPUT_TOKENS_PER_CASE,
        timeout=provider.timeout_seconds,
        response_format=strict_response_format(),
        reasoning_effort="low",
    )


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


def _provider_error_status(exc: Exception) -> int | None:
    status = getattr(exc, "status_code", None)
    return status if isinstance(status, int) else None


def run_benchmark(*, output_path: Path, today: date) -> dict[str, Any]:
    if not os.environ.get("MISTRAL_API_KEY", "").strip():
        raise BenchmarkConfigurationError("missing MISTRAL_API_KEY benchmark credential")

    price = load_controlled_price(today=today)
    projected = projected_spend_microusd(price)
    if projected > SPEND_CEILING_MICROUSD:
        raise BenchmarkConfigurationError("projected spend exceeds explicit ceiling")

    ProviderBenchmarkPreflight(
        provider=PROVIDER,
        model=MODEL,
        modality="text",
        dataset_id=DATASET_ID,
        credential_reference="env:MISTRAL_API_KEY",
        pricing_evidence_reference=price.evidence_reference,
        network_authorized=(
            os.environ.get("MISTRAL_BENCHMARK_NETWORK_AUTHORIZED", "").lower() == "true"
        ),
        spend_ceiling_microusd=SPEND_CEILING_MICROUSD,
        patient_data=False,
    ).validate()

    provider = _build_provider()
    case_rows: list[dict[str, Any]] = []
    usage_rows: list[dict[str, int | None]] = []
    successful_latencies: list[int] = []
    list_price_equivalent_microusd = 0
    machine_passed = True

    try:
        for case in CASES:
            started = perf_counter()
            try:
                response = _invoke_case(provider, case)
                elapsed_ms = max(0, round((perf_counter() - started) * 1000))
                parsed = json.loads(response.choices[0].message.content or "")
                reply = parsed.get("reply") if isinstance(parsed, dict) else None
                usage = _usage_row(response)
                input_tokens = usage["input_tokens"]
                output_tokens = usage["output_tokens"]
                if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
                    raise BenchmarkConfigurationError("provider token counts missing")

                cost = price.worst_case_microusd(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
                list_price_equivalent_microusd += cost
                usage_rows.append(usage)
                successful_latencies.append(elapsed_ms)
                checks = machine_review(case, reply)
                passed = all(checks.values())
                machine_passed = machine_passed and passed
                case_rows.append(
                    {
                        "case_id": case.case_id,
                        "locale": case.locale,
                        "synthetic_prompt": case.text,
                        "provider_reply": reply,
                        "provider_error_type": None,
                        "provider_error_status": None,
                        "latency_ms": elapsed_ms,
                        "usage": usage,
                        "list_price_equivalent_microusd": cost,
                        "machine_checks": checks,
                        "machine_passed": passed,
                    }
                )
            except Exception as exc:
                elapsed_ms = max(0, round((perf_counter() - started) * 1000))
                machine_passed = False
                case_rows.append(
                    {
                        "case_id": case.case_id,
                        "locale": case.locale,
                        "synthetic_prompt": case.text,
                        "provider_reply": None,
                        "provider_error_type": type(exc).__name__,
                        "provider_error_status": _provider_error_status(exc),
                        "latency_ms": elapsed_ms,
                        "usage": None,
                        "list_price_equivalent_microusd": None,
                        "machine_checks": None,
                        "machine_passed": False,
                    }
                )
    finally:
        provider.client.close()

    if list_price_equivalent_microusd > SPEND_CEILING_MICROUSD:
        raise BenchmarkConfigurationError("reported usage exceeded explicit spend ceiling")

    completed_calls = len(usage_rows)
    report = {
        "provider": PROVIDER,
        "model": MODEL,
        "dataset_id": DATASET_ID,
        "run_date": today.isoformat(),
        "synthetic": True,
        "patient_data": False,
        "free_tier_account_expected": True,
        "planned_calls": len(CASES),
        "completed_calls": completed_calls,
        "failed_calls": len(CASES) - completed_calls,
        "no_retries": True,
        "structured_output_mode": "one_case_per_json_schema_call",
        "spend_ceiling_microusd": SPEND_CEILING_MICROUSD,
        "projected_max_microusd": projected,
        "list_price_equivalent_microusd_from_reported_usage": (
            list_price_equivalent_microusd
        ),
        "provider_usage": usage_rows,
        "latency": latency_summary(successful_latencies),
        "machine_gate": {
            "passed": machine_passed and completed_calls == len(CASES),
            "required_case_ids": [case.case_id for case in CASES],
        },
        "human_linguistic_review": {
            "required": True,
            "status": "pending",
            "accepted_case_ids": None,
        },
        "proof_boundaries": {
            "production_or_beta_traffic": False,
            "native_speaker_certified": False,
            "provider_billing_reconciled": False,
            "daily_free_tier_capacity_certified": False,
            "patient_egress_approved": False,
        },
        "case_results": case_rows,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_benchmark(output_path=args.output, today=date.today())
    print(
        json.dumps(
            {
                "machine_passed": report["machine_gate"]["passed"],
                "completed_calls": report["completed_calls"],
                "failed_calls": report["failed_calls"],
                "latency": report["latency"],
                "list_price_equivalent_microusd": (
                    report["list_price_equivalent_microusd_from_reported_usage"]
                ),
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["machine_gate"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
