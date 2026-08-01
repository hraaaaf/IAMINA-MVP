from datetime import date

import pytest

from evaluation.dataset import validated_cases
from evaluation.vision_live_manifest import VisionProviderManifest
from evaluation.vision_live_runner import VisionBenchmarkBlocked, execute_live_vision_benchmark


class _Adapter:
    name = "synthetic-vision"

    def invoke(self, case):
        return dict(case.expected)


def _manifest(**overrides):
    values = {
        "provider": "synthetic-vision",
        "model": "synthetic-model",
        "credential_env_var": "SYNTHETIC_VISION_API_KEY",
        "evidence_owner": "security-owner",
        "evidence_source": "https://example.invalid/vision-evidence",
        "verified_on": date(2026, 8, 1),
        "review_due_on": date(2026, 9, 1),
        "no_training_confirmed": True,
        "retention_confirmed": True,
        "residency_confirmed": True,
        "subprocessors_confirmed": True,
        "image_retention_confirmed": True,
        "approved_modalities": ("document_ocr", "glucometer_ocr", "meal_vision"),
        "approved_for_synthetic_benchmark": True,
    }
    values.update(overrides)
    return VisionProviderManifest(**values)


def test_all_vision_modalities_must_be_approved():
    with pytest.raises(ValueError, match="every vision benchmark modality"):
        _manifest(approved_modalities=("document_ocr",)).validate(today=date(2026, 8, 1))


def test_missing_credential_blocks_before_adapter_creation(monkeypatch):
    monkeypatch.delenv("SYNTHETIC_VISION_API_KEY", raising=False)
    created = False

    def factory(provider, model, credential):
        nonlocal created
        created = True
        return _Adapter()

    with pytest.raises(VisionBenchmarkBlocked, match="missing benchmark credential"):
        execute_live_vision_benchmark(
            _manifest(), validated_cases(), adapter_factory=factory, today=date(2026, 8, 1)
        )
    assert created is False


def test_only_vision_and_ocr_cases_are_executed(monkeypatch):
    monkeypatch.setenv("SYNTHETIC_VISION_API_KEY", "synthetic-secret")
    runs = execute_live_vision_benchmark(
        _manifest(),
        validated_cases(),
        adapter_factory=lambda provider, model, credential: _Adapter(),
        today=date(2026, 8, 1),
    )
    assert runs
    assert {run.case_id for run in runs} == {
        case.case_id
        for case in validated_cases()
        if case.modality.value in {"document_ocr", "glucometer_ocr", "meal_vision"}
    }
