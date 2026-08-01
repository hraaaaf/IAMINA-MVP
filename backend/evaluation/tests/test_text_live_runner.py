from datetime import date

import pytest

from evaluation.dataset import validated_cases
from evaluation.text_live_manifest import TextProviderManifest
from evaluation.text_live_runner import TextBenchmarkBlocked, execute_live_text_benchmark


class _Adapter:
    name = "synthetic-provider"

    def invoke(self, case):
        return dict(case.expected)


def _manifest():
    return TextProviderManifest(
        provider="synthetic-provider",
        model="synthetic-model",
        credential_env_var="SYNTHETIC_PROVIDER_API_KEY",
        evidence_owner="security-owner",
        evidence_source="https://example.invalid/provider-evidence",
        verified_on=date(2026, 8, 1),
        review_due_on=date(2026, 9, 1),
        no_training_confirmed=True,
        retention_confirmed=True,
        residency_confirmed=True,
        subprocessors_confirmed=True,
        approved_for_synthetic_benchmark=True,
    )


def test_missing_credential_blocks_before_adapter_creation(monkeypatch):
    monkeypatch.delenv("SYNTHETIC_PROVIDER_API_KEY", raising=False)
    created = False

    def factory(provider, model, credential):
        nonlocal created
        created = True
        return _Adapter()

    with pytest.raises(TextBenchmarkBlocked, match="missing benchmark credential"):
        execute_live_text_benchmark(
            _manifest(), validated_cases(), adapter_factory=factory, today=date(2026, 8, 1)
        )
    assert created is False


def test_only_text_cases_are_sent_to_adapter(monkeypatch):
    monkeypatch.setenv("SYNTHETIC_PROVIDER_API_KEY", "synthetic-secret")
    runs = execute_live_text_benchmark(
        _manifest(),
        validated_cases(),
        adapter_factory=lambda provider, model, credential: _Adapter(),
        today=date(2026, 8, 1),
    )
    assert runs
    assert {run.case_id for run in runs} == {
        case.case_id for case in validated_cases() if case.modality.value == "text"
    }
