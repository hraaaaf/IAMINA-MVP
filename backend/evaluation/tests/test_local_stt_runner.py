from datetime import date, timedelta

import pytest

from evaluation.contracts import EvaluationCase, Locale, Modality, Severity
from evaluation.local_stt_manifest import LocalSTTManifest
from evaluation.local_stt_runner import (
    LocalSTTBenchmarkBlocked,
    execute_local_stt_benchmark,
)


class DummySTTAdapter:
    name = "local-stt-test"

    def invoke(self, case):
        return {"transcript": case.expected.get("transcript", "")}


def _manifest() -> LocalSTTManifest:
    today = date(2026, 8, 18)
    return LocalSTTManifest(
        engine="on-device-stt",
        model="synthetic-model-id",
        implementation_version="test-version",
        evidence_source="controlled-local-fixture",
        verified_on=today,
        review_due_on=today + timedelta(days=30),
        approved_for_synthetic_benchmark=True,
    )


def _case(case_id: str, modality: Modality) -> EvaluationCase:
    return EvaluationCase(
        case_id=case_id,
        modality=modality,
        locale=Locale.FR,
        severity=Severity.ROUTINE,
        input_payload={"fixture": "synthetic.wav"},
        expected={"transcript": "bonjour"},
        tags=("synthetic",),
    )


def test_local_stt_runner_executes_only_stt_without_credentials():
    created = []

    def factory(engine, model, version):
        created.append((engine, model, version))
        return DummySTTAdapter()

    runs = execute_local_stt_benchmark(
        _manifest(),
        (
            _case("eval_voice", Modality.STT),
            _case("eval_text", Modality.TEXT),
        ),
        adapter_factory=factory,
        today=date(2026, 8, 18),
    )

    assert [run.case_id for run in runs] == ["eval_voice"]
    assert created == [("on-device-stt", "synthetic-model-id", "test-version")]


def test_local_stt_runner_fails_without_stt_cases():
    with pytest.raises(LocalSTTBenchmarkBlocked):
        execute_local_stt_benchmark(
            _manifest(),
            (_case("eval_text", Modality.TEXT),),
            adapter_factory=lambda *_args: DummySTTAdapter(),
            today=date(2026, 8, 18),
        )
