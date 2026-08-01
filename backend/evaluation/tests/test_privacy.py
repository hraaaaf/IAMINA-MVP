import pytest

from evaluation.contracts import EvaluationCase, Locale, Modality, Severity
from evaluation.privacy import assert_fixture_privacy, identity_findings


def _case(payload):
    return EvaluationCase(
        case_id="eval_privacy_probe",
        modality=Modality.TEXT,
        locale=Locale.FR,
        severity=Severity.ROUTINE,
        input_payload=payload,
        expected={"safe": True},
        tags=("privacy",),
    )


def test_identity_categories_are_detected_without_exposing_values():
    case = _case(
        {
            "email": "patient@example.test",
            "phone": "+212612345678",
            "id": "AB123456",
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
        }
    )
    assert identity_findings(case) == ("email", "moroccan_id", "phone", "uuid")
    with pytest.raises(ValueError, match="email, moroccan_id, phone, uuid"):
        assert_fixture_privacy(case)


def test_synthetic_non_identifying_fixture_passes():
    assert_fixture_privacy(_case({"text": "synthetic glucose reading 54 mg/dL"}))
