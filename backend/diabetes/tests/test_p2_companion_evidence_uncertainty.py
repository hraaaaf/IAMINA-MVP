from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.services.clinical.companion_change import (
    capture_companion_review_anchor,
    compare_since_last_companion_review,
)
from diabetes.services.clinical.companion_evidence_uncertainty import (
    build_companion_evidence_context,
)
from diabetes.services.clinical.companion_pattern_intelligence import (
    project_personal_pattern_intelligence,
)


class CompanionEvidenceUncertaintyTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="p2-evidence-uncertainty")
        self.now = timezone.now()

    def _observation(
        self,
        *,
        status: str = ClinicalObservationState.STATUS_ACTIVE,
        evidence_strength: str = ClinicalObservationState.EVIDENCE_MODERATE,
        evidence_trend: str = ClinicalObservationState.TREND_INITIAL,
        previous_baseline_delta: float | None = None,
        baseline_delta: float = 40.0,
        baseline_delta_change: float | None = None,
    ) -> ClinicalObservationState:
        previous_evidence_strength = (
            ""
            if evidence_trend == ClinicalObservationState.TREND_INITIAL
            else evidence_strength
        )
        return ClinicalObservationState.objects.create(
            patient=self.patient,
            observation_key="context:stress",
            kind=ClinicalObservationState.KIND_CONTEXT,
            status=status,
            first_seen_at=self.now - timedelta(days=20),
            last_seen_at=self.now - timedelta(days=1),
            status_changed_at=self.now - timedelta(hours=12),
            recurrence_count=1,
            evidence_strength=evidence_strength,
            previous_evidence_strength=previous_evidence_strength,
            evidence_strength_trend=evidence_trend,
            observations=6,
            distinct_days=4,
            observation_median_glucose_mg_dl=165.0,
            window_median_glucose_mg_dl=125.0,
            baseline_delta_mg_dl=baseline_delta,
            previous_baseline_delta_mg_dl=previous_baseline_delta,
            baseline_delta_change_mg_dl=baseline_delta_change,
            evidence_window_days=90,
            evidence_id=ClinicalObservationState.APPROVED_EVIDENCE_ID,
            producer=ClinicalObservationState.APPROVED_PRODUCER,
            context_modifiers={"source_field": "stressed", "recorded_value": "yes"},
            last_evidence_fingerprint="e" * 64,
        )

    def test_pattern_exposes_governed_provenance_and_explicit_missing_data(self):
        self._observation()

        pattern = project_personal_pattern_intelligence(
            patient_id=self.patient.id
        ).patterns[0]
        context = pattern.evidence_context

        self.assertEqual(
            context.provenance.evidence_id,
            "rule.personal-response.repetition.v1",
        )
        self.assertEqual(
            context.provenance.producer,
            ClinicalObservationState.APPROVED_PRODUCER,
        )
        self.assertEqual(
            context.provenance.evidence_maturity,
            "internal_governed_rule",
        )
        self.assertEqual(context.provenance.clinical_authority, "governed_rule")
        self.assertEqual(
            context.provenance.finality_status,
            "versioned_product_rule",
        )
        self.assertIn("at least three matching observations", context.provenance.rule_summary)
        self.assertEqual(context.uncertainty.evidence_density, "moderate")
        self.assertEqual(context.uncertainty.evidence_density_trend, "initial")
        self.assertEqual(
            context.uncertainty.missing_data,
            (
                "previous_evidence_density_not_available",
                "previous_baseline_relative_delta_not_available",
            ),
        )
        self.assertEqual(context.uncertainty.limitations, pattern.limitations)
        self.assertFalse(hasattr(context, "confidence"))

    def test_resolved_pattern_discloses_missing_current_active_evidence(self):
        self._observation(status=ClinicalObservationState.STATUS_INACTIVE)

        pattern = project_personal_pattern_intelligence(
            patient_id=self.patient.id
        ).patterns[0]

        self.assertIn(
            "current_active_evidence_not_available_after_resolution",
            pattern.evidence_context.uncertainty.missing_data,
        )
        self.assertIn(
            "numeric_pattern_values_describe_last_eligible_active_evidence",
            pattern.evidence_context.uncertainty.limitations,
        )

    def test_unknown_change_promotes_reason_to_missing_data(self):
        self._observation()
        capture_companion_review_anchor(patient_id=self.patient.id)

        change = compare_since_last_companion_review(
            patient_id=self.patient.id
        ).changes[0]

        self.assertEqual(change.change_kind, "unknown")
        self.assertEqual(change.missing_data, ("no_eligible_post_review_evidence",))
        self.assertEqual(
            change.evidence_context.uncertainty.missing_data,
            change.missing_data,
        )
        self.assertEqual(
            change.evidence_context.provenance.evidence_id,
            change.evidence_id,
        )
        self.assertEqual(
            change.evidence_context.provenance.clinical_authority,
            "governed_rule",
        )

    def test_provable_change_keeps_missing_data_empty(self):
        observation = self._observation()
        anchor = capture_companion_review_anchor(patient_id=self.patient.id)
        ClinicalObservationState.objects.filter(pk=observation.pk).update(
            last_seen_at=anchor.captured_at + timedelta(days=1),
            last_refreshed_at=anchor.captured_at + timedelta(days=1),
            baseline_delta_mg_dl=45.0,
        )

        change = compare_since_last_companion_review(
            patient_id=self.patient.id
        ).changes[0]

        self.assertEqual(change.change_kind, "persisting")
        self.assertEqual(change.missing_data, ())
        self.assertEqual(change.evidence_context.uncertainty.missing_data, ())

    def test_external_source_maturity_remains_separate_from_product_rule_maturity(self):
        context = build_companion_evidence_context(
            evidence_id="rule.metric.recorded-range-fractions.v1",
            producer="test-governed-producer",
            evidence_density="moderate",
            evidence_density_trend=None,
            missing_data=(),
            limitations=("descriptive_test_only",),
        )

        self.assertEqual(context.provenance.evidence_maturity, "internal_governed_rule")
        self.assertEqual(len(context.provenance.supporting_evidence), 1)
        supporting = context.provenance.supporting_evidence[0]
        self.assertEqual(supporting.evidence_id, "source.ada.2026.section6")
        self.assertEqual(supporting.evidence_maturity, "standard_of_care")
        self.assertEqual(supporting.finality_status, "final")

    def test_candidate_rule_cannot_authorize_material_companion_observation(self):
        with self.assertRaisesRegex(ValueError, "requires governed runtime authority"):
            build_companion_evidence_context(
                evidence_id="rule.metric.gmi-cgm.v1",
                producer="candidate-test",
                evidence_density="moderate",
                evidence_density_trend=None,
                missing_data=(),
                limitations=("candidate_rule_test",),
            )

    def test_narrative_only_rule_cannot_authorize_material_companion_observation(self):
        with self.assertRaisesRegex(ValueError, "requires governed runtime authority"):
            build_companion_evidence_context(
                evidence_id="rule.pattern.explicit-context-observation.v1",
                producer="narrative-test",
                evidence_density="moderate",
                evidence_density_trend=None,
                missing_data=(),
                limitations=("narrative_rule_test",),
            )

    def test_external_source_cannot_become_runtime_rule_authority(self):
        with self.assertRaisesRegex(ValueError, "requires a governed rule"):
            build_companion_evidence_context(
                evidence_id="source.ada.2026.section6",
                producer="source-test",
                evidence_density="moderate",
                evidence_density_trend=None,
                missing_data=(),
                limitations=("source_record_test",),
            )

    def test_unknown_evidence_id_fails_closed(self):
        with self.assertRaisesRegex(KeyError, "Unknown diabetes evidence_id"):
            build_companion_evidence_context(
                evidence_id="rule.does-not-exist.v1",
                producer="unknown-test",
                evidence_density="moderate",
                evidence_density_trend=None,
                missing_data=(),
                limitations=("unknown_rule_test",),
            )

    def test_uncertainty_payload_must_be_immutable_and_unique(self):
        with self.assertRaisesRegex(ValueError, "missing_data must be an immutable tuple"):
            build_companion_evidence_context(
                evidence_id=ClinicalObservationState.APPROVED_EVIDENCE_ID,
                producer=ClinicalObservationState.APPROVED_PRODUCER,
                evidence_density="moderate",
                evidence_density_trend=None,
                missing_data=["missing"],  # type: ignore[arg-type]
                limitations=("bounded",),
            )
        with self.assertRaisesRegex(ValueError, "limitations must not contain duplicates"):
            build_companion_evidence_context(
                evidence_id=ClinicalObservationState.APPROVED_EVIDENCE_ID,
                producer=ClinicalObservationState.APPROVED_PRODUCER,
                evidence_density="moderate",
                evidence_density_trend=None,
                missing_data=(),
                limitations=("bounded", "bounded"),
            )
