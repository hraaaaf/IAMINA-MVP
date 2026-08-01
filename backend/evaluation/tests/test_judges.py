import pytest

from evaluation.contracts import EvaluationCase, Locale, Modality, Severity
from evaluation.dataset import validated_cases
from evaluation.judges import score_case


def test_full_match_scores_100():
    case = validated_cases()[0]
    assert score_case(
        case,
        {"must_refuse_dose": True, "must_escalate": True},
    ) == 100


def test_partial_match_is_proportional():
    case = validated_cases()[0]
    assert score_case(
        case,
        {"must_refuse_dose": True, "must_escalate": False},
    ) == 50


def test_structured_ocr_requires_exact_fields():
    case = next(
        item
        for item in validated_cases()
        if item.case_id == "eval_document_ocr_lab_result"
    )
    assert score_case(case, {"fields": case.expected["fields"]}) == 100
    assert score_case(case, {"fields": {"hba1c_percent": 7.0}}) == 0


def test_case_without_machine_expectations_fails_closed():
    case = EvaluationCase(
        case_id="eval_human_only",
        modality=Modality.TEXT,
        locale=Locale.FR,
        severity=Severity.ROUTINE,
        input_payload={"text": "synthetic"},
        expected={"human_review_only": True},
        tags=("human_review",),
    )
    with pytest.raises(ValueError):
        score_case(case, {})
