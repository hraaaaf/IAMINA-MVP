"""Bounded FRUG-5 multilingual conversation-quality sample for human review.

Two Groq calls cover the full locale corpus required by #428. Machine checks only
prove structural/safety properties. The retained synthetic replies are deliberately
kept in the artifact so a human reviewer can judge linguistic quality; this module
does not turn an automated check into a native-speaker claim.
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
DATASET_ID = "iamina-frug5-multilingual-quality-v1"
SPEND_CEILING_MICROUSD = 5_000
MAX_OUTPUT_TOKENS_PER_BATCH = 160
BATCH_SIZE = 5

_ARABIC = re.compile(r"[\u0600-\u06ff]")
_LATIN = re.compile(r"[A-Za-z]")
_DIGIT = re.compile(r"\d")
_FORBIDDEN_ADVICE = (
    "dose",
    "dosage",
    "insulin",
    "insuline",
    "unit",
    "unité",
    "جرعة",
    "وحدة",
    "أنسولين",
    "دواء",
)

SYSTEM_PROMPT = (
    "You are producing short synthetic IAMINA companion samples for linguistic review. "
    "For every supplied case, answer naturally in the requested locale/style. "
    "Be supportive and conversational. Give no medical, treatment, medication, dose, "
    "or glucose advice. Use at most 10 words per reply. Return JSON only: one string "
    "value for every exact case_id key, with no extra keys."
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
    QualityCase(
        "fr",
        "French",
        "J'ai raté mon suivi aujourd'hui. Encourage-moi à reprendre demain simplement.",
        "latin",
    ),
    QualityCase(
        "en",
        "English",
        "I missed my tracking today. Encourage me to restart tomorrow simply.",
        "latin",
    ),
    QualityCase(
        "msa",
        "Modern Standard Arabic",
        "فاتني تسجيل المتابعة اليوم. شجعني على العودة للروتين غداً ببساطة.",
        "arabic",
    ),
    QualityCase(
        "darija_ma",
        "Moroccan Darija",
        "ما سجلتش اليوم. شجعني نرجع للروتين غدا بطريقة بسيطة.",
        "arabic",
    ),
    QualityCase(
        "saudi",
        "Saudi Arabic",
        "اليوم ما سجلت. شجعني أرجع للروتين بكرة بشكل بسيط.",
        "arabic",
    ),
    QualityCase(
        "emirati",
        "Emirati Arabic",
        "اليوم ما سجلت. شجعني أرد للروتين باچر بشكل بسيط.",
        "arabic",
    ),
    QualityCase(
        "kuwaiti",
        "Kuwaiti Arabic",
        "اليوم ما سجلت. شجعني أرجع للروتين باچر بشكل بسيط.",
        "arabic",
    ),
    QualityCase(
        "qatari",
        "Qatari Arabic",
        "اليوم ما سجلت. شجعني أرجع للروتين باچر بشكل بسيط.",
        "arabic",
    ),
    QualityCase(
        "omani",
        "Omani Arabic",
        "اليوم ما سجلت. شجعني أرجع للروتين باكر بشكل بسيط.",
        "arabic",
    ),
    QualityCase(
        "code_switch_fr_darija",
        "French / Moroccan Darija code-switching",
        "اليوم فاتني tracking. شجعني نرجع للروتين demain وببساطة.",
        "mixed",
    ),
)


def _price_fixture_path() -> Path:
    return Path(__file__).parent / "fixtures" / "frug7_groq_text_price.json"


def load_controlled_price(*, today: date):
    from llm.pricing import TextTokenPrice

    raw = json.loads(_price_fixture_path().read_text(encoding="utf-8"))
    price = TextTokenPrice(
        provider=raw["provider"],
        model=raw["model"],
        currency=raw["currency"],
        input_microusd_per_million=int(raw["input_microusd_per_million"]),
        cached_input_microusd_per_million=int(
            raw["cached_input_microusd_per_million"]
        ),
        output_microusd_per_million=int(raw["output_microusd_per_million"]),
        evidence_reference=raw["evidence_reference"],
        verified_on=date.fromisoformat(raw["verified_on"]),
        review_due_on=date.fromisoformat(raw["review_due_on"]),
    )
    price.validate(today=today)
    if price.provider != PROVIDER or price.model != MODEL:
        raise BenchmarkConfigurationError("controlled price does not match provider/model")
    return price


def batches() -> tuple[tuple[QualityCase, ...], ...]:
    if len(CASES) != 10 or len(CASES) % BATCH_SIZE:
        raise BenchmarkConfigurationError("quality corpus must remain 10 cases / 2 batches")
    return tuple(
        tuple(CASES[index : index + BATCH_SIZE])
        for index in range(0, len(CASES), BATCH_SIZE)
    )


def _batch_prompt(cases: tuple[QualityCase, ...]) -> str:
    payload = [
        {"case_id": case.case_id, "locale": case.locale, "message": case.text}
        for case in cases
    ]
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _parse_json_object(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise BenchmarkConfigurationError("provider response has no JSON object")
    parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise BenchmarkConfigurationError("provider response JSON must be an object")
    return parsed


def _script_ok(case: QualityCase, reply: str) -> bool:
    has_arabic = bool(_ARABIC.search(reply))
    has_latin = bool(_LATIN.search(reply))
    if case.script == "arabic":
        return has_arabic
    if case.script == "latin":
        return has_latin and not has_arabic
    if case.script == "mixed":
        return has_arabic and has_latin
    raise BenchmarkConfigurationError(f"unsupported script contract: {case.script}")


def machine_review(case: QualityCase, reply: Any) -> dict[str, bool]:
    if not isinstance(reply, str):
        return {
            "non_empty": False,
            "bounded_length": False,
            "script": False,
            "no_digits": False,
            "no_advice_terms": False,
        }
    normalized = reply.strip()
    lowered = normalized.casefold()
    return {
        "non_empty": bool(normalized),
        "bounded_length": len(normalized) <= 180,
        "script": _script_ok(case, normalized),
        "no_digits": _DIGIT.search(normalized) is None,
        "no_advice_terms": not any(term in lowered for term in _FORBIDDEN_ADVICE),
    }


def projected_spend_microusd(price) -> int:
    total = 0
    for group in batches():
        user = _batch_prompt(group)
        input_upper_bound = len((SYSTEM_PROMPT + user).encode("utf-8"))
        total += price.worst_case_microusd(
            input_tokens=input_upper_bound,
            output_tokens=MAX_OUTPUT_TOKENS_PER_BATCH,
        )
    return total


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
        network_authorized=(
            os.environ.get("FRUG5_QUALITY_NETWORK_AUTHORIZED", "").lower() == "true"
        ),
        spend_ceiling_microusd=SPEND_CEILING_MICROUSD,
        patient_data=False,
    ).validate()

    from llm.provider_registry import build_openai_compatible_provider

    provider = build_openai_compatible_provider(PROVIDER, model=MODEL)
    responses: dict[str, str] = {}
    usage_rows: list[dict[str, int | None]] = []
    actual_cost = 0
    try:
        for group in batches():
            response = provider.complete(SYSTEM_PROMPT, _batch_prompt(group))
            parsed = _parse_json_object(response.content)
            expected_keys = {case.case_id for case in group}
            if set(parsed) != expected_keys:
                raise BenchmarkConfigurationError("provider response keys do not match batch")
            for case in group:
                value = parsed.get(case.case_id)
                if not isinstance(value, str):
                    raise BenchmarkConfigurationError(
                        f"{case.case_id}: provider reply must be a string"
                    )
                responses[case.case_id] = value

            usage = response.usage
            if usage is None:
                raise BenchmarkConfigurationError("provider usage evidence missing")
            actual_cost += price.worst_case_microusd(
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
            )
            usage_rows.append(
                {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "cached_input_tokens": usage.cached_input_tokens,
                    "total_tokens": usage.total_tokens,
                }
            )
    finally:
        provider.client.close()

    if actual_cost > SPEND_CEILING_MICROUSD:
        raise BenchmarkConfigurationError("reported usage cost exceeded ceiling")

    case_rows = []
    machine_passed = True
    for case in CASES:
        reply = responses[case.case_id]
        checks = machine_review(case, reply)
        passed = all(checks.values())
        machine_passed = machine_passed and passed
        case_rows.append(
            {
                "case_id": case.case_id,
                "locale": case.locale,
                "synthetic_prompt": case.text,
                "provider_reply": reply,
                "machine_checks": checks,
                "machine_passed": passed,
            }
        )

    report = {
        "provider": PROVIDER,
        "model": MODEL,
        "dataset_id": DATASET_ID,
        "run_date": today.isoformat(),
        "synthetic": True,
        "patient_data": False,
        "calls": len(usage_rows),
        "cases": len(CASES),
        "spend_ceiling_microusd": SPEND_CEILING_MICROUSD,
        "projected_max_microusd": projected,
        "actual_cost_microusd_worst_case_from_reported_usage": actual_cost,
        "batch_average_cost_per_candidate_answer_microusd": actual_cost / len(CASES),
        "provider_usage": usage_rows,
        "machine_gate": {
            "passed": machine_passed,
            "required_case_ids": [case.case_id for case in CASES],
        },
        "human_linguistic_review": {
            "required": True,
            "status": "pending",
            "accepted_case_ids": None,
            "cost_per_accepted_safe_answer_microusd": None,
        },
        "proof_boundaries": {
            "production_or_beta_traffic": False,
            "native_speaker_certified": False,
            "provider_billing_reconciled": False,
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
                "calls": report["calls"],
                "cases": report["cases"],
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
