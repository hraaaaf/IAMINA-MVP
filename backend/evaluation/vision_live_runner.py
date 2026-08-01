"""Controlled execution boundary for live synthetic vision/OCR benchmarks."""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import date

from .contracts import EvaluationCase, Modality
from .runner import CaseRun, run_dataset
from .vision_live_manifest import VisionProviderManifest


class VisionBenchmarkBlocked(RuntimeError):
    """Raised when the live vision benchmark is not authorized to execute."""


VISION_MODALITIES = frozenset(
    {Modality.DOCUMENT_OCR, Modality.GLUCOMETER_OCR, Modality.MEAL_VISION}
)


def execute_live_vision_benchmark(
    manifest: VisionProviderManifest,
    cases: tuple[EvaluationCase, ...],
    *,
    adapter_factory: Callable[[str, str, str], object],
    today: date,
) -> tuple[CaseRun, ...]:
    manifest.validate(today=today)
    credential = os.environ.get(manifest.credential_env_var, "").strip()
    if not credential:
        raise VisionBenchmarkBlocked(
            f"missing benchmark credential environment variable: {manifest.credential_env_var}"
        )
    vision_cases = tuple(case for case in cases if case.modality in VISION_MODALITIES)
    if not vision_cases:
        raise VisionBenchmarkBlocked("canonical dataset contains no vision/OCR cases")
    adapter = adapter_factory(manifest.provider, manifest.model, credential)
    return run_dataset(adapter, vision_cases)
