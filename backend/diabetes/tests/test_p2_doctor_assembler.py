from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from core.contracts.truth import TruthKind
from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.models.entry import LogEntry
from diabetes.models.proactive_insight import ProactiveInsightState
from diabetes.services.clinical.consultation_brief_assembler import (
    assemble_consultation_brief,
)
from diabetes.services.clinical.consultation_brief_contract import (
    ConsultationChangeKind,
    ConsultationComparisonBasis,
    ConsultationEvidenceDensity,
    ConsultationNextStep,
    ConsultationReviewCheckpoint,
)


class ConsultationBriefAssemblerTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="p2-doctor-assembler")
        self.other = User.objects.create_user(username="p2-doctor-other")
        self.now = timezone.now()
        self.start = self.now - timedelta(days=14)

    def _log(
        self,
        patient: User,
        *,
        days_ago: int,
        glucose: int,
        source: str = "manual",
    ) -> LogEntry:
        return LogEntry.objects.create(
            patient=patient,
            logged_at=self.now - timedelta(days=days_ago),
            blood_sugar=glucose,
            source=source,
        )

    def _observation(
        self,
        patient: User,
        *,
        key: str = "context:stress",
        status: str = ClinicalObservationState.STATUS_ACTIVE,
        first_seen_at=None,
        last_seen_at=None,
        status_changed_at=None,
        evidence_strength: str = ClinicalObservationState.EVIDENCE_MODERATE,
    ) -> ClinicalObservationState:
        first_seen_at = first_seen_at or self.now - timedelta(days=10)
        last_seen_at = last_seen_at or self.now - timedelta(days=1)
        status_changed_at = status_changed_at or first_seen_at
        return ClinicalObservationState.objects.create(
            patient=patient,
            observation_key=key,
            kind=ClinicalObservationState.KIND_CONTEXT,
            status=status,
            first_seen_at=first_seen_at,
            last_seen_at=last_seen_at,
            status_changed_at=status_changed_at,
            recurrence_count=1,
            evidence_strength=evidence_strength,
            previous_evidence_strength="",
            evidence_strength_trend=ClinicalObservationState.TREND_INITIAL,
            observations=4,
            distinct_days=3,
            observation_median_glucose_mg_dl=165.0,
            window_median_glucose_mg_dl=125.0,
            baseline_delta_mg_dl=40.0,
            previous_baseline_delta_mg_dl=None,
            baseline_delta_change_mg_dl=None,
            evidence_window_days=90,
            evidence_id=ClinicalObservationState.APPROVED_EVIDENCE_ID,
            producer=ClinicalObservationState.APPROVED_PRODUCER,
            context_modifiers={"context": "stress"},
            last_evidence_fingerprint="a" * 64,
        )

    def test_current_snapshot_uses_only_patient_non_demo_logs_and_governed_twin(self):
        self._log(self.patient, days_ago=3, glucose=120)
        self._log(self.patient, days_ago=1, glucose=180)
        self._log(self.patient, days_ago=0, glucose=600, source="demo")
        self._log(self.other, days_ago=0, glucose=300)
        self._observation(self.patient)
        self._observation(self.other, key="context:activity")

        before_observations = ClinicalObservationState.objects.count()
        before_proactive = ProactiveInsightState.objects.count()
        brief = assemble_consultation_brief(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.now,
        )

        self.assertEqual(
            brief.comparison_basis,
            ConsultationComparisonBasis.CURRENT_SNAPSHOT,
        )
        self.assertIsNone(brief.review_checkpoint)
        self.assertIn("no_authoritative_review_checkpoint", brief.missing_data)
        self.assertIn("since_review_comparison_unavailable", brief.limitations)
        self.assertEqual(ClinicalObservationState.objects.count(), before_observations)
        self.assertEqual(ProactiveInsightState.objects.count(), before_proactive)

        by_key = {item.key: item for item in brief.items}
        self.assertEqual(by_key["recorded_glucose.latest_mg_dl"].value, 180.0)
        self.assertEqual(by_key["recorded_glucose.latest_mg_dl"].truth_kind, TruthKind.OBSERVED_FACT)

        average = by_key["recorded_glucose.average_mg_dl"]
        self.assertEqual(average.value, 150.0)
        self.assertEqual(average.truth_kind, TruthKind.DETERMINISTIC_DERIVATION)
        self.assertEqual(average.evidence_id, "rule.metric.recorded-glucose-stats.v1")
        self.assertIn("not_cgm_time_weighted_and_not_target_assessment", average.limitations)

        twin = by_key["clinical_twin.context:stress.status"]
        self.assertEqual(twin.value, ClinicalObservationState.STATUS_ACTIVE)
        self.assertEqual(twin.truth_kind, TruthKind.DETERMINISTIC_DERIVATION)
        self.assertEqual(twin.evidence_id, ClinicalObservationState.APPROVED_EVIDENCE_ID)
        self.assertEqual(twin.evidence_density, ConsultationEvidenceDensity.MODERATE)
        self.assertEqual(twin.allowed_next_step, ConsultationNextStep.PREPARE_CLINICIAN_DISCUSSION)
        self.assertNotIn("clinical_twin.context:activity.status", by_key)

    def test_window_excludes_outside_rows_and_reports_missing_glucose_truthfully(self):
        self._log(self.patient, days_ago=30, glucose=220)

        brief = assemble_consultation_brief(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.now,
        )

        keys = {item.key for item in brief.items}
        self.assertNotIn("recorded_glucose.latest_mg_dl", keys)
        self.assertNotIn("recorded_glucose.average_mg_dl", keys)
        self.assertIn("no_synchronized_non_demo_glucose_in_window", brief.missing_data)
        self.assertIn("no_eligible_clinical_twin_observations", brief.missing_data)

    def test_explicit_checkpoint_unlocks_only_provable_twin_transitions(self):
        checkpoint_at = self.now - timedelta(days=7)
        checkpoint = ConsultationReviewCheckpoint(
            reviewed_at=checkpoint_at,
            source="test.explicit-clinician-review",
        )
        self._log(self.patient, days_ago=1, glucose=140)
        self._observation(
            self.patient,
            key="context:new",
            first_seen_at=self.now - timedelta(days=3),
            last_seen_at=self.now - timedelta(days=1),
            status_changed_at=self.now - timedelta(days=3),
        )
        self._observation(
            self.patient,
            key="context:persisting",
            first_seen_at=self.now - timedelta(days=20),
            last_seen_at=self.now - timedelta(days=1),
            status_changed_at=self.now - timedelta(days=20),
        )
        self._observation(
            self.patient,
            key="context:resolved",
            status=ClinicalObservationState.STATUS_INACTIVE,
            first_seen_at=self.now - timedelta(days=20),
            last_seen_at=self.now - timedelta(days=8),
            status_changed_at=self.now - timedelta(days=2),
        )
        self._observation(
            self.patient,
            key="context:ambiguous",
            first_seen_at=self.now - timedelta(days=20),
            last_seen_at=self.now - timedelta(days=1),
            status_changed_at=self.now - timedelta(days=2),
        )

        brief = assemble_consultation_brief(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.now,
            review_checkpoint=checkpoint,
        )

        self.assertEqual(
            brief.comparison_basis,
            ConsultationComparisonBasis.SINCE_REVIEW_CHECKPOINT,
        )
        self.assertEqual(brief.review_checkpoint, checkpoint)
        self.assertNotIn("no_authoritative_review_checkpoint", brief.missing_data)

        by_key = {item.key: item for item in brief.items}
        self.assertEqual(
            by_key["clinical_twin.context:new.status"].change_kind,
            ConsultationChangeKind.NEW_SINCE_REVIEW,
        )
        self.assertEqual(
            by_key["clinical_twin.context:persisting.status"].change_kind,
            ConsultationChangeKind.PERSISTING_SINCE_REVIEW,
        )
        self.assertEqual(
            by_key["clinical_twin.context:resolved.status"].change_kind,
            ConsultationChangeKind.RESOLVED_SINCE_REVIEW,
        )
        ambiguous = by_key["clinical_twin.context:ambiguous.status"]
        self.assertEqual(ambiguous.change_kind, ConsultationChangeKind.UNKNOWN)
        self.assertIn(
            "since_review_change_not_inferred_from_incomplete_transition_history",
            ambiguous.limitations,
        )

        # Window statistics are current facts/derivations, not fabricated deltas.
        self.assertEqual(
            by_key["recorded_glucose.latest_mg_dl"].change_kind,
            ConsultationChangeKind.CURRENT_STATE,
        )
        self.assertEqual(
            by_key["recorded_glucose.average_mg_dl"].change_kind,
            ConsultationChangeKind.CURRENT_STATE,
        )

    def test_old_inactive_twin_state_is_not_reintroduced_into_current_brief(self):
        self._observation(
            self.patient,
            key="context:old-resolved",
            status=ClinicalObservationState.STATUS_INACTIVE,
            first_seen_at=self.now - timedelta(days=60),
            last_seen_at=self.now - timedelta(days=40),
            status_changed_at=self.now - timedelta(days=30),
        )

        brief = assemble_consultation_brief(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.now,
        )

        self.assertNotIn(
            "clinical_twin.context:old-resolved.status",
            {item.key for item in brief.items},
        )

    def test_assembler_rejects_invalid_identity_window_and_checkpoint_type(self):
        with self.assertRaisesRegex(ValueError, "patient_id must be a positive integer"):
            assemble_consultation_brief(
                patient_id=0,
                window_start=self.start,
                window_end=self.now,
            )

        with self.assertRaisesRegex(ValueError, "window must be timezone-aware"):
            assemble_consultation_brief(
                patient_id=self.patient.id,
                window_start=self.start.replace(tzinfo=None),
                window_end=self.now,
            )

        with self.assertRaisesRegex(ValueError, "window_start must precede window_end"):
            assemble_consultation_brief(
                patient_id=self.patient.id,
                window_start=self.now,
                window_end=self.start,
            )

        with self.assertRaisesRegex(ValueError, "review_checkpoint must be"):
            assemble_consultation_brief(
                patient_id=self.patient.id,
                window_start=self.start,
                window_end=self.now,
                review_checkpoint="2026-08-01",
            )

    def test_checkpoint_at_or_after_window_end_fails_closed(self):
        checkpoint = ConsultationReviewCheckpoint(
            reviewed_at=self.now,
            source="test.explicit-clinician-review",
        )
        with self.assertRaisesRegex(ValueError, "checkpoint must precede"):
            assemble_consultation_brief(
                patient_id=self.patient.id,
                window_start=self.start,
                window_end=self.now,
                review_checkpoint=checkpoint,
            )
