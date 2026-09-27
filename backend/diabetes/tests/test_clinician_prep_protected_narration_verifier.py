from datetime import timedelta

from django.utils import timezone

from core.contracts.truth import TruthKind
from diabetes.services.clinical.clinician_prep_decision import (
    resolve_clinician_prep_from_brief,
)
from diabetes.services.clinical.clinician_prep_protected_narration_verifier import (
    verified_clinician_prep_protected_narration_or_fallback,
    verify_clinician_prep_protected_narration,
)
from diabetes.services.clinical.consultation_brief_contract import (
    ConsultationBriefEnvelope,
    ConsultationComparisonBasis,
    ConsultationEvidenceItem,
    ConsultationNextStep,
)


def _resolution():
    end = timezone.now()
    brief = ConsultationBriefEnvelope(
        window_start=end - timedelta(days=14),
        window_end=end,
        comparison_basis=ConsultationComparisonBasis.CURRENT_SNAPSHOT,
        items=(
            ConsultationEvidenceItem(
                key="recorded_glucose.latest_mg_dl",
                value=142.0,
                unit="mg/dL",
                truth_kind=TruthKind.OBSERVED_FACT,
                source="diabetes.log-entry",
                source_version="consultation-companion-assembler.v1",
                allowed_next_step=ConsultationNextStep.MONITOR,
            ),
        ),
    )
    return resolve_clinician_prep_from_brief(
        "Aide-moi à préparer les questions pour mon médecin.",
        brief,
        language="fr",
    )


def test_benign_nonclinical_wrapper_preserves_exact_body():
    resolution = _resolution()
    assert resolution is not None
    candidate = f"D'accord, on fait simple. {resolution.reply}"

    check = verify_clinician_prep_protected_narration(
        resolution.decision,
        candidate,
        resolution.reply,
    )

    assert check.passed
    assert check.violations == ()


def test_exact_body_without_wrapper_remains_valid():
    resolution = _resolution()
    assert resolution is not None

    check = verify_clinician_prep_protected_narration(
        resolution.decision,
        resolution.reply,
        resolution.reply,
    )

    assert check.passed


def test_clinical_content_added_in_wrapper_fails_closed():
    resolution = _resolution()
    assert resolution is not None
    candidate = f"Ton glucose semble stable. {resolution.reply}"

    check = verify_clinician_prep_protected_narration(
        resolution.decision,
        candidate,
        resolution.reply,
    )

    assert not check.passed
    assert check.violations == ("wrapper_contains_clinical_content",)
    assert verified_clinician_prep_protected_narration_or_fallback(
        resolution.decision,
        candidate,
        resolution.reply,
    ) == resolution.reply


def test_arabic_clinical_content_added_in_wrapper_fails_closed():
    resolution = _resolution()
    assert resolution is not None
    candidate = f"السكر مستقر. {resolution.reply}"

    check = verify_clinician_prep_protected_narration(
        resolution.decision,
        candidate,
        resolution.reply,
    )

    assert not check.passed
    assert "wrapper_contains_clinical_content" in check.violations


def test_number_added_in_wrapper_fails_closed():
    resolution = _resolution()
    assert resolution is not None
    candidate = f"Je te fais 2 points rapides. {resolution.reply}"

    check = verify_clinician_prep_protected_narration(
        resolution.decision,
        candidate,
        resolution.reply,
    )

    assert not check.passed
    assert check.violations == ("wrapper_contains_number",)


def test_missing_or_duplicated_body_fails_closed():
    resolution = _resolution()
    assert resolution is not None

    missing = verify_clinician_prep_protected_narration(
        resolution.decision,
        "D'accord, on fait simple.",
        resolution.reply,
    )
    duplicated = verify_clinician_prep_protected_narration(
        resolution.decision,
        f"{resolution.reply} {resolution.reply}",
        resolution.reply,
    )

    assert missing.violations == ("protected_body_not_present_exactly_once",)
    assert duplicated.violations == ("protected_body_not_present_exactly_once",)


def test_long_wrapper_fails_closed():
    resolution = _resolution()
    assert resolution is not None
    wrapper = "Très bien, " + ("on garde ça simple et naturel, " * 8)
    candidate = wrapper + resolution.reply

    check = verify_clinician_prep_protected_narration(
        resolution.decision,
        candidate,
        resolution.reply,
    )

    assert not check.passed
    assert "wrapper_too_long" in check.violations
