"""Bounded FRUG-5 Groq raw-HTTP prompt-cache capability probe.

The probe uses Groq's OpenAI-compatible HTTP endpoint directly so provider-specific
usage fields are observed from raw JSON rather than inferred through an SDK model.
Only synthetic non-patient requests are sent. This does not estimate production
cache-hit rate.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import date
from pathlib import Path
from typing import Any

import requests

from companion.narrator_prompts import SYSTEM_WITH_STATE, get_language_label
from evaluation.frug5_multilingual_quality_benchmark import (
    MODEL,
    PROVIDER,
    BenchmarkConfigurationError,
    load_controlled_price,
)
from evaluation.provider_benchmark_preflight import ProviderBenchmarkPreflight

DATASET_ID = "iamina-frug5-groq-cache-probe-v2"
SPEND_CEILING_MICROUSD = 5_000
MAX_OUTPUT_TOKENS = 64
_PROBE_CALLS = 3
_MAX_OBSERVED_PROMPT_TOKENS_PER_CALL = 2_200
_GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


def shared_prefix() -> str:
    base = SYSTEM_WITH_STATE.format(
        language=get_language_label("en"),
        tone="warm",
        state="[SYNTHETIC_CACHE_PROBE]\nNo approved clinical facts.",
    )
    # Prior live run measured ~1.5k prompt tokens at this padding size, above
    # Groq's documented maximum minimum-cacheable threshold (1024 tokens).
    neutral_padding = " ".join(["neutral"] * 1_100)
    return f"{base}\n[SYNTHETIC_STATIC_CONTEXT]\n{neutral_padding}"


def request_body() -> dict[str, Any]:
    return {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": shared_prefix()},
            {
                "role": "user",
                "content": "Synthetic cache probe. Reply briefly.",
            },
        ],
        "max_tokens": MAX_OUTPUT_TOKENS,
        "reasoning_effort": "low",
    }


def projected_spend_microusd(price) -> int:
    input_upper_bound = len(shared_prefix().encode("utf-8")) + 128
    return _PROBE_CALLS * price.worst_case_microusd(
        input_tokens=input_upper_bound,
        output_tokens=MAX_OUTPUT_TOKENS,
    )


def usage_cache_row(raw: dict[str, Any]) -> dict[str, int | float | bool | None]:
    usage = raw.get("usage")
    if not isinstance(usage, dict):
        raise BenchmarkConfigurationError("provider usage evidence missing")

    prompt_tokens = usage.get("prompt_tokens")
    output_tokens = usage.get("completion_tokens")
    total_tokens = usage.get("total_tokens")
    if not isinstance(prompt_tokens, int) or prompt_tokens <= 0:
        raise BenchmarkConfigurationError("provider prompt token count missing")
    if not isinstance(output_tokens, int) or output_tokens < 0:
        raise BenchmarkConfigurationError("provider completion token count missing")
    if not isinstance(total_tokens, int) or total_tokens < prompt_tokens:
        raise BenchmarkConfigurationError("provider total token count missing")

    details = usage.get("prompt_tokens_details")
    field_present = isinstance(details, dict) and "cached_tokens" in details
    cached = details.get("cached_tokens") if isinstance(details, dict) else None
    if cached is not None and not isinstance(cached, int):
        raise BenchmarkConfigurationError("provider cached token field is non-numeric")
    if isinstance(cached, int) and (cached < 0 or cached > prompt_tokens):
        raise BenchmarkConfigurationError("provider cached token count is invalid")

    ratio = cached / prompt_tokens if isinstance(cached, int) else None
    return {
        "input_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "cached_field_present": field_present,
        "cached_input_tokens": cached,
        "total_tokens": total_tokens,
        "cache_ratio": ratio,
    }


def _invoke_raw(api_key: str) -> dict[str, Any]:
    response = requests.post(
        _GROQ_CHAT_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=request_body(),
        timeout=30,
    )
    if response.status_code >= 400:
        raise BenchmarkConfigurationError(
            f"Groq cache probe HTTP {response.status_code}"
        )
    raw = response.json()
    if not isinstance(raw, dict):
        raise BenchmarkConfigurationError("Groq cache probe returned non-object JSON")
    return raw


def run_probe(*, output_path: Path, today: date) -> dict[str, Any]:
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise BenchmarkConfigurationError("missing GROQ_API_KEY benchmark credential")

    price = load_controlled_price(today=today)
    projected = projected_spend_microusd(price)
    if projected > SPEND_CEILING_MICROUSD:
        raise BenchmarkConfigurationError("projected spend exceeds explicit ceiling")

    ProviderBenchmarkPreflight(
        provider=PROVIDER,
        model=MODEL,
        modality="text",
        dataset_id=DATASET_ID,
        credential_reference="env:GROQ_API_KEY",
        pricing_evidence_reference=price.evidence_reference,
        network_authorized=os.environ.get("FRUG5_CACHE_NETWORK_AUTHORIZED", "").lower()
        == "true",
        spend_ceiling_microusd=SPEND_CEILING_MICROUSD,
        patient_data=False,
    ).validate()

    rows: list[dict[str, int | float | bool | None]] = []
    for index in range(_PROBE_CALLS):
        raw = _invoke_raw(api_key)
        row = usage_cache_row(raw)
        if row["input_tokens"] > _MAX_OBSERVED_PROMPT_TOKENS_PER_CALL:
            raise BenchmarkConfigurationError(
                "prompt token count exceeded bounded cache-probe TPM guard"
            )
        row["call_index"] = index + 1
        rows.append(row)

    subsequent = rows[1:]
    measurable = any(
        bool(row["cached_field_present"])
        and isinstance(row["cached_input_tokens"], int)
        for row in subsequent
    )
    hit_rows = [
        row
        for row in subsequent
        if isinstance(row["cached_input_tokens"], int)
        and row["cached_input_tokens"] > 0
    ]

    report = {
        "provider": PROVIDER,
        "model": MODEL,
        "dataset_id": DATASET_ID,
        "run_date": today.isoformat(),
        "synthetic": True,
        "patient_data": False,
        "production_cache_rate_claim": False,
        "transport": "raw_https_json",
        "planned_calls": _PROBE_CALLS,
        "completed_calls": len(rows),
        "spend_ceiling_microusd": SPEND_CEILING_MICROUSD,
        "projected_max_microusd": projected,
        "provider_usage": rows,
        "cache_measurement": {
            "measurable": measurable,
            "cache_hit_observed": bool(hit_rows),
            "subsequent_cached_token_values": [
                row["cached_input_tokens"] for row in subsequent
            ],
            "subsequent_cache_ratios": [row["cache_ratio"] for row in subsequent],
            "field_presence": [row["cached_field_present"] for row in subsequent],
        },
        "proof_boundaries": {
            "production_cache_rate": False,
            "provider_billing_reconciled": False,
            "patient_data": False,
        },
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
    report = run_probe(output_path=args.output, today=date.today())
    print(json.dumps(report["cache_measurement"]))
    return 0 if report["cache_measurement"]["measurable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
