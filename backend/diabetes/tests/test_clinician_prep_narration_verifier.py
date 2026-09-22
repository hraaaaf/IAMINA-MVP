from datetime import timedelta

from django.utils import timezone

from core.contracts.truth import TruthKind
from diabetes.services.clinical.clinician_prep_decision import (
    resolve_clinician_prep_from_brief,
)
from diabetes.services.clinical.clinician_prep_narration_verifier import (
    verified_clinician_prep_narration_or_fallback,
    verify_clinician_prep_narration,
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


def test_clinician_prep_deterministic_copy_passes():
    resolution = _resolution()
    assert resolution is not None
    check = verify_clinician_prep_narration(
        resolution.decision,
        resolution.reply,
        resolution.reply,
    )
    assert check.passed


def test_clinician_prep_any_altered_copy_fails_closed_to_exact_fallback():
    resolution = _resolution()
    assert resolution is not None

    altered = (
        "Tu as clairement une hypoglycémie, demande au médecin de changer ton traitement.",
        "Voici une reformulation apparemment anodine mais différente.",
        "",
    )
    for candidate in altered:
        assert verified_clinician_prep_narration_or_fallback(
            resolution.decision,
            candidate,
            resolution.reply,
        ) == resolution.reply


def test_clinician_prep_wrong_rule_family_is_rejected():
    resolution = _resolution()
    assert resolution is not None
    other = resolution.decision.__class__(
        intent=resolution.decision.intent,
        authority_level=resolution.decision.authority_level,
        decision=resolution.decision.decision,
        rule_id="diabetes.food.permission",
        rule_version="1",
        allowed_actions=resolution.decision.allowed_actions,
        forbidden_actions=resolution.decision.forbidden_actions,
        evidence_refs=resolution.decision.evidence_refs,
        limitations=resolution.decision.limitations,
        language=resolution.decision.language,
    )
    check = verify_clinician_prep_narration(other, resolution.reply, resolution.reply)
    assert not check.passed
    assert check.violations == ("wrong_rule_family",)
