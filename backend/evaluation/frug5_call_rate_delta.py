"""Deterministic before/after FRUG-5 Companion call-rate evidence.

This intentionally measures a controlled optimization corpus, not production traffic.
The baseline replay is pinned to the pre-farewell zero-model router merged at the
recorded commit/blob. Current routing executes the production zero-model router.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from companion.zero_model_router import exact_chitchat_reply

BASELINE_ROUTER_COMMIT = "299676ca99c357f6146eb772048eeeaa6a10c2af"
BASELINE_ROUTER_BLOB = "80ec292ebe2032503d45117555cb84e89d1a0320"

_TRAILING_PUNCTUATION = re.compile(r"[\s.!?…،؛:]+$")
_INTERNAL_SPACE = re.compile(r"\s+")
_BASELINE_ZERO_MODEL = frozenset(
    {
        "salut",
        "hello",
        "hi",
        "salam",
        "سلام",
        "السلام عليكم",
        "merci",
        "merci beaucoup",
        "thanks",
        "thank you",
        "chokran",
        "شكرا",
        "شكراً",
    }
)


@dataclass(frozen=True, slots=True)
class RouteCase:
    case_id: str
    message: str
    locale: str
    baseline_route: str
    current_route: str


CASES = (
    RouteCase("fr-greeting", "Salut", "fr", "zero_model", "zero_model"),
    RouteCase("en-thanks", "thank you", "en", "zero_model", "zero_model"),
    RouteCase("ar-greeting", "سلام", "ar", "zero_model", "zero_model"),
    RouteCase("ma-thanks", "chokran", "ar-MA", "zero_model", "zero_model"),
    RouteCase("fr-farewell", "au revoir", "fr", "llm", "zero_model"),
    RouteCase("en-farewell", "goodbye", "en", "llm", "zero_model"),
    RouteCase("ar-farewell", "مع السلامة", "ar", "llm", "zero_model"),
    RouteCase("ma-farewell", "bslama", "ar-MA", "llm", "zero_model"),
    RouteCase(
        "fr-health",
        "Pourquoi ma glycémie varie après le repas ?",
        "fr",
        "llm",
        "llm",
    ),
    RouteCase(
        "ar-health",
        "ليش السكر يتغير بعد الأكل؟",
        "ar",
        "llm",
        "llm",
    ),
    RouteCase("ambiguous-ok", "ok", "fr", "llm", "llm"),
    RouteCase(
        "farewell-extra-content",
        "au revoir glycémie",
        "fr",
        "llm",
        "llm",
    ),
)


def _normalize(message: str) -> str:
    normalized = _INTERNAL_SPACE.sub(" ", message.strip().casefold())
    return _TRAILING_PUNCTUATION.sub("", normalized)


def baseline_route(message: str) -> str:
    return "zero_model" if _normalize(message) in _BASELINE_ZERO_MODEL else "llm"


def current_route(message: str, locale: str) -> str:
    return "zero_model" if exact_chitchat_reply(message, locale) is not None else "llm"


def build_call_rate_report() -> dict[str, object]:
    rows = []
    baseline_llm = 0
    current_llm = 0
    for case in CASES:
        observed_baseline = baseline_route(case.message)
        observed_current = current_route(case.message, case.locale)
        if observed_baseline != case.baseline_route:
            raise AssertionError(f"baseline route drift: {case.case_id}")
        if observed_current != case.current_route:
            raise AssertionError(f"current route drift: {case.case_id}")
        baseline_llm += int(observed_baseline == "llm")
        current_llm += int(observed_current == "llm")
        rows.append(
            {
                "case_id": case.case_id,
                "locale": case.locale,
                "baseline_route": observed_baseline,
                "current_route": observed_current,
            }
        )

    interactions = len(CASES)
    baseline_rate = baseline_llm / interactions
    current_rate = current_llm / interactions
    relative_reduction = (
        (baseline_rate - current_rate) / baseline_rate if baseline_rate else 0.0
    )
    return {
        "evidence_scope": "controlled_synthetic_route_mix_not_production",
        "baseline_router_commit": BASELINE_ROUTER_COMMIT,
        "baseline_router_blob": BASELINE_ROUTER_BLOB,
        "interactions": interactions,
        "baseline": {
            "llm_calls": baseline_llm,
            "zero_model_calls": interactions - baseline_llm,
            "llm_call_rate_per_interaction": baseline_rate,
        },
        "current": {
            "llm_calls": current_llm,
            "zero_model_calls": interactions - current_llm,
            "llm_call_rate_per_interaction": current_rate,
        },
        "absolute_rate_delta": current_rate - baseline_rate,
        "relative_llm_call_reduction": relative_reduction,
        "cases": rows,
    }
