"""Controlled execution boundary for live synthetic STT benchmarks."""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import date

from .contracts import EvaluationCase, Modality
from .runner import CaseRun, run_dataset
from .stt_live_manifest import STTProviderManifest


class STTBenchmarkBlocked(RuntimeError):
    """Raised when the live STT benchmark is not authorized to execute."""


def execute_live_stt_benchmark(
    manifest: STTProviderManifest,
    cases: tuple[EvaluationCase, ...],
    *,
    adapter_factory: Callable[[str, str, str], object],
    today: date,
) -> tuple[CaseRun, ...]:
    manifest.validate(today=today)
    credential = os.environ.get(manifest.credential_env_var, "").strip()
    if not credential:
        raise STTBenchmarkBlocked(
            f"missing benchmark credential environment variable: {manifest.credential_env_var}"
        )
    stt_cases = tuple(case for case in cases if case.modality is Modality.STT)
    if not stt_cases:
        raise STTBenchmarkBlocked("canonical dataset contains no STT cases")
    adapter = adapter_factory(manifest.provider, manifest.model, credential)
    return run_dataset(adapter, stt_cases)
