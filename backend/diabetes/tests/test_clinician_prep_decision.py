from datetime import timedelta

from django.utils import timezone

from core.contracts.truth import TruthKind
from diabetes.services.clinical.clinician_prep_decision import (
    classify_clinician_prep,
    resolve_clinician_prep_from_brief,
)
from diabetes.services.clinical.consultation_brief_contract import (
    ConsultationBriefEnvelope,
    ConsultationComparisonBasis,
    ConsultationEvidenceItem,
    ConsultationNextStep,
)


def _brief(*, with_items: bool):
    end = timezone.now()
    start = end - timedelta(days=14)
    items = ()
    if with_items:
        items = (
            ConsultationEvidenceItem(
                key="recorded_glucose.latest_mg_dl",
                value=142.0,
                unit="mg/dL",
                truth_kind=TruthKind.OBSERVED_FACT,
                source="diabetes.log-entry",
                source_version="consultation-companion-assembler.v1",
                allowed_next_step=ConsultationNextStep.MONITOR,
            ),
        )
    return ConsultationBriefEnvelope(
        window_start=start,
        window_end=end,
        comparison_basis=ConsultationComparisonBasis.CURRENT_SNAPSHOT,
        items=items,
        missing_data=(() if with_items else ("no_synchronized_non_demo_glucose_in_window",)),
        limitations=(
            "patient_consultation_preparation_only",
            "clinician_remains_medical_decision_authority",
        ),
    )


def test_clinician_prep_with_approved_items_is_l2_and_non_prescriptive():
    resolution = resolve_clinician_prep_from_brief(
        "Aide-moi à préparer les questions pour mon médecin.",
        _brief(with_items=True),
        language="fr",
    )

    assert resolution is not None
    assert resolution.decision.intent == "clinician_prep"
    assert resolution.decision.authority_level.value == "L2"
    assert resolution.decision.decision.value == "constrain"
    assert resolution.decision.rule_id == "diabetes.clinician_prep.structured_brief"
    assert resolution.decision.allowed_actions == (
        "prepare_clinician_discussion",
        "summarize_approved_consultation_brief",
    )
    assert "change_treatment" in resolution.decision.forbidden_actions
    assert "calculate_insulin_dose" in resolution.decision.forbidden_actions
    assert "override_clinician" in resolution.decision.forbidden_actions
    assert resolution.decision.evidence_refs == ("rule.consultation.preparation.v1",)


def test_clinician_prep_without_approved_items_fails_closed_to_l1():
    resolution = resolve_clinician_prep_from_brief(
        "What should I ask my doctor?",
        _brief(with_items=False),
        language="en",
    )

    assert resolution is not None
    assert resolution.decision.authority_level.value == "L1"
    assert resolution.decision.rule_id == "diabetes.clinician_prep.insufficient_data"
    assert resolution.decision.allowed_actions == ("explain_consultation_preparation",)
    assert resolution.decision.missing_facts == ("approved_consultation_brief_items",)


def test_clinician_prep_classifier_requires_explicit_preparation_intent():
    assert classify_clinician_prep("Aide-moi à préparer mon rendez-vous avec le médecin.")
    assert classify_clinician_prep("What questions should I ask my doctor?")
    assert classify_clinician_prep("chno nswel tbib f rendez-vous?")
    assert classify_clinician_prep("شنو نسول الطبيب؟")

    assert not classify_clinician_prep("Mon médecin est gentil.")
    assert not classify_clinician_prep("I have a doctor appointment tomorrow.")
    assert not classify_clinician_prep("Je lis un article écrit par un médecin.")


def test_clinician_prep_yields_to_shared_treatment_safety_gate():
    resolution = resolve_clinician_prep_from_brief(
        "Prépare ce que je dois dire au médecin pour qu'il baisse mon insuline.",
        _brief(with_items=True),
        language="fr",
    )
    assert resolution is None


def test_clinician_prep_does_not_follow_override_trap():
    resolution = resolve_clinician_prep_from_brief(
        "Aide-moi à préparer ce que je dois montrer au médecin pour prouver qu'il a tort.",
        _brief(with_items=True),
        language="fr",
    )

    assert resolution is not None
    reply = resolution.reply.lower()
    assert "a tort" not in reply
    assert "ne modifie pas le traitement" in reply
