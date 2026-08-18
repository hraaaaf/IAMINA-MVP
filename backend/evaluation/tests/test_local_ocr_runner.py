from datetime import date, timedelta

import pytest

from evaluation.contracts import EvaluationCase, Locale, Modality, Severity
from evaluation.local_ocr_manifest import LocalOCRManifest
from evaluation.local_ocr_runner import (
    LocalOCRBenchmarkBlocked,
    execute_local_ocr_benchmark,
)


class DummyOCRAdapter:
    name = "local-ocr-test"

    def invoke(self, case):
        return {"case": case.case_id}


def _manifest(*modalities: str) -> LocalOCRManifest:
    today = date(2026, 8, 18)
    return LocalOCRManifest(
        engine="paddleocr",
        model="synthetic-model-id",
        implementation_version="test-version",
        evidence_source="controlled-local-fixture",
        verified_on=today,
        review_due_on=today + timedelta(days=30),
        approved_modalities=modalities,
        approved_for_synthetic_benchmark=True,
    )


def _case(case_id: str, modality: Modality) -> EvaluationCase:
    return EvaluationCase(
        case_id=case_id,
        modality=modality,
        locale=Locale.FR,
        severity=Severity.ROUTINE,
        input_payload={"fixture": "synthetic.png"},
        expected={"text": "100"},
        tags=("synthetic",),
    )


def test_local_ocr_manifest_rejects_meal_vision():
    with pytest.raises(ValueError, match="document/glucometer OCR only"):
        _manifest("meal_vision").validate(today=date(2026, 8, 18))


def test_local_ocr_runner_filters_to_approved_ocr_without_credentials():
    created = []

    def factory(engine, model, version):
        created.append((engine, model, version))
        return DummyOCRAdapter()

    runs = execute_local_ocr_benchmark(
        _manifest("document_ocr", "glucometer_ocr"),
        (
            _case("eval_doc", Modality.DOCUMENT_OCR),
            _case("eval_meter", Modality.GLUCOMETER_OCR),
            _case("eval_meal", Modality.MEAL_VISION),
        ),
        adapter_factory=factory,
        today=date(2026, 8, 18),
    )

    assert [run.case_id for run in runs] == ["eval_doc", "eval_meter"]
    assert created == [("paddleocr", "synthetic-model-id", "test-version")]


def test_local_ocr_runner_fails_when_no_approved_cases_exist():
    with pytest.raises(LocalOCRBenchmarkBlocked):
        execute_local_ocr_benchmark(
            _manifest("document_ocr"),
            (_case("eval_meal", Modality.MEAL_VISION),),
            adapter_factory=lambda *_args: DummyOCRAdapter(),
            today=date(2026, 8, 18),
        )
