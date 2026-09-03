"""FRUG-5 live Gulf sample using the real Companion narrator prompt surface."""
from __future__ import annotations

import argparse
import json
import os
from datetime import date
from pathlib import Path
from typing import Any

from companion.narrator_prompts import EMOTIONAL_USER, SYSTEM_WITH_STATE, get_language_label
from evaluation.frug5_multilingual_quality_benchmark import (
    CASES,
    MODEL,
    PROVIDER,
    SPEND_CEILING_MICROUSD,
    BenchmarkConfigurationError,
    _usage_row,
    load_controlled_price,
    machine_review,
    strict_response_format,
)
from evaluation.provider_benchmark_preflight import ProviderBenchmarkPreflight
from llm.lowcost_openai_compatible import _GPT_OSS_MAX_OUTPUT_TOKENS

DATASET_ID = "iamina-frug5-product-prompt-gulf-v1"
_GULF_LOCALES = {
    "saudi": "ar-SA",
    "emirati": "ar-AE",
    "kuwaiti": "ar-KW",
    "qatari": "ar-QA",
    "omani": "ar-OM",
}
_GULF_CASES = tuple(case for case in CASES if case.case_id in _GULF_LOCALES)


def _system_prompt(case_id: str) -> str:
    locale_code = _GULF_LOCALES[case_id]
    return SYSTEM_WITH_STATE.format(
        language=get_language_label(locale_code),
        tone="warm",
        state="[SYNTHETIC_EVAL_STATE]\nNo approved clinical facts.",
    )


def _user_prompt(case) -> str:
    """Mirror runtime routing for the benchmark's supportive/emotional scenarios."""
    return EMOTIONAL_USER.format(
        memory="Aucune donnée relationnelle mémorisée.",
        history="",
        message=case.text,
    )


def _gpt_oss_request_tuning() -> dict[str, Any]:
    """Mirror the production Groq GPT-OSS non-streaming transport exactly."""
    return {
        "max_completion_tokens": _GPT_OSS_MAX_OUTPUT_TOKENS,
        "response_format": strict_response_format(),
        "reasoning_effort": "low",
        "extra_body": {"reasoning_format": "hidden"},
    }


def projected_spend_microusd(price) -> int:
    total = 0
    for case in _GULF_CASES:
        payload = _system_prompt(case.case_id) + _user_prompt(case)
        total += price.worst_case_microusd(
            input_tokens=len(payload.encode("utf-8")),
            output_tokens=_GPT_OSS_MAX_OUTPUT_TOKENS,
        )
    return total


def _invoke_case(provider, case):
    return provider.client.chat.completions.create(
        model=provider.model,
        messages=[
            {"role": "system", "content": _system_prompt(case.case_id)},
            {"role": "user", "content": _user_prompt(case)},
        ],
        timeout=provider.timeout_seconds,
        **_gpt_oss_request_tuning(),
    )


def run_benchmark(*, output_path: Path, today: date) -> dict[str, Any]:
    if not os.environ.get("GROQ_API_KEY", "").strip():
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
        network_authorized=os.environ.get("FRUG5_PRODUCT_PROMPT_NETWORK_AUTHORIZED", "").lower()
        == "true",
        spend_ceiling_microusd=SPEND_CEILING_MICROUSD,
        patient_data=False,
    ).validate()

    from llm.provider_registry import build_openai_compatible_provider

    provider = build_openai_compatible_provider(PROVIDER, model=MODEL)
    rows: list[dict[str, Any]] = []
    usage_rows: list[dict[str, int | None]] = []
    actual_cost = 0
    machine_passed = True
    try:
        for case in _GULF_CASES:
            try:
                response = _invoke_case(provider, case)
                parsed = json.loads(response.choices[0].message.content or "")
                reply = parsed.get("reply") if isinstance(parsed, dict) else None
                usage = _usage_row(response)
                input_tokens = usage["input_tokens"]
                output_tokens = usage["output_tokens"]
                if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
                    raise BenchmarkConfigurationError("provider token counts missing")
                actual_cost += price.worst_case_microusd(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
                usage_rows.append(usage)
                checks = machine_review(case, reply)
                passed = all(checks.values())
                machine_passed = machine_passed and passed
                rows.append(
                    {
                        "case_id": case.case_id,
                        "locale_code": _GULF_LOCALES[case.case_id],
                        "product_language_label": get_language_label(
                            _GULF_LOCALES[case.case_id]
                        ),
                        "provider_reply": reply,
                        "machine_checks": checks,
                        "machine_passed": passed,
                    }
                )
            except Exception as exc:
                machine_passed = False
                rows.append(
                    {
                        "case_id": case.case_id,
                        "locale_code": _GULF_LOCALES[case.case_id],
                        "provider_reply": None,
                        "provider_error_type": type(exc).__name__,
                        "machine_passed": False,
                    }
                )
                break
    finally:
        provider.client.close()

    report = {
        "provider": PROVIDER,
        "model": MODEL,
        "dataset_id": DATASET_ID,
        "run_date": today.isoformat(),
        "synthetic": True,
        "patient_data": False,
        "product_prompt_surface": True,
        "planned_calls": len(_GULF_CASES),
        "completed_calls": len(usage_rows),
        "actual_cost_microusd_worst_case_from_reported_usage": actual_cost,
        "provider_usage": usage_rows,
        "machine_gate": {
            "passed": machine_passed and len(rows) == len(_GULF_CASES),
            "required_case_ids": [case.case_id for case in _GULF_CASES],
        },
        "human_linguistic_review": {
            "required": True,
            "status": "pending",
            "accepted_case_ids": None,
            "cost_per_accepted_safe_answer_microusd": None,
        },
        "case_results": rows,
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
                "actual_cost_microusd": report[
                    "actual_cost_microusd_worst_case_from_reported_usage"
                ],
            }
        )
    )
    return 0 if report["machine_gate"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
