from datetime import timedelta
from inspect import signature

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from core.contracts.truth import TruthKind
from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.models.entry import LogEntry
from diabetes.services.clinical.companion_change import capture_companion_review_anchor
from diabetes.services.clinical.consultation_brief_assembler import (
    assemble_consultation_brief,
)
from diabetes.services.clinical.consultation_brief_contract import (
    ConsultationChangeKind,
    ConsultationComparisonBasis,
    ConsultationNextStep,
)


class ConsultationCompanionAssemblerTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="p2-companion-consultation")
        self.other = User.objects.create_user(username="p2-companion-consultation-other")
        self.now = timezone.now()
        self.end = self.now + timedelta(minutes=5)
        self.start = self.end - timedelta(days=14)

    def _log(self, patient: User, *, days_ago: int, glucose: int, source: str = "manual"):
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
        baseline_delta: float = 40.0,
    ) -> ClinicalObservationState:
        return ClinicalObservationState.objects.create(
            patient=patient,
            observation_key=key,
            kind=ClinicalObservationState.KIND_CONTEXT,
            status=status,
            first_seen_at=self.now - timedelta(days=10),
            last_seen_at=self.now - timedelta(days=1),
            status_changed_at=self.now - timedelta(days=10),
            recurrence_count=1,
            evidence_strength=ClinicalObservationState.EVIDENCE_MODERATE,
            previous_evidence_strength="",
            evidence_strength_trend=ClinicalObservationState.TREND_INITIAL,
            observations=4,
            distinct_days=3,
            observation_median_glucose_mg_dl=165.0,
            window_median_glucose_mg_dl=125.0,
            baseline_delta_mg_dl=baseline_delta,
            previous_baseline_delta_mg_dl=None,
            baseline_delta_change_mg_dl=None,
            evidence_window_days=90,
            evidence_id=ClinicalObservationState.APPROVED_EVIDENCE_ID,
            producer=ClinicalObservationState.APPROVED_PRODUCER,
            context_modifiers={"source_field": "stressed", "recorded_value": "yes"},
            last_evidence_fingerprint="a" * 64,
        )

    def test_without_review_anchor_brief_is_current_snapshot_and_fails_closed_on_history(self):
        self._log(self.patient, days_ago=2, glucose=120)
        self._log(self.patient, days_ago=1, glucose=180)
        self._observation(self.patient)

        brief = assemble_consultation_brief(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
        )

        self.assertEqual(
            brief.comparison_basis,
            ConsultationComparisonBasis.CURRENT_SNAPSHOT,
        )
        self.assertIsNone(brief.review_checkpoint)
        self.assertIn("no_explicit_companion_review_anchor", brief.missing_data)
        self.assertIn("clinician_remains_medical_decision_authority", brief.limitations)
        self.assertFalse(brief.has_since_review_claims)

        by_key = {item.key: item for item in brief.items}
        self.assertEqual(by_key["recorded_glucose.latest_mg_dl"].value, 180.0)
        self.assertEqual(by_key["recorded_glucose.average_mg_dl"].value, 150.0)
        self.assertEqual(
            by_key["clinical_twin.context:stress.status"].truth_kind,
            TruthKind.DETERMINISTIC_DERIVATION,
        )

    def test_authoritative_companion_anchor_enables_bounded_since_review_semantics(self):
        self._log(self.patient, days_ago=1, glucose=170)
        observation = self._observation(self.patient, baseline_delta=40.0)
        anchor = capture_companion_review_anchor(patient_id=self.patient.id)
        ClinicalObservationState.objects.filter(pk=observation.pk).update(
            last_seen_at=anchor.captured_at + timedelta(hours=2),
            last_refreshed_at=anchor.captured_at + timedelta(hours=2),
            baseline_delta_mg_dl=45.0,
        )

        brief = assemble_consultation_brief(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
        )

        self.assertEqual(
            brief.comparison_basis,
            ConsultationComparisonBasis.SINCE_REVIEW_CHECKPOINT,
        )
        self.assertIsNotNone(brief.review_checkpoint)
        assert brief.review_checkpoint is not None
        self.assertEqual(brief.review_checkpoint.reviewed_at, anchor.captured_at)
        self.assertEqual(brief.review_checkpoint.source, "companion.explicit-review.v1")

        change = {
            item.key: item for item in brief.items
        }["companion_change.context:stress"]
        self.assertEqual(
            change.change_kind,
            ConsultationChangeKind.PERSISTING_SINCE_REVIEW,
        )
        self.assertEqual(
            change.allowed_next_step,
            ConsultationNextStep.PREPARE_CLINICIAN_DISCUSSION,
        )
        self.assertIn("observational_association_only", change.limitations)
        self.assertTrue(brief.has_since_review_claims)

    def test_unknown_change_stays_unknown_and_only_authorizes_missing_data_collection(self):
        observation = self._observation(self.patient)
        capture_companion_review_anchor(patient_id=self.patient.id)
        self.assertIsNotNone(observation.pk)

        brief = assemble_consultation_brief(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
        )

        change = {
            item.key: item for item in brief.items
        }["companion_change.context:stress"]
        self.assertEqual(change.change_kind, ConsultationChangeKind.UNKNOWN)
        self.assertEqual(
            change.allowed_next_step,
            ConsultationNextStep.COLLECT_MISSING_DATA,
        )
        self.assertIn("no_eligible_post_review_evidence", change.missing_data)

    def test_patient_scope_and_demo_exclusion_are_preserved(self):
        self._log(self.patient, days_ago=2, glucose=140)
        self._log(self.patient, days_ago=0, glucose=600, source="demo")
        self._log(self.other, days_ago=0, glucose=300)
        self._observation(self.other, key="context:activity")

        brief = assemble_consultation_brief(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
        )
        by_key = {item.key: item for item in brief.items}

        self.assertEqual(by_key["recorded_glucose.latest_mg_dl"].value, 140.0)
        self.assertNotIn("clinical_twin.context:activity.status", by_key)

    def test_public_entrypoint_has_no_free_text_model_or_caller_checkpoint_authority(self):
        self.assertEqual(
            tuple(signature(assemble_consultation_brief).parameters),
            ("patient_id", "window_start", "window_end"),
        )

    def test_invalid_identity_and_window_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "patient_id must be a positive integer"):
            assemble_consultation_brief(
                patient_id=0,
                window_start=self.start,
                window_end=self.end,
            )
        with self.assertRaisesRegex(ValueError, "window must be timezone-aware"):
            assemble_consultation_brief(
                patient_id=self.patient.id,
                window_start=self.start.replace(tzinfo=None),
                window_end=self.end,
            )
        with self.assertRaisesRegex(ValueError, "window_start must precede window_end"):
            assemble_consultation_brief(
                patient_id=self.patient.id,
                window_start=self.end,
                window_end=self.start,
            )
