"""Controlled zero-egress execution boundary for local/on-device STT benchmarks."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from datetime import date
from pathlib import Path

from .contracts import EvaluationCase, Modality
from .local_stt_manifest import LocalSTTManifest
from .runner import CaseRun, run_dataset


class LocalSTTBenchmarkBlocked(RuntimeError):
    """Raised when a local STT benchmark cannot execute safely."""


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_AUDIO_SUFFIXES = frozenset({".wav", ".mp3", ".m4a", ".mp4", ".webm", ".ogg", ".flac"})


def _validate_audio_fixture(case: EvaluationCase) -> None:
    """Require a real, integrity-pinned audio file before measuring STT."""
    fixture = case.input_payload.get("audio_fixture")
    digest = case.input_payload.get("audio_sha256")

    if not isinstance(fixture, str) or not fixture.strip():
        raise LocalSTTBenchmarkBlocked(
            f"{case.case_id}: STT benchmark requires audio_fixture; transcript text alone is not evidence"
        )
    path = Path(fixture)
    if path.is_absolute() or ".." in path.parts:
        raise LocalSTTBenchmarkBlocked(
            f"{case.case_id}: audio_fixture must be a repository-relative path"
        )
    if path.suffix.lower() not in _ALLOWED_AUDIO_SUFFIXES:
        raise LocalSTTBenchmarkBlocked(
            f"{case.case_id}: unsupported audio fixture format {path.suffix!r}"
        )
    if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
        raise LocalSTTBenchmarkBlocked(
            f"{case.case_id}: audio_sha256 must be a lowercase SHA-256 digest"
        )
    if not path.is_file():
        raise LocalSTTBenchmarkBlocked(
            f"{case.case_id}: audio fixture does not exist: {fixture}"
        )

    observed = hashlib.sha256(path.read_bytes()).hexdigest()
    if observed != digest:
        raise LocalSTTBenchmarkBlocked(
            f"{case.case_id}: audio fixture SHA-256 mismatch"
        )


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

    for case in stt_cases:
        _validate_audio_fixture(case)

    adapter = adapter_factory(
        manifest.engine,
        manifest.model,
        manifest.implementation_version,
    )
    return run_dataset(adapter, stt_cases)
