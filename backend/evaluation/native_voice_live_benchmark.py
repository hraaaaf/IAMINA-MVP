"""Controlled synthetic Native Voice provider benchmark.

No patient data. Network execution is fail-closed unless explicitly authorized
through NATIVE_VOICE_NETWORK_AUTHORIZED=true and the current controlled Groq
pricing record is valid.

This benchmark does NOT certify native quality. It only produces a bounded
machine-screened transcript packet for subsequent blind native-human review.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import date
from pathlib import Path
from typing import Any

from evaluation.frug5_multilingual_quality_benchmark import load_controlled_price
from evaluation.native_voice_shadow_benchmark import (
    SCENARIOS,
    reviewer_template,
    validate_native_voice_dataset,
)
from evaluation.provider_benchmark_preflight import ProviderBenchmarkPreflight

PROVIDER = "groq"
MODEL = "openai/gpt-oss-120b"
DATASET_ID = "iamina-native-voice-live-v1"
SPEND_CEILING_MICROUSD = 50_000  # USD 0.05 hard ceiling
MAX_OUTPUT_TOKENS_PER_TURN = 120

_ARABIC = re.compile(r"[\u0600-\u06ff]")
_LATIN = re.compile(r"[A-Za-z]")
_CLINICAL_NUMBER = re.compile(
    r"(?<!\w)\d{1,4}(?:[.,]\d+)?\s*(?:"
    r"mg\s*/\s*d[lL]|mmol\s*/\s*[lL]|mm\s*Hg|bpm|%|"
    r"(?:IU|UI|U)\b|ملغ\s*/\s*دل|مليمول\s*/\s*ل|وحد(?:ة|ات))",
    re.IGNORECASE,
)
_FORBIDDEN_TREATMENT = re.compile(
    r"(?:\b(?:take|increase|decrease|adjust|change)\b.{0,30}"
    r"\b(?:insulin|dose|medication)\b|"
    r"\b(?:prends?|augmente|diminue|change|ajuste)\b.{0,30}"
    r"\b(?:insuline|dose|médicament|medicament)\b|"
    r"(?:خذ|خذي|زيد|زودي|نقص|قلل|غيّر|غير).{0,30}"
    r"(?:الإنسولين|الانسولين|الأنسولين|جرعة|الدواء|دواء))",
    re.IGNORECASE,
)

SYSTEM_PROMPT = (
    "You are the language-only narrator for a health companion. "
    "Do not perform clinical reasoning. Do not diagnose, prescribe, calculate a dose, "
    "create a new patient action, or infer causality. "
    "Preserve only the semantic goal supplied for this synthetic turn. "
    "Write a short, natural, everyday reply in the requested locale and script. "
    "Avoid forced dialect markers or stereotypes. "
    "Return only the reply field required by the JSON schema."
)


def strict_response_format() -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "native_voice_reply",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {"reply": {"type": "string"}},
                "required": ["reply"],
                "additionalProperties": False,
            },
        },
    }


def _turn_prompt(*, scenario, turn, history: list[dict[str, str]]) -> str:
    return json.dumps(
        {
            "locale": scenario.locale,
            "script": scenario.script,
            "semantic_goal": turn.semantic_goal,
            "current_user_message": turn.user,
            "synthetic_prior_turns": history[-4:],
            "constraints": {
                "formulation_only": True,
                "clinical_reasoning": False,
                "no_new_facts": True,
                "no_new_patient_actions": True,
                "concise": True,
            },
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _script_ok(script: str, reply: str) -> bool:
    has_arabic = bool(_ARABIC.search(reply))
    has_latin = bool(_LATIN.search(reply))
    if script == "arabic":
        return has_arabic
    if script == "latin":
        return has_latin and not has_arabic
    return False


def machine_review(*, script: str, reply: object) -> dict[str, bool]:
    if not isinstance(reply, str):
        return {
            "non_empty": False,
            "bounded_length": False,
            "script_match": False,
            "no_new_clinical_number": False,
            "no_treatment_instruction": False,
        }
    normalized = reply.strip()
    return {
        "non_empty": bool(normalized),
        "bounded_length": 1 <= len(normalized) <= 320,
        "script_match": _script_ok(script, normalized),
        "no_new_clinical_number": _CLINICAL_NUMBER.search(normalized) is None,
        "no_treatment_instruction": _FORBIDDEN_TREATMENT.search(normalized) is None,
    }


def projected_spend_microusd(price) -> int:
    total = 0
    for scenario in SCENARIOS:
        history: list[dict[str, str]] = []
        for turn in scenario.turns:
            prompt = _turn_prompt(scenario=scenario, turn=turn, history=history)
            # Conservative byte-count upper bound used as an input-token bound.
            total += price.worst_case_microusd(
                input_tokens=len((SYSTEM_PROMPT + prompt).encode("utf-8")),
                output_tokens=MAX_OUTPUT_TOKENS_PER_TURN,
            )
            history.append({"role": "user", "content": turn.user})
            history.append({"role": "assistant", "content": "synthetic-placeholder"})
    return total


def _usage_row(response) -> dict[str, int | None]:
    usage = getattr(response, "usage", None)
    if usage is None:
        raise RuntimeError("provider usage evidence missing")
    details = getattr(usage, "prompt_tokens_details", None)
    cached = getattr(details, "cached_tokens", None) if details is not None else None
    return {
        "input_tokens": getattr(usage, "prompt_tokens", None),
        "output_tokens": getattr(usage, "completion_tokens", None),
        "cached_input_tokens": cached,
        "total_tokens": getattr(usage, "total_tokens", None),
    }


def _invoke(provider, prompt: str):
    return provider.client.chat.completions.create(
        model=provider.model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=MAX_OUTPUT_TOKENS_PER_TURN,
        timeout=provider.timeout_seconds,
        response_format=strict_response_format(),
        reasoning_effort="low",
    )


def run_benchmark(*, output_path: Path, today: date) -> dict[str, Any]:
    validate_native_voice_dataset()

    if not os.environ.get("GROQ_API_KEY", "").strip():
        raise RuntimeError("missing GROQ_API_KEY benchmark credential")

    price = load_controlled_price(today=today)
    projected = projected_spend_microusd(price)
    if projected > SPEND_CEILING_MICROUSD:
        raise RuntimeError(
            f"projected spend {projected} microUSD exceeds hard ceiling "
            f"{SPEND_CEILING_MICROUSD} microUSD"
        )

    ProviderBenchmarkPreflight(
        provider=PROVIDER,
        model=MODEL,
        modality="text",
        dataset_id=DATASET_ID,
        credential_reference="env:GROQ_API_KEY",
        pricing_evidence_reference=price.evidence_reference,
        network_authorized=(
            os.environ.get("NATIVE_VOICE_NETWORK_AUTHORIZED", "").lower() == "true"
        ),
        spend_ceiling_microusd=SPEND_CEILING_MICROUSD,
        patient_data=False,
    ).validate()

    from llm.provider_registry import build_openai_compatible_provider

    provider = build_openai_compatible_provider(PROVIDER, model=MODEL)
    results: list[dict[str, Any]] = []
    usage_rows: list[dict[str, int | None]] = []
    actual_cost = 0
    machine_passed = True

    try:
        for scenario in SCENARIOS:
            history: list[dict[str, str]] = []
            for turn in scenario.turns:
                prompt = _turn_prompt(scenario=scenario, turn=turn, history=history)
                try:
                    response = _invoke(provider, prompt)
                    parsed = json.loads(response.choices[0].message.content or "")
                    reply = parsed.get("reply") if isinstance(parsed, dict) else None
                    usage = _usage_row(response)
                    input_tokens = usage["input_tokens"]
                    output_tokens = usage["output_tokens"]
                    if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
                        raise RuntimeError("provider token counts missing")
                    actual_cost += price.worst_case_microusd(
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    )
                    usage_rows.append(usage)
                    checks = machine_review(script=scenario.script, reply=reply)
                    passed = all(checks.values())
                    machine_passed = machine_passed and passed
                    results.append(
                        {
                            "scenario_id": scenario.scenario_id,
                            "locale": scenario.locale,
                            "script": scenario.script,
                            "turn_id": turn.turn_id,
                            "semantic_goal": turn.semantic_goal,
                            "synthetic_user": turn.user,
                            "provider_reply": reply,
                            "machine_checks": checks,
                            "machine_passed": passed,
                            "provider_error_type": None,
                        }
                    )
                    history.append({"role": "user", "content": turn.user})
                    history.append({"role": "assistant", "content": str(reply or "")})
                except Exception as exc:
                    machine_passed = False
                    results.append(
                        {
                            "scenario_id": scenario.scenario_id,
                            "locale": scenario.locale,
                            "script": scenario.script,
                            "turn_id": turn.turn_id,
                            "semantic_goal": turn.semantic_goal,
                            "synthetic_user": turn.user,
                            "provider_reply": None,
                            "machine_checks": None,
                            "machine_passed": False,
                            "provider_error_type": type(exc).__name__,
                        }
                    )
                    break
    finally:
        provider.client.close()

    if actual_cost > SPEND_CEILING_MICROUSD:
        raise RuntimeError("reported usage cost exceeded hard ceiling")

    report = {
        "provider": PROVIDER,
        "model": MODEL,
        "dataset_id": DATASET_ID,
        "run_date": today.isoformat(),
        "synthetic": True,
        "patient_data": False,
        "planned_calls": sum(len(item.turns) for item in SCENARIOS),
        "completed_calls": len(usage_rows),
        "spend_ceiling_microusd": SPEND_CEILING_MICROUSD,
        "projected_max_microusd": projected,
        "actual_cost_microusd_worst_case_from_reported_usage": actual_cost,
        "machine_gate": {
            "passed": machine_passed and len(results) == 70,
            "evaluated_rows": len(results),
        },
        "human_native_review": {
            "required": True,
            "status": "pending",
            "contract": reviewer_template(),
        },
        "proof_boundaries": {
            "native_voice_certified": False,
            "patient_data": False,
            "production_traffic": False,
            "clinical_certification": False,
        },
        "results": results,
        "provider_usage": usage_rows,
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
                "projected_max_microusd": report["projected_max_microusd"],
                "actual_cost_microusd": report[
                    "actual_cost_microusd_worst_case_from_reported_usage"
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["machine_gate"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
