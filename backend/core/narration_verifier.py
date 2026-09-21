"""Fail-closed verification contract for narrated clinical output.

This foundation does not perform NLP extraction. It verifies already-observed
actions against AdviceDecision. A later adapter may extract candidate actions
from text, but cannot weaken these checks.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.contracts.advice_decision import AdviceDecision


@dataclass(frozen=True, slots=True)
class NarrationVerification:
    passed: bool
    violations: tuple[str, ...]


def verify_observed_actions(
    decision: AdviceDecision,
    observed_actions: tuple[str, ...],
) -> NarrationVerification:
    violations: list[str] = []
    seen: set[str] = set()

    for raw in observed_actions:
        if not isinstance(raw, str) or not raw.strip():
            violations.append("malformed_observed_action")
            continue
        action = raw.strip()
        if action in seen:
            continue
        seen.add(action)

        if action in decision.forbidden_actions:
            violations.append(f"forbidden:{action}")
            continue
        if action not in decision.allowed_actions:
            violations.append(f"unauthorized:{action}")

    return NarrationVerification(
        passed=not violations,
        violations=tuple(violations),
    )


def require_verified_actions(
    decision: AdviceDecision,
    observed_actions: tuple[str, ...],
) -> None:
    result = verify_observed_actions(decision, observed_actions)
    if not result.passed:
        raise PermissionError(
            "narrated output exceeds AdviceDecision: " + ", ".join(result.violations)
        )


__all__ = [
    "NarrationVerification",
    "require_verified_actions",
    "verify_observed_actions",
]
