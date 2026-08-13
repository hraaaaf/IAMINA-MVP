from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvalCase:
    case_id: str
    dimension: str
    expected: bool


def validate_cases(cases: tuple[EvalCase, ...]) -> None:
    ids = tuple(case.case_id for case in cases)
    if any(not case_id.strip() for case_id in ids):
        raise ValueError("case_id must not be empty")
    if len(set(ids)) != len(ids):
        raise ValueError("case_id must be unique")
    if any(not case.dimension.strip() for case in cases):
        raise ValueError("dimension must not be empty")
