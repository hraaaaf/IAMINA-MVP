"""Controlled zero-egress execution boundary for native/local TTS benchmarks."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from time import perf_counter

from .local_tts_manifest import LocalTTSManifest


class LocalTTSBenchmarkBlocked(RuntimeError):
    """Raised when a native/local TTS benchmark cannot execute safely."""


@dataclass(frozen=True, slots=True)
class LocalTTSCase:
    case_id: str
    locale: str
    text: str

    def validate(self) -> None:
        if not self.case_id.startswith("eval_tts_"):
            raise ValueError("local TTS case_id must use eval_tts_ prefix")
        if not self.locale.strip() or not self.text.strip():
            raise ValueError("local TTS case requires locale and text")


@dataclass(frozen=True, slots=True)
class LocalTTSRun:
    case_id: str
    engine: str
    output: dict[str, object]
    latency_ms: float


def execute_local_tts_benchmark(
    manifest: LocalTTSManifest,
    cases: tuple[LocalTTSCase, ...],
    *,
    adapter_factory: Callable[[str, str, str], object],
    today: date,
) -> tuple[LocalTTSRun, ...]:
    manifest.validate(today=today)
    approved_locales = set(manifest.approved_locales)
    eligible = tuple(case for case in cases if case.locale in approved_locales)
    if not eligible:
        raise LocalTTSBenchmarkBlocked("local TTS dataset has no approved-locale cases")

    adapter = adapter_factory(
        manifest.engine,
        manifest.voice,
        manifest.implementation_version,
    )
    runs: list[LocalTTSRun] = []
    for case in eligible:
        case.validate()
        started = perf_counter()
        output = adapter.invoke(case)
        elapsed = (perf_counter() - started) * 1000
        if not isinstance(output, dict):
            raise TypeError("local TTS adapter must return a structured dictionary")
        runs.append(
            LocalTTSRun(
                case_id=case.case_id,
                engine=manifest.engine,
                output=output,
                latency_ms=round(elapsed, 3),
            )
        )
    return tuple(runs)
