"""Controlled zero-egress execution boundary for local/on-device STT benchmarks."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from .contracts import EvaluationCase, Modality
from .local_stt_manifest import LocalSTTManifest
from .runner import CaseRun, run_dataset


class LocalSTTBenchmarkBlocked(RuntimeError):
    """Raised when a local STT benchmark cannot execute safely."""


def execute_local_stt_benchmark(
    manifest: LocalSTTManifest,
    cases: tuple[EvaluationCase, ...],
    *,
    adapter_factory: Callable[[str, str, str], object],
    today: date,
) -> tuple[CaseRun, ...]:
    manifest.validate(today=today)
    stt_cases = tuple(case for case in cases if case.modality is Modality.STT)
    if not stt_cases:
        raise LocalSTTBenchmarkBlocked("canonical dataset contains no STT cases")
    adapter = adapter_factory(
        manifest.engine,
        manifest.model,
        manifest.implementation_version,
    )
    return run_dataset(adapter, stt_cases)
