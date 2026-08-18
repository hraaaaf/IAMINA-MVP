"""Controlled zero-egress execution boundary for native/local TTS benchmarks."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from .contracts import EvaluationCase, Modality
from .local_tts_manifest import LocalTTSManifest
from .runner import CaseRun, run_dataset


class LocalTTSBenchmarkBlocked(RuntimeError):
    """Raised when a native/local TTS benchmark cannot execute safely."""


def execute_local_tts_benchmark(
    manifest: LocalTTSManifest,
    cases: tuple[EvaluationCase, ...],
    *,
    adapter_factory: Callable[[str, str, str], object],
    today: date,
) -> tuple[CaseRun, ...]:
    manifest.validate(today=today)
    approved_locales = set(manifest.approved_locales)
    tts_cases = tuple(
        case
        for case in cases
        if case.modality is Modality.TTS and case.locale.value in approved_locales
    )
    if not tts_cases:
        raise LocalTTSBenchmarkBlocked(
            "canonical dataset contains no approved-locale TTS cases"
        )
    adapter = adapter_factory(
        manifest.engine,
        manifest.voice,
        manifest.implementation_version,
    )
    return run_dataset(adapter, tts_cases)
