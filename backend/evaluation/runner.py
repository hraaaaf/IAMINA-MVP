"""Provider-neutral benchmark execution with explicit evidence provenance."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Protocol

from .contracts import EvaluationCase


class EvaluationAdapter(Protocol):
    name: str

    def invoke(self, case: EvaluationCase) -> dict[str, object]: ...


@dataclass(frozen=True, slots=True)
class CaseRun:
    case_id: str
    provider: str
    output: dict[str, object]
    latency_ms: float
    dataset_fingerprint: str


def run_case(adapter: EvaluationAdapter, case: EvaluationCase) -> CaseRun:
    case.validate()
    started = perf_counter()
    output = adapter.invoke(case)
    elapsed = (perf_counter() - started) * 1000
    if not isinstance(output, dict):
        raise TypeError("evaluation adapters must return a structured dictionary")
    return CaseRun(
        case_id=case.case_id,
        provider=adapter.name,
        output=output,
        latency_ms=round(elapsed, 3),
        dataset_fingerprint=case.fingerprint,
    )


def run_dataset(
    adapter: EvaluationAdapter,
    cases: tuple[EvaluationCase, ...],
) -> tuple[CaseRun, ...]:
    return tuple(run_case(adapter, case) for case in cases)
