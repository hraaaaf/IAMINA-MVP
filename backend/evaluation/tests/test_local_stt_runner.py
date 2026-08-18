import hashlib
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


def _case(
    case_id: str,
    modality: Modality,
    *,
    fixture: str,
    digest: str,
) -> EvaluationCase:
    return EvaluationCase(
        case_id=case_id,
        modality=modality,
        locale=Locale.FR,
        severity=Severity.ROUTINE,
        input_payload={"audio_fixture": fixture, "audio_sha256": digest},
        expected={"transcript": "bonjour"},
        tags=("synthetic",),
    )


def test_local_stt_runner_executes_only_integrity_pinned_stt(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    audio = tmp_path / "fixtures" / "synthetic.wav"
    audio.parent.mkdir()
    audio.write_bytes(b"RIFF-controlled-synthetic-audio")
    digest = hashlib.sha256(audio.read_bytes()).hexdigest()
    created = []

    def factory(engine, model, version):
        created.append((engine, model, version))
        return DummySTTAdapter()

    runs = execute_local_stt_benchmark(
        _manifest(),
        (
            _case(
                "eval_voice",
                Modality.STT,
                fixture="fixtures/synthetic.wav",
                digest=digest,
            ),
            _case(
                "eval_text",
                Modality.TEXT,
                fixture="fixtures/synthetic.wav",
                digest=digest,
            ),
        ),
        adapter_factory=factory,
        today=date(2026, 8, 18),
    )

    assert [run.case_id for run in runs] == ["eval_voice"]
    assert created == [("on-device-stt", "synthetic-model-id", "test-version")]


def test_local_stt_runner_fails_without_stt_cases(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(LocalSTTBenchmarkBlocked):
        execute_local_stt_benchmark(
            _manifest(),
            (
                _case(
                    "eval_text",
                    Modality.TEXT,
                    fixture="fixtures/missing.wav",
                    digest="0" * 64,
                ),
            ),
            adapter_factory=lambda *_args: DummySTTAdapter(),
            today=date(2026, 8, 18),
        )


def test_local_stt_runner_rejects_transcript_only_case_before_adapter_creation():
    case = EvaluationCase(
        case_id="eval_voice_transcript_only",
        modality=Modality.STT,
        locale=Locale.MIXED,
        severity=Severity.HIGH,
        input_payload={"transcript_reference": "sokkar tay7 بزاف, I feel dizzy"},
        expected={"required_concepts": ["low glucose", "dizziness"]},
        tags=("synthetic", "stt"),
    )
    created = []

    with pytest.raises(LocalSTTBenchmarkBlocked, match="audio_fixture"):
        execute_local_stt_benchmark(
            _manifest(),
            (case,),
            adapter_factory=lambda *_args: created.append(True) or DummySTTAdapter(),
            today=date(2026, 8, 18),
        )

    assert created == []


def test_local_stt_runner_rejects_tampered_fixture(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    audio = tmp_path / "fixtures" / "synthetic.wav"
    audio.parent.mkdir()
    audio.write_bytes(b"first")
    original_digest = hashlib.sha256(audio.read_bytes()).hexdigest()
    audio.write_bytes(b"tampered")

    with pytest.raises(LocalSTTBenchmarkBlocked, match="SHA-256 mismatch"):
        execute_local_stt_benchmark(
            _manifest(),
            (
                _case(
                    "eval_voice",
                    Modality.STT,
                    fixture="fixtures/synthetic.wav",
                    digest=original_digest,
                ),
            ),
            adapter_factory=lambda *_args: DummySTTAdapter(),
            today=date(2026, 8, 18),
        )


def test_local_stt_runner_rejects_path_traversal_before_file_access():
    with pytest.raises(LocalSTTBenchmarkBlocked, match="repository-relative"):
        execute_local_stt_benchmark(
            _manifest(),
            (
                _case(
                    "eval_voice",
                    Modality.STT,
                    fixture="../outside.wav",
                    digest="0" * 64,
                ),
            ),
            adapter_factory=lambda *_args: DummySTTAdapter(),
            today=date(2026, 8, 18),
        )
