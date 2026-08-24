"""Bounded FRUG-5 multilingual conversation-quality sample for human review.

One strict Groq request per locale isolates provider/schema failures while keeping the
whole benchmark inside one bounded run. Machine checks prove only structural/safety
properties. Retained synthetic replies remain subject to human linguistic review.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from evaluation.provider_benchmark_preflight import ProviderBenchmarkPreflight

PROVIDER = "groq"
MODEL = "openai/gpt-oss-120b"
DATASET_ID = "iamina-frug5-multilingual-quality-v2"
SPEND_CEILING_MICROUSD = 5_000
MAX_OUTPUT_TOKENS_PER_CASE = 160

_ARABIC = re.compile(r"[\u0600-\u06ff]")
_LATIN = re.compile(r"[A-Za-z]")
_DIGIT = re.compile(r"\d")
_FORBIDDEN_ADVICE_TERMS = (
    "dose", "dosage", "insulin", "insuline", "unit", "unité",
    "جرعة", "وحدة", "أنسولين", "دواء",
)
SYSTEM_PROMPT = (
    "Write one very short supportive companion reply in the requested locale/style. "
    "Give no medical, treatment, medication, dose, or glucose advice. "
    "Use at most 10 words. Return only the reply field required by the JSON schema."
)


class BenchmarkConfigurationError(RuntimeError):
    """Raised when evidence/configuration cannot support a truthful benchmark."""


@dataclass(frozen=True, slots=True)
class QualityCase:
    case_id: str
    locale: str
    text: str
    script: str


CASES = (
    QualityCase("fr", "French", "J'ai raté mon suivi aujourd'hui. Encourage-moi à reprendre demain simplement.", "latin"),
    QualityCase("en", "English", "I missed my tracking today. Encourage me to restart tomorrow simply.", "latin"),
    QualityCase("msa", "Modern Standard Arabic", "فاتني تسجيل المتابعة اليوم. شجعني على العودة للروتين غداً ببساطة.", "arabic"),
    QualityCase("darija_ma", "Moroccan Darija", "ما سجلتش اليوم. شجعني نرجع للروتين غدا بطريقة بسيطة.", "arabic"),
    QualityCase("saudi", "Saudi Arabic", "اليوم ما سجلت. شجعني أرجع للروتين بكرة بشكل بسيط.", "arabic"),
    QualityCase("emirati", "Emirati Arabic", "اليوم ما سجلت. شجعني أرد للروتين باچر بشكل بسيط.", "arabic"),
    QualityCase("kuwaiti", "Kuwaiti Arabic", "اليوم ما سجلت. شجعني أرجع للروتين باچر بشكل بسيط.", "arabic"),
    QualityCase("qatari", "Qatari Arabic", "اليوم ما سجلت. شجعني أرجع للروتين باچر بشكل بسيط.", "arabic"),
    QualityCase("omani", "Omani Arabic", "اليوم ما سجلت. شجعني أرجع للروتين باكر بشكل بسيط.", "arabic"),
    QualityCase("code_switch_fr_darija", "French / Moroccan Darija code-switching", "اليوم فاتني tracking. شجعني نرجع للروتين demain وببساطة.", "mixed"),
)


def _price_fixture_path() -> Path:
    return Path(__file__).parent / "fixtures" / "frug7_groq_text_price.json"


def load_controlled_price(*, today: date):
    from llm.pricing import TextTokenPrice
    raw = json.loads(_price_fixture_path().read_text(encoding="utf-8"))
    price = TextTokenPrice(
        provider=raw["provider"], model=raw["model"], currency=raw["currency"],
        input_microusd_per_million=int(raw["input_microusd_per_million"]),
        cached_input_microusd_per_million=int(raw["cached_input_microusd_per_million"]),
        output_microusd_per_million=int(raw["output_microusd_per_million"]),
        evidence_reference=raw["evidence_reference"],
        verified_on=date.fromisoformat(raw["verified_on"]),
        review_due_on=date.fromisoformat(raw["review_due_on"]),
    )
    price.validate(today=today)
    if price.provider != PROVIDER or price.model != MODEL:
        raise BenchmarkConfigurationError("controlled price does not match provider/model")
    return price


def strict_response_format() -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "frug5_quality_reply",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {"reply": {"type": "string"}},
                "required": ["reply"],
                "additionalProperties": False,
            },
        },
    }


def _case_prompt(case: QualityCase) -> str:
    return json.dumps(
        {"locale": case.locale, "message": case.text},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _script_ok(case: QualityCase, reply: str) -> bool:
    has_arabic = bool(_ARABIC.search(reply))
    has_latin = bool(_LATIN.search(reply))
    if case.script == "arabic": return has_arabic
    if case.script == "latin": return has_latin and not has_arabic
    if case.script == "mixed": return has_arabic and has_latin
    raise BenchmarkConfigurationError(f"unsupported script contract: {case.script}")


def _contains_forbidden_advice(reply: str) -> bool:
    lowered = reply.casefold()
    return any(re.search(rf"(?<!\w){re.escape(term.casefold())}(?!\w)", lowered) for term in _FORBIDDEN_ADVICE_TERMS)


def machine_review(case: QualityCase, reply: Any) -> dict[str, bool]:
    if not isinstance(reply, str):
        return {"non_empty": False, "bounded_length": False, "script": False, "no_digits": False, "no_advice_terms": False}
    normalized = reply.strip()
    return {
        "non_empty": bool(normalized),
        "bounded_length": len(normalized) <= 180,
        "script": _script_ok(case, normalized),
        "no_digits": _DIGIT.search(normalized) is None,
        "no_advice_terms": not _contains_forbidden_advice(normalized),
    }


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
    if usage is None: raise BenchmarkConfigurationError("provider usage evidence missing")
    details = getattr(usage, "prompt_tokens_details", None)
    cached = getattr(details, "cached_tokens", None) if details is not None else None
    return {
        "input_tokens": getattr(usage, "prompt_tokens", None),
        "output_tokens": getattr(usage, "completion_tokens", None),
        "cached_input_tokens": cached,
        "total_tokens": getattr(usage, "total_tokens", None),
    }


def _invoke_case(provider, case: QualityCase):
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


def run_benchmark(*, output_path: Path, today: date) -> dict[str, Any]:
    if not os.environ.get("GROQ_API_KEY", "").strip():
        raise BenchmarkConfigurationError("missing GROQ_API_KEY benchmark credential")
    price = load_controlled_price(today=today)
    projected = projected_spend_microusd(price)
    if projected > SPEND_CEILING_MICROUSD:
        raise BenchmarkConfigurationError("projected spend exceeds explicit ceiling")

    ProviderBenchmarkPreflight(
        provider=PROVIDER, model=MODEL, modality="text", dataset_id=DATASET_ID,
        credential_reference="env:GROQ_API_KEY", pricing_evidence_reference=price.evidence_reference,
        network_authorized=os.environ.get("FRUG5_QUALITY_NETWORK_AUTHORIZED", "").lower() == "true",
        spend_ceiling_microusd=SPEND_CEILING_MICROUSD, patient_data=False,
    ).validate()

    from llm.provider_registry import build_openai_compatible_provider
    provider = build_openai_compatible_provider(PROVIDER, model=MODEL)
    case_rows: list[dict[str, Any]] = []
    usage_rows: list[dict[str, int | None]] = []
    actual_cost = 0
    machine_passed = True
    try:
        for case in CASES:
            try:
                response = _invoke_case(provider, case)
                parsed = json.loads(response.choices[0].message.content or "")
                reply = parsed.get("reply") if isinstance(parsed, dict) else None
                row = _usage_row(response)
                input_tokens, output_tokens = row["input_tokens"], row["output_tokens"]
                if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
                    raise BenchmarkConfigurationError("provider token counts missing")
                actual_cost += price.worst_case_microusd(input_tokens=input_tokens, output_tokens=output_tokens)
                usage_rows.append(row)
                checks = machine_review(case, reply)
                passed = all(checks.values())
                machine_passed = machine_passed and passed
                case_rows.append({
                    "case_id": case.case_id, "locale": case.locale,
                    "synthetic_prompt": case.text, "provider_reply": reply,
                    "provider_error_type": None, "machine_checks": checks,
                    "machine_passed": passed,
                })
            except Exception as exc:
                machine_passed = False
                case_rows.append({
                    "case_id": case.case_id, "locale": case.locale,
                    "synthetic_prompt": case.text, "provider_reply": None,
                    "provider_error_type": type(exc).__name__,
                    "machine_checks": None, "machine_passed": False,
                })
                break
    finally:
        provider.client.close()

    if actual_cost > SPEND_CEILING_MICROUSD:
        raise BenchmarkConfigurationError("reported usage cost exceeded ceiling")

    report = {
        "provider": PROVIDER, "model": MODEL, "dataset_id": DATASET_ID,
        "run_date": today.isoformat(), "synthetic": True, "patient_data": False,
        "structured_output_mode": "one_case_per_json_schema_strict_call",
        "planned_calls": len(CASES), "completed_calls": len(usage_rows),
        "planned_cases": len(CASES), "evaluated_cases": len(case_rows),
        "spend_ceiling_microusd": SPEND_CEILING_MICROUSD,
        "projected_max_microusd": projected,
        "actual_cost_microusd_worst_case_from_reported_usage": actual_cost,
        "provider_usage": usage_rows,
        "machine_gate": {"passed": machine_passed and len(case_rows) == len(CASES), "required_case_ids": [case.case_id for case in CASES]},
        "human_linguistic_review": {"required": True, "status": "pending", "accepted_case_ids": None, "cost_per_accepted_safe_answer_microusd": None},
        "proof_boundaries": {"production_or_beta_traffic": False, "native_speaker_certified": False, "provider_billing_reconciled": False, "patient_egress_approved": False},
        "case_results": case_rows,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args()
    report = run_benchmark(output_path=args.output, today=date.today())
    print(json.dumps({
        "machine_passed": report["machine_gate"]["passed"],
        "completed_calls": report["completed_calls"],
        "evaluated_cases": report["evaluated_cases"],
        "actual_cost_microusd": report["actual_cost_microusd_worst_case_from_reported_usage"],
    }, ensure_ascii=False))
    return 0 if report["machine_gate"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
