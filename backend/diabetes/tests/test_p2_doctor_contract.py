from datetime import timedelta

import pytest
from django.utils import timezone

from core.contracts.truth import TruthKind
from diabetes.services.clinical.consultation_brief_contract import (
    CONSULTATION_BRIEF_SCHEMA_VERSION,
    ConsultationAuthority,
    ConsultationBriefEnvelope,
    ConsultationChangeKind,
    ConsultationComparisonBasis,
    ConsultationEvidenceDensity,
    ConsultationEvidenceItem,
    ConsultationNarrationPolicy,
    ConsultationNextStep,
    ConsultationReviewCheckpoint,
)


def _now_window():
    end = timezone.now()
    return end - timedelta(days=14), end


def _deterministic_item(**overrides):
    values = {
        "key": "personal_response.context.stress",
        "value": {"status": "active", "observations": 4},
        "truth_kind": TruthKind.DETERMINISTIC_DERIVATION,
        "source": "diabetes.personal_response.v1",
        "source_version": "personal-response.v1",
        "evidence_id": "rule.personal-response.repetition.v1",
        "evidence_window_days": 90,
        "evidence_density": ConsultationEvidenceDensity.MODERATE,
        "limitations": ("observational_association_only",),
        "allowed_next_step": ConsultationNextStep.PREPARE_CLINICIAN_DISCUSSION,
    }
    values.update(overrides)
    return ConsultationEvidenceItem(**values)


def test_contract_accepts_observed_fact_and_governed_derivation_only():
    start, end = _now_window()
    observed = ConsultationEvidenceItem(
        key="journal.glucose.latest",
        value=142,
        unit="mg/dL",
        truth_kind=TruthKind.OBSERVED_FACT,
        source="journal.log",
        source_version="journal.sync.v1",
        allowed_next_step=ConsultationNextStep.MONITOR,
    )
    derived = _deterministic_item()

    brief = ConsultationBriefEnvelope(
        window_start=start,
        window_end=end,
        comparison_basis=ConsultationComparisonBasis.CURRENT_SNAPSHOT,
        items=(observed, derived),
        missing_data=("no_explicit_prior_review_checkpoint",),
        limitations=("review_support_not_diagnosis_or_treatment_authority",),
    )

    assert brief.schema_version == CONSULTATION_BRIEF_SCHEMA_VERSION
    assert brief.authority is ConsultationAuthority.REVIEW_SUPPORT_ONLY
    assert (
        brief.narration_policy
        is ConsultationNarrationPolicy.APPROVED_STRUCTURED_FIELDS_ONLY
    )
    assert brief.can_be_narrated_by_model is True
    assert brief.has_since_review_claims is False


@pytest.mark.parametrize(
    "truth_kind",
    [
        TruthKind.USER_CLAIM,
        TruthKind.PREFERENCE,
        TruthKind.CONVERSATIONAL_STATE,
        TruthKind.HEURISTIC_INFERENCE,
        TruthKind.MODEL_INFERENCE,
    ],
)
def test_contract_rejects_unapproved_truth_kinds(truth_kind):
    with pytest.raises(ValueError, match="not authorized"):
        ConsultationEvidenceItem(
            key="unsafe.input",
            value="unverified",
            truth_kind=truth_kind,
            source="companion",
            source_version="v1",
        )


def test_deterministic_derivation_requires_evidence_provenance():
    with pytest.raises(ValueError, match="require an evidence_id"):
        _deterministic_item(evidence_id=None)


def test_deterministic_derivation_rejects_unknown_evidence_id():
    with pytest.raises(ValueError, match="evidence_id is not registered"):
        _deterministic_item(evidence_id="rule.unknown.v1")


def test_deterministic_derivation_rejects_external_source_record():
    with pytest.raises(ValueError, match="must reference a product rule"):
        _deterministic_item(evidence_id="source.ada.2026.section6")


@pytest.mark.parametrize(
    "evidence_id",
    [
        "rule.metric.gmi-cgm.v1",
        "rule.pattern.night-low-later-morning-high.v1",
    ],
)
def test_deterministic_derivation_rejects_non_governed_rule_authority(evidence_id):
    with pytest.raises(ValueError, match="requires governed_rule clinical authority"):
        _deterministic_item(evidence_id=evidence_id)


def test_observed_fact_cannot_masquerade_as_governed_derivation():
    with pytest.raises(ValueError, match="must not masquerade"):
        ConsultationEvidenceItem(
            key="journal.glucose.latest",
            value=142,
            truth_kind=TruthKind.OBSERVED_FACT,
            source="journal.log",
            source_version="journal.sync.v1",
            evidence_id="rule.personal-response.repetition.v1",
        )


def test_evidence_density_is_not_available_for_plain_observed_fact():
    with pytest.raises(ValueError, match="reserved for approved deterministic"):
        ConsultationEvidenceItem(
            key="journal.glucose.latest",
            value=142,
            truth_kind=TruthKind.OBSERVED_FACT,
            source="journal.log",
            source_version="journal.sync.v1",
            evidence_density=ConsultationEvidenceDensity.STRONG,
        )


def test_since_review_change_claim_fails_closed_without_checkpoint():
    start, end = _now_window()
    item = _deterministic_item(
        change_kind=ConsultationChangeKind.NEW_SINCE_REVIEW,
    )

    with pytest.raises(ValueError, match="explicit review checkpoint"):
        ConsultationBriefEnvelope(
            window_start=start,
            window_end=end,
            comparison_basis=ConsultationComparisonBasis.CURRENT_SNAPSHOT,
            items=(item,),
        )

    with pytest.raises(ValueError, match="requires an explicit review checkpoint"):
        ConsultationBriefEnvelope(
            window_start=start,
            window_end=end,
            comparison_basis=ConsultationComparisonBasis.SINCE_REVIEW_CHECKPOINT,
            items=(item,),
        )


def test_explicit_review_checkpoint_unlocks_bounded_change_semantics():
    start, end = _now_window()
    checkpoint = ConsultationReviewCheckpoint(
        reviewed_at=start - timedelta(days=1),
        source="clinician.review_checkpoint",
    )
    item = _deterministic_item(
        change_kind=ConsultationChangeKind.PERSISTING_SINCE_REVIEW,
    )

    brief = ConsultationBriefEnvelope(
        window_start=start,
        window_end=end,
        comparison_basis=ConsultationComparisonBasis.SINCE_REVIEW_CHECKPOINT,
        review_checkpoint=checkpoint,
        items=(item,),
    )

    assert brief.has_since_review_claims is True
    assert brief.review_checkpoint == checkpoint


def test_current_snapshot_cannot_carry_checkpoint_or_imply_review_history():
    start, end = _now_window()
    checkpoint = ConsultationReviewCheckpoint(
        reviewed_at=start - timedelta(days=1),
        source="clinician.review_checkpoint",
    )

    with pytest.raises(ValueError, match="must not carry a review checkpoint"):
        ConsultationBriefEnvelope(
            window_start=start,
            window_end=end,
            comparison_basis=ConsultationComparisonBasis.CURRENT_SNAPSHOT,
            review_checkpoint=checkpoint,
            items=(_deterministic_item(),),
        )


def test_invalid_or_future_review_checkpoint_is_rejected():
    start, end = _now_window()
    with pytest.raises(ValueError, match="must precede the brief window end"):
        ConsultationBriefEnvelope(
            window_start=start,
            window_end=end,
            comparison_basis=ConsultationComparisonBasis.SINCE_REVIEW_CHECKPOINT,
            review_checkpoint=ConsultationReviewCheckpoint(
                reviewed_at=end + timedelta(minutes=1),
                source="clinician.review_checkpoint",
            ),
            items=(_deterministic_item(),),
        )


def test_naive_datetimes_are_rejected_before_temporal_comparison():
    start, end = _now_window()
    naive_start = start.replace(tzinfo=None)
    naive_review = (start - timedelta(days=1)).replace(tzinfo=None)

    with pytest.raises(ValueError, match="window datetimes must be timezone-aware"):
        ConsultationBriefEnvelope(
            window_start=naive_start,
            window_end=end,
            comparison_basis=ConsultationComparisonBasis.CURRENT_SNAPSHOT,
            items=(),
        )

    with pytest.raises(ValueError, match="reviewed_at must be timezone-aware"):
        ConsultationReviewCheckpoint(
            reviewed_at=naive_review,
            source="clinician.review_checkpoint",
        )


def test_contract_has_no_treatment_change_action_class():
    allowed = {member.value for member in ConsultationNextStep}
    assert allowed == {
        "MONITOR",
        "COLLECT_MISSING_DATA",
        "PREPARE_CLINICIAN_DISCUSSION",
    }
    with pytest.raises(ValueError):
        ConsultationNextStep("CHANGE_TREATMENT")
    with pytest.raises(ValueError):
        ConsultationNextStep("CALCULATE_DOSE")


def test_contract_has_no_numeric_confidence_field():
    item_fields = set(ConsultationEvidenceItem.__dataclass_fields__)
    brief_fields = set(ConsultationBriefEnvelope.__dataclass_fields__)

    assert "confidence" not in item_fields
    assert "confidence_score" not in item_fields
    assert "confidence" not in brief_fields
    assert "confidence_score" not in brief_fields
    assert "evidence_density" in item_fields


def test_empty_current_snapshot_can_expose_missing_data_without_fabrication():
    start, end = _now_window()
    brief = ConsultationBriefEnvelope(
        window_start=start,
        window_end=end,
        comparison_basis=ConsultationComparisonBasis.CURRENT_SNAPSHOT,
        items=(),
        missing_data=("insufficient_approved_evidence", "no_review_checkpoint"),
        limitations=("no_change_since_review_claim_without_checkpoint",),
    )

    assert brief.items == ()
    assert "insufficient_approved_evidence" in brief.missing_data
    assert brief.has_since_review_claims is False
