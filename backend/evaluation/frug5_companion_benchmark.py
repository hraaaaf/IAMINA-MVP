"""Live non-patient FRUG-5 Companion measurement on the production routing path.

The benchmark sends only controlled synthetic interactions. Deterministic
safety/zero-model routing runs through ``companion.conversation.chat``; only the
LLM lane reaches the configured Groq/GPT-OSS adapter. Retained evidence contains
only content-free route/usage aggregates and explicit proof boundaries.

This is real provider-usage evidence on synthetic traffic, not production/beta
traffic, billing reconciliation, patient-egress approval, or human linguistic
certification.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from companion.conversation import _build_runtime_prompt, chat, detect_language
from companion.parser import parse_llm_json
from companion.zero_model_router import exact_chitchat_reply
from core.input_safety import ALLOW, evaluate_input_safety
from evaluation.provider_benchmark_preflight import ProviderBenchmarkPreflight
from llm.cost_metrics import aggregate_cost_events, parse_cost_telemetry_lines
from llm.middleware.logging import LoggingMiddleware
from llm.pipeline import LLMPipeline
from llm.provider_registry import build_openai_compatible_provider
from llm.usage_telemetry import usage_workload_scope

PROVIDER = "groq"
MODEL = "openai/gpt-oss-120b"
DATASET_ID = "iamina-frug5-companion-synthetic-v1"
SPEND_CEILING_MICROUSD = 20_000
CURRENT_HISTORY_BUDGET = 1800
BASELINE_HISTORY_BUDGET = 3000
MAX_OUTPUT_TOKENS = 160


class BenchmarkConfigurationError(RuntimeError):
    """Raised when the controlled benchmark cannot support a truthful report."""


@dataclass(frozen=True, slots=True)
class CompanionCase:
    case_id: str
    language: str
    message: str
    expected_route: str


@dataclass(slots=True)
class MemoryStub:
    """Minimal relationship-memory contract used by the real Companion path."""

    milestones_celebrated: list[str] = field(default_factory=list)
    emotional_signals: list[str] = field(default_factory=list)
    last_concern: str | None = None

    def _record_keyword_emotion(self, signal: str, concern: str) -> None:
        if signal not in self.emotional_signals:
            self.emotional_signals.append(signal)
        self.last_concern = concern[:100]

    def save(self) -> None:
        return None


@dataclass(slots=True)
class DeepStub:
    """Minimal deep-memory/advice-throttle contract used by Companion runtime."""

    consecutive_log_days: int = 0
    total_interactions: int = 0
    last_log_date: str | None = None
    relationship_stage: str = "new"
    communication_style: str = "unknown"
    _advice_given: bool = False

    def advice_given_within(self, hours: int = 24) -> bool:
        del hours
        return self._advice_given

    def record_advice_given(self) -> None:
        self._advice_given = True

    def save(self) -> None:
        return None


class CostEventHandler(logging.Handler):
    """Collect the already-sanitized ``iamina.cost`` lines emitted by runtime."""

    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(record.getMessage())


class TelemetryCompanionLLM:
    """Real Groq adapter plus the production LLM usage telemetry middleware."""

    def __init__(self) -> None:
        self.provider = build_openai_compatible_provider(PROVIDER, model=MODEL)
        self.pipeline = LLMPipeline(self.provider, [LoggingMiddleware()])
        self.invalid_response = False

    def complete(self, system: str, user: str):
        with usage_workload_scope("conversation"):
            response = self.pipeline.complete(system, user)
        try:
            parse_llm_json(response.content, ["reply"])
        except Exception:
            self.invalid_response = True
        return response

    def close(self) -> None:
        self.provider.client.close()


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
        cached_input_microusd_per_million=int(raw["cached_input_microusd_per_million"]),
        output_microusd_per_million=int(raw["output_microusd_per_million"]),
        evidence_reference=raw["evidence_reference"],
        verified_on=date.fromisoformat(raw["verified_on"]),
        review_due_on=date.fromisoformat(raw["review_due_on"]),
    )
    price.validate(today=today)
    if price.provider != PROVIDER or price.model != MODEL:
        raise BenchmarkConfigurationError(
            "controlled pricing does not match FRUG-5 benchmark provider/model"
        )
    return price


def companion_cases() -> tuple[CompanionCase, ...]:
    return (
        CompanionCase("zero-fr-greeting", "fr", "Salut", "zero_model"),
        CompanionCase("zero-fr-thanks", "fr", "Merci", "zero_model"),
        CompanionCase(
            "safety-fr-insulin-dose",
            "fr",
            "Combien d'unités d'insuline je dois prendre ?",
            "safety",
        ),
        CompanionCase(
            "safety-fr-treatment-change",
            "fr",
            "Est-ce que je dois arrêter mon traitement maintenant ?",
            "safety",
        ),
        CompanionCase(
            "llm-fr-routine",
            "fr",
            "Aide-moi à garder une routine régulière de suivi, sans conseil de traitement.",
            "llm",
        ),
        CompanionCase(
            "llm-en-routine",
            "en",
            "Help me stay consistent with my tracking routine without treatment advice.",
            "llm",
        ),
        CompanionCase(
            "llm-ar-routine",
            "ar",
            "ساعدني على الاستمرار في تسجيل ملاحظاتي بانتظام دون نصائح علاجية.",
            "llm",
        ),
        CompanionCase(
            "llm-darija-routine",
            "ar-MA",
            "3tini chi tariqa bach nb9a mntadem f suivi dyali bla nasi7a 3ilajiya.",
            "llm",
        ),
    )


def expected_route(case: CompanionCase) -> str:
    if evaluate_input_safety(case.message).action != ALLOW:
        return "safety"
    language = detect_language(case.message, case.language)
    if exact_chitchat_reply(case.message, language) is not None:
        return "zero_model"
    return "llm"


def validate_route_corpus() -> tuple[CompanionCase, ...]:
    cases = companion_cases()
    for case in cases:
        resolved = expected_route(case)
        if resolved != case.expected_route:
            raise BenchmarkConfigurationError(
                f"{case.case_id}: expected {case.expected_route}, resolved {resolved}"
            )
    if not any(case.expected_route == "llm" for case in cases):
        raise BenchmarkConfigurationError("FRUG-5 benchmark requires live LLM cases")
    return cases


def synthetic_history() -> tuple[SimpleNamespace, ...]:
    """Long content-free history that exercises both 1800 and 3000 budgets."""
    base = (
        "Synthetic routine note: tracking stayed ordinary; no patient identity, "
        "no dose, no diagnosis, no prescription, and no emergency content. "
    )
    turns: list[SimpleNamespace] = []
    for index in range(10):
        role = "user" if index % 2 == 0 else "assistant"
        turns.append(SimpleNamespace(role=role, message=(base * 4) + f"turn={index}"))
    return tuple(turns)


def _recent_turns_stub(history: tuple[SimpleNamespace, ...]):
    def recent(_patient, limit: int, offset: int = 0, role: str | None = None):
        items = [turn for turn in history if role is None or turn.role == role]
        if offset:
            items = items[:-offset] if offset < len(items) else []
        return list(reversed(items[-limit:]))

    return recent


def build_prompt_for_case(
    case: CompanionCase,
    *,
    history_budget: int,
) -> tuple[str, str]:
    history = synthetic_history()
    with (
        patch("companion.conversation._recent_turns", side_effect=_recent_turns_stub(history)),
        patch("companion.conversation._HISTORY_CHAR_BUDGET", history_budget),
    ):
        _language, _ctx, system, user = _build_runtime_prompt(
            message=case.message,
            memory=MemoryStub(),
            deep=DeepStub(),
            language=case.language,
            patient=None,
            context_days=14,
            streaming=False,
        )
    return system, user


def _projected_spend_microusd(
    llm_cases: tuple[CompanionCase, ...],
    price,
) -> int:
    total = 0
    for case in llm_cases:
        for budget in (CURRENT_HISTORY_BUDGET, BASELINE_HISTORY_BUDGET):
            system, user = build_prompt_for_case(case, history_budget=budget)
            # UTF-8 bytes are a conservative tokenizer-independent upper bound.
            input_upper_bound = len((system + user).encode("utf-8"))
            total += price.worst_case_microusd(
                input_tokens=input_upper_bound,
                output_tokens=MAX_OUTPUT_TOKENS,
            )
    return total


def _cost_from_usage_event(event: dict[str, Any], price) -> int:
    input_tokens = event.get("input_tokens")
    output_tokens = event.get("output_tokens")
    if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
        raise BenchmarkConfigurationError("provider token counts missing from live telemetry")
    return price.worst_case_microusd(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


def _usage_event_from_response(response, *, prompt_chars: int) -> dict[str, Any]:
    usage = response.usage
    if usage is None:
        raise BenchmarkConfigurationError("baseline provider usage evidence missing")
    return {
        "event": "llm_usage",
        "status": "success",
        "workload": "conversation",
        "provider_route": response.provider,
        "from_cache": bool(response.from_cache),
        "prompt_chars": prompt_chars,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cached_input_tokens": usage.cached_input_tokens,
        "total_tokens": usage.total_tokens,
    }


def run_benchmark(*, output_path: Path, today: date) -> dict[str, Any]:
    if not os.environ.get("GROQ_API_KEY", "").strip():
        raise BenchmarkConfigurationError("missing GROQ_API_KEY benchmark credential")

    ProviderBenchmarkPreflight(
        provider=PROVIDER,
        model=MODEL,
        modality="text",
        dataset_id=DATASET_ID,
        credential_reference="env:GROQ_API_KEY",
        pricing_evidence_reference="issue-430-comment-5358477221",
        network_authorized=os.environ.get("FRUG5_NETWORK_AUTHORIZED", "").lower()
        == "true",
        spend_ceiling_microusd=SPEND_CEILING_MICROUSD,
        patient_data=False,
    ).validate()

    cases = validate_route_corpus()
    llm_cases = tuple(case for case in cases if case.expected_route == "llm")
    price = load_controlled_price(today=today)
    projected = _projected_spend_microusd(llm_cases, price)
    if projected > SPEND_CEILING_MICROUSD:
        raise BenchmarkConfigurationError(
            f"projected benchmark ceiling {projected} exceeds "
            f"{SPEND_CEILING_MICROUSD} microusd"
        )

    cost_logger = logging.getLogger("iamina.cost")
    handler = CostEventHandler()
    old_level = cost_logger.level
    cost_logger.addHandler(handler)
    cost_logger.setLevel(logging.INFO)
    llm = TelemetryCompanionLLM()
    history = synthetic_history()
    try:
        for case in cases:
            with patch(
                "companion.conversation._recent_turns",
                side_effect=_recent_turns_stub(history),
            ):
                reply = chat(
                    case.message,
                    memory=MemoryStub(),
                    deep=DeepStub(),
                    llm=llm,
                    language=case.language,
                    patient=None,
                )
            if not isinstance(reply, str) or not reply.strip():
                raise BenchmarkConfigurationError(f"{case.case_id}: empty Companion reply")

        if llm.invalid_response:
            raise BenchmarkConfigurationError(
                "one or more live provider responses violated the Companion JSON contract"
            )

        live_events = parse_cost_telemetry_lines(handler.lines)
        current_report = aggregate_cost_events(live_events)

        baseline_events: list[dict[str, Any]] = []
        baseline_cost_microusd = 0
        for case in llm_cases:
            system, user = build_prompt_for_case(
                case,
                history_budget=BASELINE_HISTORY_BUDGET,
            )
            response = llm.provider.complete(system, user)
            event = _usage_event_from_response(
                response,
                prompt_chars=len(system) + len(user),
            )
            baseline_events.append(event)
            baseline_cost_microusd += _cost_from_usage_event(event, price)
    finally:
        llm.close()
        cost_logger.removeHandler(handler)
        cost_logger.setLevel(old_level)

    baseline_report = aggregate_cost_events(baseline_events)
    if current_report["interactions"] != len(cases):
        raise BenchmarkConfigurationError(
            "Companion route denominator did not match controlled interaction count"
        )
    if current_report["llm_success_events"] != len(llm_cases):
        raise BenchmarkConfigurationError(
            "live LLM success count did not match controlled LLM route count"
        )

    current_llm_events = [
        event
        for event in live_events
        if event.get("event") == "llm_usage" and event.get("status") == "success"
    ]
    current_cost_microusd = sum(
        _cost_from_usage_event(event, price) for event in current_llm_events
    )
    actual_cost_microusd = current_cost_microusd + baseline_cost_microusd
    if actual_cost_microusd > SPEND_CEILING_MICROUSD:
        raise BenchmarkConfigurationError("reported benchmark spend exceeded explicit ceiling")

    current_input = current_report["overall"]["distributions"]["input_tokens"]
    baseline_input = baseline_report["overall"]["distributions"]["input_tokens"]
    current_p95 = current_input["p95"]
    baseline_p95 = baseline_input["p95"]
    p95_delta_tokens = (
        current_p95 - baseline_p95
        if isinstance(current_p95, int) and isinstance(baseline_p95, int)
        else None
    )
    p95_reduction_ratio = (
        (baseline_p95 - current_p95) / baseline_p95
        if isinstance(current_p95, int)
        and isinstance(baseline_p95, int)
        and baseline_p95 > 0
        else None
    )

    report = {
        "provider": PROVIDER,
        "model": MODEL,
        "dataset_id": DATASET_ID,
        "run_date": today.isoformat(),
        "synthetic": True,
        "patient_data": False,
        "traffic_scope": "controlled_synthetic_companion_production_path",
        "pricing_evidence_reference": price.evidence_reference,
        "spend_ceiling_microusd": SPEND_CEILING_MICROUSD,
        "projected_max_microusd": projected,
        "actual_cost_microusd_worst_case_from_reported_usage": actual_cost_microusd,
        "current_runtime": {
            "history_budget_chars": CURRENT_HISTORY_BUDGET,
            "interactions": current_report["interactions"],
            "route_counts": current_report["route_counts"],
            "llm_call_rate_per_interaction": current_report[
                "llm_call_rate_per_interaction"
            ],
            "zero_model_rate_per_interaction": current_report[
                "zero_model_rate_per_interaction"
            ],
            "safety_rate_per_interaction": current_report[
                "safety_rate_per_interaction"
            ],
            "llm_success_events": current_report["llm_success_events"],
            "llm_error_events": current_report["llm_error_events"],
            "conversation_token_distributions": current_report["by_workload"].get(
                "conversation"
            ),
            "observed_llm_cost_microusd": current_cost_microusd,
            "cost_per_observed_llm_answer_microusd": (
                current_cost_microusd / len(llm_cases) if llm_cases else None
            ),
        },
        "history_window_live_comparison": {
            "baseline_history_budget_chars": BASELINE_HISTORY_BUDGET,
            "current_history_budget_chars": CURRENT_HISTORY_BUDGET,
            "baseline_input_tokens": baseline_input,
            "current_input_tokens": current_input,
            "p95_delta_tokens_current_minus_baseline": p95_delta_tokens,
            "p95_reduction_ratio": p95_reduction_ratio,
            "baseline_cost_microusd": baseline_cost_microusd,
            "current_cost_microusd": current_cost_microusd,
        },
        "proof_boundaries": {
            "production_or_beta_traffic": False,
            "provider_billing_reconciliation": False,
            "native_speaker_quality_certification": False,
            "patient_egress_approval": False,
            "cost_per_accepted_safe_answer": None,
            "reason": (
                "Real provider usage on synthetic Companion inputs does not replace "
                "observed beta traffic, billing reconciliation, or human acceptance."
            ),
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
    report = run_benchmark(output_path=args.output, today=date.today())
    print(
        json.dumps(
            {
                "llm_call_rate": report["current_runtime"][
                    "llm_call_rate_per_interaction"
                ],
                "input_p95": report["current_runtime"][
                    "conversation_token_distributions"
                ]["distributions"]["input_tokens"]["p95"],
                "p95_reduction_ratio": report["history_window_live_comparison"][
                    "p95_reduction_ratio"
                ],
                "actual_cost_microusd": report[
                    "actual_cost_microusd_worst_case_from_reported_usage"
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
