from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.services.clinical.companion_pattern_intelligence import (
    project_personal_pattern_intelligence,
)


class CompanionPersonalPatternIntelligenceTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="p2-pattern-intelligence")
        self.other = User.objects.create_user(username="p2-pattern-other")
        self.now = timezone.now()

    def _observation(
        self,
        patient: User,
        *,
        key: str = "context:stress",
        status: str = ClinicalObservationState.STATUS_ACTIVE,
        recurrence_count: int = 1,
        evidence_strength: str = ClinicalObservationState.EVIDENCE_MODERATE,
        evidence_trend: str = ClinicalObservationState.TREND_STABLE,
        baseline_delta: float = 40.0,
        previous_baseline_delta: float | None = None,
        baseline_delta_change: float | None = None,
        context_modifiers: dict[str, str] | None = None,
    ) -> ClinicalObservationState:
        first_seen = self.now - timedelta(days=20)
        last_seen = self.now - timedelta(days=1)
        return ClinicalObservationState.objects.create(
            patient=patient,
            observation_key=key,
            kind=(
                ClinicalObservationState.KIND_MEAL
                if key.startswith("meal:")
                else ClinicalObservationState.KIND_CONTEXT
            ),
            status=status,
            first_seen_at=first_seen,
            last_seen_at=last_seen,
            status_changed_at=self.now - timedelta(hours=12),
            recurrence_count=recurrence_count,
            evidence_strength=evidence_strength,
            previous_evidence_strength=(
                ClinicalObservationState.EVIDENCE_LIMITED
                if evidence_trend == ClinicalObservationState.TREND_STRENGTHENING
                else ""
            ),
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
            context_modifiers=(
                context_modifiers
                if context_modifiers is not None
                else {"source_field": "stressed", "recorded_value": "yes"}
            ),
            last_evidence_fingerprint="a" * 64,
        )

    def test_no_governed_patterns_fails_closed_without_inference(self):
        result = project_personal_pattern_intelligence(patient_id=self.patient.id)

        self.assertEqual(result.status, "no_governed_patterns")
        self.assertEqual(result.patterns, ())
        self.assertIn(
            "absence_of_pattern_is_not_evidence_of_absence_of_clinical_issue",
            result.limitations,
        )

    def test_projection_is_patient_scoped_read_only_and_provenance_preserving(self):
        own = self._observation(self.patient)
        self._observation(self.other, key="context:activity")
        before_refresh = own.last_refreshed_at

        result = project_personal_pattern_intelligence(patient_id=self.patient.id)

        self.assertEqual(result.status, "ready")
        self.assertEqual(len(result.patterns), 1)
        pattern = result.patterns[0]
        self.assertEqual(pattern.observation_key, "context:stress")
        self.assertEqual(pattern.current_state, "active")
        self.assertEqual(pattern.markers, ("persisting",))
        self.assertEqual(pattern.first_observed_at, own.first_seen_at)
        self.assertEqual(pattern.last_observed_at, own.last_seen_at)
        self.assertEqual(pattern.evidence_density, "moderate")
        self.assertEqual(pattern.evidence_id, own.evidence_id)
        self.assertEqual(pattern.producer, own.producer)
        self.assertEqual(
            pattern.recorded_context,
            (("recorded_value", "yes"), ("source_field", "stressed")),
        )
        self.assertFalse(hasattr(pattern, "confidence"))
        self.assertEqual(
            ClinicalObservationState.objects.get(pk=own.pk).last_refreshed_at,
            before_refresh,
        )

    def test_first_observed_and_recurring_are_separate_longitudinal_facts(self):
        row = self._observation(self.patient, recurrence_count=3)

        pattern = project_personal_pattern_intelligence(
            patient_id=self.patient.id
        ).patterns[0]

        self.assertEqual(pattern.first_observed_at, row.first_seen_at)
        self.assertEqual(pattern.recurrence_count, 3)
        self.assertEqual(pattern.markers, ("persisting", "recurring"))

    def test_movement_toward_personal_baseline_is_descriptive_improving_only(self):
        self._observation(
            self.patient,
            baseline_delta=20.0,
            previous_baseline_delta=40.0,
            baseline_delta_change=-20.0,
        )

        pattern = project_personal_pattern_intelligence(
            patient_id=self.patient.id
        ).patterns[0]

        self.assertEqual(
            pattern.baseline_movement,
            "toward_personal_window_baseline",
        )
        self.assertEqual(
            pattern.markers,
            ("persisting", "improving_descriptively"),
        )
        self.assertIn(
            "improving_descriptively_does_not_mean_treatment_response_or_outcome",
            pattern.limitations,
        )
        self.assertIn(
            "no_diagnosis_causality_treatment_response_or_future_prediction",
            pattern.limitations,
        )

    def test_baseline_direction_is_descriptive_not_target_judgment(self):
        self._observation(self.patient, key="context:stress", baseline_delta=30.0)
        self._observation(self.patient, key="context:activity", baseline_delta=-15.0)
        self._observation(self.patient, key="meal:lunch", baseline_delta=0.0)

        patterns = {
            item.observation_key: item
            for item in project_personal_pattern_intelligence(
                patient_id=self.patient.id
            ).patterns
        }

        self.assertEqual(
            patterns["context:stress"].baseline_direction,
            "above_personal_window_baseline",
        )
        self.assertEqual(
            patterns["context:activity"].baseline_direction,
            "below_personal_window_baseline",
        )
        self.assertEqual(
            patterns["meal:lunch"].baseline_direction,
            "aligned_with_personal_window_baseline",
        )
        for pattern in patterns.values():
            self.assertIn(
                "personal_window_baseline_is_descriptive_not_a_clinical_target",
                pattern.limitations,
            )

    def test_resolved_pattern_does_not_claim_current_numeric_state(self):
        self._observation(
            self.patient,
            status=ClinicalObservationState.STATUS_INACTIVE,
            recurrence_count=2,
            baseline_delta=10.0,
            previous_baseline_delta=20.0,
            baseline_delta_change=-10.0,
        )

        pattern = project_personal_pattern_intelligence(
            patient_id=self.patient.id
        ).patterns[0]

        self.assertEqual(pattern.current_state, "resolved")
        self.assertEqual(pattern.markers, ("resolved",))
        self.assertIn(
            "numeric_pattern_values_describe_last_eligible_active_evidence",
            pattern.limitations,
        )

    def test_evidence_density_trend_remains_repeatability_not_confidence(self):
        self._observation(
            self.patient,
            evidence_strength=ClinicalObservationState.EVIDENCE_MODERATE,
            evidence_trend=ClinicalObservationState.TREND_STRENGTHENING,
        )

        pattern = project_personal_pattern_intelligence(
            patient_id=self.patient.id
        ).patterns[0]

        self.assertEqual(pattern.evidence_density, "moderate")
        self.assertEqual(pattern.evidence_density_trend, "strengthening")
        self.assertIn(
            "evidence_density_is_repeatability_not_probability_or_clinical_confidence",
            pattern.limitations,
        )

    def test_inconsistent_baseline_history_fails_closed(self):
        self._observation(
            self.patient,
            baseline_delta=20.0,
            previous_baseline_delta=40.0,
            baseline_delta_change=5.0,
        )

        with self.assertRaisesRegex(ValueError, "baseline change is internally inconsistent"):
            project_personal_pattern_intelligence(patient_id=self.patient.id)

    def test_ungoverned_runtime_vocabulary_fails_closed(self):
        row = self._observation(self.patient)
        ClinicalObservationState.objects.filter(pk=row.pk).update(
            evidence_strength="very_strong"
        )

        with self.assertRaisesRegex(ValueError, "unapproved evidence density"):
            project_personal_pattern_intelligence(patient_id=self.patient.id)

    def test_noncanonical_window_fails_closed(self):
        row = self._observation(self.patient)
        ClinicalObservationState.objects.filter(pk=row.pk).update(
            evidence_window_days=30
        )

        with self.assertRaisesRegex(ValueError, "canonical evidence window"):
            project_personal_pattern_intelligence(patient_id=self.patient.id)

    def test_invalid_patient_identity_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "patient_id must be a positive integer"):
            project_personal_pattern_intelligence(patient_id=0)
        with self.assertRaisesRegex(ValueError, "patient_id must be a positive integer"):
            project_personal_pattern_intelligence(patient_id=True)
