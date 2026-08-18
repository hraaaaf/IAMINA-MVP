from datetime import date, timedelta

import pytest

from evaluation.local_tts_manifest import LocalTTSManifest
from evaluation.local_tts_runner import (
    LocalTTSBenchmarkBlocked,
    LocalTTSCase,
    execute_local_tts_benchmark,
)


class DummyTTSAdapter:
    def invoke(self, case):
        return {"rendered": bool(case.text)}


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


def test_local_tts_runner_filters_locale_without_touching_canonical_modalities():
    created = []

    def factory(engine, voice, version):
        created.append((engine, voice, version))
        return DummyTTSAdapter()

    runs = execute_local_tts_benchmark(
        _manifest(),
        (
            LocalTTSCase("eval_tts_fr", "fr", "bonjour"),
            LocalTTSCase("eval_tts_en", "en", "hello"),
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
            (LocalTTSCase("eval_tts_en", "en", "hello"),),
            adapter_factory=lambda *_args: DummyTTSAdapter(),
            today=date(2026, 8, 18),
        )


def test_local_tts_case_fails_closed_on_invalid_fixture():
    with pytest.raises(ValueError):
        LocalTTSCase("bad", "fr", "bonjour").validate()
