"""Fail-closed privacy validation for benchmark fixtures."""

from __future__ import annotations

import re
from collections.abc import Iterable

from evaluation.contracts import EvaluationCase


_FORBIDDEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("email", re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b", re.IGNORECASE)),
    ("phone", re.compile(r"(?<!\d)(?:\+?212|0)[5-7]\d{8}(?!\d)")),
    ("uuid", re.compile(r"\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b", re.IGNORECASE)),
    ("moroccan_id", re.compile(r"\b[A-Z]{1,2}\d{5,8}\b")),
)


def _strings(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _strings(key)
            yield from _strings(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _strings(item)


def identity_findings(case: EvaluationCase) -> tuple[str, ...]:
    findings: set[str] = set()
    for text in _strings((case.input_payload, case.expected)):
        for category, pattern in _FORBIDDEN_PATTERNS:
            if pattern.search(text):
                findings.add(category)
    return tuple(sorted(findings))


def assert_fixture_privacy(case: EvaluationCase) -> None:
    findings = identity_findings(case)
    if findings:
        raise ValueError(
            "benchmark fixture contains forbidden identity categories: "
            + ", ".join(findings)
        )
