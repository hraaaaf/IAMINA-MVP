"""Controlled zero-egress execution boundary for local synthetic OCR benchmarks."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from .contracts import EvaluationCase, Modality
from .local_ocr_manifest import LocalOCRManifest
from .runner import CaseRun, run_dataset


class LocalOCRBenchmarkBlocked(RuntimeError):
    """Raised when a local OCR benchmark cannot execute safely."""


LOCAL_OCR_MODALITIES = frozenset(
    {Modality.DOCUMENT_OCR, Modality.GLUCOMETER_OCR}
)


def execute_local_ocr_benchmark(
    manifest: LocalOCRManifest,
    cases: tuple[EvaluationCase, ...],
    *,
    adapter_factory: Callable[[str, str, str], object],
    today: date,
) -> tuple[CaseRun, ...]:
    """Run local OCR cases without credentials or network-provider semantics."""
    manifest.validate(today=today)
    approved = set(manifest.approved_modalities)
    ocr_cases = tuple(
        case
        for case in cases
        if case.modality in LOCAL_OCR_MODALITIES
        and case.modality.value in approved
    )
    if not ocr_cases:
        raise LocalOCRBenchmarkBlocked(
            "canonical dataset contains no approved local OCR cases"
        )
    adapter = adapter_factory(
        manifest.engine,
        manifest.model,
        manifest.implementation_version,
    )
    return run_dataset(adapter, ocr_cases)
