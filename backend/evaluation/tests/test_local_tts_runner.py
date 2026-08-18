from datetime import date, timedelta

import pytest

from evaluation.contracts import EvaluationCase, Locale, Modality, Severity
from evaluation.local_tts_manifest import LocalTTSManifest
from evaluation.local_tts_runner import (
    LocalTTSBenchmarkBlocked,
    execute_local_tts_benchmark,
)


class DummyTTSAdapter:
    name = "local-tts-test"

    def invoke(self, case):
        return {"rendered": case.expected.get("rendered", True)}


def _manifest() -> LocalTTSManifest:
    today = date(2026, 8, 18)
    return LocalTTSManifest(
        engine="native-os-tts",
        voice="system-default",
        implementation_version="test-version",
        evidence_source="controlled-local-fixture",
        verified_on=today,
        review_due_on=today + timedelta(days=30),
        approved_locales=("fr", "ar", "ar-MA"),
        approved_for_synthetic_benchmark=True,
    )


def _case(case_id: str, modality: Modality, locale: Locale) -> EvaluationCase:
    return EvaluationCase(
        case_id=case_id,
        modality=modality,
        locale=locale,
        severity=Severity.ROUTINE,
        input_payload={"text": "bonjour"},
        expected={"rendered": True},
        tags=("synthetic",),
    )


def test_local_tts_runner_filters_modality_and_locale():
    created = []

    def factory(engine, voice, version):
        created.append((engine, voice, version))
        return DummyTTSAdapter()

    runs = execute_local_tts_benchmark(
        _manifest(),
        (
            _case("eval_tts_fr", Modality.TTS, Locale.FR),
            _case("eval_tts_en", Modality.TTS, Locale.EN),
            _case("eval_text", Modality.TEXT, Locale.FR),
        ),
        adapter_factory=factory,
        today=date(2026, 8, 18),
    )

    assert [run.case_id for run in runs] == ["eval_tts_fr"]
    assert created == [("native-os-tts", "system-default", "test-version")]


def test_local_tts_runner_fails_without_eligible_cases():
    with pytest.raises(LocalTTSBenchmarkBlocked):
        execute_local_tts_benchmark(
            _manifest(),
            (_case("eval_tts_en", Modality.TTS, Locale.EN),),
            adapter_factory=lambda *_args: DummyTTSAdapter(),
            today=date(2026, 8, 18),
        )
