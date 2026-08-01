"""Controlled execution boundary for live synthetic text benchmarks."""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import date

from .contracts import EvaluationCase, Modality
from .runner import CaseRun, run_dataset
from .text_live_manifest import TextProviderManifest


class TextBenchmarkBlocked(RuntimeError):
    """Raised when the live text benchmark is not authorized to execute."""


def execute_live_text_benchmark(
    manifest: TextProviderManifest,
    cases: tuple[EvaluationCase, ...],
    *,
    adapter_factory: Callable[[str, str, str], object],
    today: date,
) -> tuple[CaseRun, ...]:
    manifest.validate(today=today)
    credential = os.environ.get(manifest.credential_env_var, "").strip()
    if not credential:
        raise TextBenchmarkBlocked(
            f"missing benchmark credential environment variable: {manifest.credential_env_var}"
        )
    text_cases = tuple(case for case in cases if case.modality is Modality.TEXT)
    if not text_cases:
        raise TextBenchmarkBlocked("canonical dataset contains no text cases")
    adapter = adapter_factory(manifest.provider, manifest.model, credential)
    return run_dataset(adapter, text_cases)
