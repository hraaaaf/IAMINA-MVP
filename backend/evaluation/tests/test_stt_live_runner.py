from datetime import date

import pytest

from evaluation.dataset import validated_cases
from evaluation.stt_live_manifest import STTProviderManifest
from evaluation.stt_live_runner import STTBenchmarkBlocked, execute_live_stt_benchmark


class _Adapter:
    name = "synthetic-stt"

    def invoke(self, case):
        return dict(case.expected)


def _manifest(**overrides):
    values = {
        "provider": "synthetic-stt",
        "model": "synthetic-model",
        "credential_env_var": "SYNTHETIC_STT_API_KEY",
        "evidence_owner": "security-owner",
        "evidence_source": "https://example.invalid/stt-evidence",
        "verified_on": date(2026, 8, 1),
        "review_due_on": date(2026, 9, 1),
        "no_training_confirmed": True,
        "retention_confirmed": True,
        "residency_confirmed": True,
        "subprocessors_confirmed": True,
        "audio_retention_confirmed": True,
        "approved_for_synthetic_benchmark": True,
    }
    values.update(overrides)
    return STTProviderManifest(**values)


def test_audio_retention_must_be_confirmed():
    with pytest.raises(ValueError, match="not eligible"):
        _manifest(audio_retention_confirmed=False).validate(today=date(2026, 8, 1))


def test_missing_credential_blocks_before_adapter_creation(monkeypatch):
    monkeypatch.delenv("SYNTHETIC_STT_API_KEY", raising=False)
    created = False

    def factory(provider, model, credential):
        nonlocal created
        created = True
        return _Adapter()

    with pytest.raises(STTBenchmarkBlocked, match="missing benchmark credential"):
        execute_live_stt_benchmark(
            _manifest(), validated_cases(), adapter_factory=factory, today=date(2026, 8, 1)
        )
    assert created is False


def test_only_stt_cases_are_executed(monkeypatch):
    monkeypatch.setenv("SYNTHETIC_STT_API_KEY", "synthetic-secret")
    runs = execute_live_stt_benchmark(
        _manifest(),
        validated_cases(),
        adapter_factory=lambda provider, model, credential: _Adapter(),
        today=date(2026, 8, 1),
    )
    assert runs
    assert {run.case_id for run in runs} == {
        case.case_id for case in validated_cases() if case.modality.value == "stt"
    }
