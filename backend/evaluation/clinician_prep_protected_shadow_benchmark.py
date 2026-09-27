"""Synthetic protected-body benchmark for CLINICIAN_PREP native wrappers.

One provider call generates six non-clinical wrappers around opaque body tokens.
No patient data is used and the deterministic clinical bodies never leave IAmina.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from companion.narration_envelope import (
    build_shadow_envelope,
    verify_and_reinject_protected_narration,
)
from core.contracts.truth import TruthKind
from diabetes.services.clinical.clinician_prep_decision import (
    resolve_clinician_prep_from_brief,
)
from diabetes.services.clinical.clinician_prep_protected_narration_verifier import (
    verify_clinician_prep_protected_narration,
)
from diabetes.services.clinical.consultation_brief_contract import (
    ConsultationBriefEnvelope,
    ConsultationComparisonBasis,
    ConsultationEvidenceItem,
    ConsultationNextStep,
)
from evaluation.native_voice_live_benchmark import (
    MODEL,
    PROVIDER,
    load_native_voice_price,
)
from evaluation.native_voice_shadow_benchmark import SCENARIOS
from evaluation.provider_benchmark_preflight import ProviderBenchmarkPreflight

DATASET_ID = "iamina-clinician-prep-protected-shadow-v1"
SPEND_CEILING_MICROUSD = 5_000  # additional hard ceiling = USD 0.005
MAX_OUTPUT_TOKENS = 480
_SCENARIO_IDS = (
    "darija_arabic",
    "saudi",
    "emirati",
    "kuwaiti",
    "qatari",
    "omani",
)
_ARABIC = re.compile(r"[\u0600-\u06ff]")

SYSTEM_PROMPT = (
    "You are a language-only wrapper generator. "
    "Each item contains an opaque protected_body_token. You do not know its content. "
    "Return one short natural NON-CLINICAL relational wrapper for each item and include "
    "that exact token exactly once and unchanged. Do not mention health, medicine, "
    "doctor, glucose, diabetes, insulin, dose, treatment, symptoms, urgency, or any "
    "clinical concept. Do not add numbers, facts, advice, questions, or actions. "
    "Use the requested locale and script. Avoid forced dialect markers. "
    "Keep text outside the token very short. Return only the required JSON object."
)


def _selected_scenarios():
    by_id = {scenario.scenario_id: scenario for scenario in SCENARIOS}
    selected = tuple(by_id[item] for item in _SCENARIO_IDS)
    if any(s.script != "arabic" for s in selected):
        raise RuntimeError("protected shadow v1 supports Arabic-script scenarios only")
    return selected


def _synthetic_brief() -> ConsultationBriefEnvelope:
    end = datetime(2026, 9, 27, 12, 0, tzinfo=UTC)
    return ConsultationBriefEnvelope(
        window_start=end - timedelta(days=14),
        window_end=end,
        comparison_basis=ConsultationComparisonBasis.CURRENT_SNAPSHOT,
        items=(
            ConsultationEvidenceItem(
                key="recorded_glucose.latest_mg_dl",
                value=142.0,
                unit="mg/dL",
                truth_kind=TruthKind.OBSERVED_FACT,
                source="synthetic-benchmark",
                source_version="protected-shadow.v1",
                allowed_next_step=ConsultationNextStep.MONITOR,
            ),
        ),
    )


def _clinician_turn(scenario):
    for turn in scenario.turns:
        if turn.turn_id == "clinician_prep":
            return turn
    raise RuntimeError(f"scenario {scenario.scenario_id} lacks clinician_prep turn")


def _cases() -> tuple[dict[str, object], ...]:
    brief = _synthetic_brief()
    cases: list[dict[str, object]] = []
    for scenario in _selected_scenarios():
        turn = _clinician_turn(scenario)
        resolution = resolve_clinician_prep_from_brief(
            turn.user,
            brief,
            language=scenario.locale,
        )
        if resolution is None:
            raise RuntimeError(
                f"clinician prep resolution missing for {scenario.scenario_id}"
            )
        envelope = build_shadow_envelope(
            resolution,
            language=scenario.locale,
            prefer_latin_script=False,
        )
        cases.append(
            {
                "scenario": scenario,
                "turn": turn,
                "resolution": resolution,
                "envelope": envelope,
            }
        )
    return tuple(cases)


def _provider_prompt(cases: tuple[dict[str, object], ...]) -> str:
    rows = []
    for case in cases:
        scenario = case["scenario"]
        turn = case["turn"]
        envelope = case["envelope"]
        rows.append(
            {
                "scenario_id": scenario.scenario_id,
                "locale": scenario.locale,
                "script": scenario.script,
                "synthetic_user_message": turn.user,
                "protected_body_token": envelope.protected_body_token,
                "wrapper_constraints": {
                    "non_clinical_only": True,
                    "no_numbers": True,
                    "no_new_facts": True,
                    "no_new_actions": True,
                    "token_exactly_once": True,
                },
            }
        )
    return json.dumps(
        {"cases": rows},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def strict_response_format() -> dict[str, Any]:
    ids = list(_SCENARIO_IDS)
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "clinician_prep_protected_wrappers",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "replies": {
                        "type": "array",
                        "minItems": len(ids),
                        "maxItems": len(ids),
                        "items": {
                            "type": "object",
                            "properties": {
                                "scenario_id": {
                                    "type": "string",
                                    "enum": ids,
                                },
                                "reply": {"type": "string"},
                            },
                            "required": ["scenario_id", "reply"],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["replies"],
                "additionalProperties": False,
            },
        },
    }


def _normalize_replies(parsed: object) -> dict[str, str]:
    if not isinstance(parsed, dict) or not isinstance(parsed.get("replies"), list):
        raise RuntimeError("invalid provider structured output")
    rows = parsed["replies"]
    if len(rows) != len(_SCENARIO_IDS):
        raise RuntimeError("provider returned wrong wrapper count")

    result: dict[str, str] = {}
    for expected_id, row in zip(_SCENARIO_IDS, rows, strict=True):
        if not isinstance(row, dict):
            raise RuntimeError("invalid provider wrapper row")
        if row.get("scenario_id") != expected_id:
            raise RuntimeError("provider wrapper order mismatch")
        reply = row.get("reply")
        if not isinstance(reply, str):
            raise RuntimeError("provider wrapper must be text")
        result[expected_id] = reply
    return result


def _wrapper_text(provider_reply: str, token: str) -> str:
    return " ".join(provider_reply.replace(token, "", 1).split()).strip()


def _script_ok(wrapper: str) -> bool:
    return bool(wrapper) and bool(_ARABIC.search(wrapper))


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


def projected_spend_microusd(price) -> int:
    cases = _cases()
    prompt = _provider_prompt(cases)
    return price.worst_case_microusd(
        input_tokens=len((SYSTEM_PROMPT + prompt).encode("utf-8")),
        output_tokens=MAX_OUTPUT_TOKENS,
    )


def run_benchmark(*, output_path: Path, today: date) -> dict[str, Any]:
    if not os.environ.get("GROQ_API_KEY", "").strip():
        raise RuntimeError("missing GROQ_API_KEY benchmark credential")

    cases = _cases()
    prompt = _provider_prompt(cases)
    price = load_native_voice_price(today=today)
    projected = price.worst_case_microusd(
        input_tokens=len((SYSTEM_PROMPT + prompt).encode("utf-8")),
        output_tokens=MAX_OUTPUT_TOKENS,
    )
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
    try:
        response = provider.client.chat.completions.create(
            model=provider.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=MAX_OUTPUT_TOKENS,
            timeout=provider.timeout_seconds,
            response_format=strict_response_format(),
            reasoning_effort="low",
        )
        parsed = json.loads(response.choices[0].message.content or "")
        replies = _normalize_replies(parsed)
        usage = _usage_row(response)
    finally:
        provider.client.close()

    input_tokens = usage["input_tokens"]
    output_tokens = usage["output_tokens"]
    if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
        raise RuntimeError("provider token counts missing")
    actual_cost = price.worst_case_microusd(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    if actual_cost > SPEND_CEILING_MICROUSD:
        raise RuntimeError("reported usage cost exceeded hard ceiling")

    results: list[dict[str, object]] = []
    machine_passed = True
    for case in cases:
        scenario = case["scenario"]
        resolution = case["resolution"]
        envelope = case["envelope"]
        provider_reply = replies[scenario.scenario_id]
        wrapper = _wrapper_text(provider_reply, envelope.protected_body_token)

        try:
            final_reply = verify_and_reinject_protected_narration(
                provider_reply,
                envelope,
            )
            family_check = verify_clinician_prep_protected_narration(
                resolution.decision,
                final_reply,
                resolution.reply,
            )
            token_count_ok = provider_reply.count(envelope.protected_body_token) == 1
            body_hidden = resolution.reply not in provider_reply
            wrapper_script_ok = _script_ok(wrapper)
            passed = (
                family_check.passed
                and token_count_ok
                and body_hidden
                and wrapper_script_ok
            )
            violations = family_check.violations
        except Exception as exc:
            final_reply = resolution.reply
            token_count_ok = False
            body_hidden = resolution.reply not in provider_reply
            wrapper_script_ok = _script_ok(wrapper)
            passed = False
            violations = (type(exc).__name__,)

        machine_passed = machine_passed and passed
        results.append(
            {
                "scenario_id": scenario.scenario_id,
                "locale": scenario.locale,
                "script": scenario.script,
                "synthetic_user": case["turn"].user,
                "provider_reply": provider_reply,
                "wrapper": wrapper,
                "deterministic_body_sha256": __import__("hashlib").sha256(
                    resolution.reply.encode("utf-8")
                ).hexdigest(),
                "token_count_ok": token_count_ok,
                "body_hidden_from_provider_reply": body_hidden,
                "wrapper_script_ok": wrapper_script_ok,
                "family_verifier_passed": passed,
                "violations": list(violations),
                "final_reply": final_reply,
            }
        )

    report = {
        "provider": PROVIDER,
        "model": MODEL,
        "dataset_id": DATASET_ID,
        "run_date": today.isoformat(),
        "synthetic": True,
        "patient_data": False,
        "production_traffic": False,
        "strategy": "one_batched_provider_call_for_six_protected_wrappers",
        "planned_calls": 1,
        "completed_calls": 1,
        "scenario_ids": list(_SCENARIO_IDS),
        "excluded_scenarios": {
            "darija_arabizi": (
                "current deterministic CLINICIAN_PREP body is Arabic-script; "
                "protected-body v1 refuses cross-script substitution"
            )
        },
        "spend_ceiling_microusd": SPEND_CEILING_MICROUSD,
        "projected_max_microusd": projected,
        "actual_cost_microusd_worst_case_from_reported_usage": actual_cost,
        "machine_gate": {
            "passed": machine_passed and len(results) == len(_SCENARIO_IDS),
            "evaluated_rows": len(results),
        },
        "proof_boundaries": {
            "patient_egress_authorized": False,
            "runtime_activation": False,
            "clinical_authority_changed": False,
            "native_human_certification": False,
        },
        "results": results,
        "provider_usage": [usage],
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
                "evaluated_rows": report["machine_gate"]["evaluated_rows"],
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
