from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from core.data_portability import build_patient_export
from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.models.companion_review import (
    CompanionReviewAnchor,
    CompanionReviewObservationSnapshot,
)
from diabetes.services.clinical.companion_change import (
    capture_companion_review_anchor,
    compare_since_last_companion_review,
)
from diabetes.services.clinical.observation_erasure import (
    reconcile_personal_response_memory_after_source_erasure,
)


class CompanionChangeSinceReviewTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="p2-companion-review")
        self.other = User.objects.create_user(username="p2-companion-other")
        self.now = timezone.now()

    def _observation(
        self,
        patient: User,
        *,
        key: str = "context:stress",
        status: str = ClinicalObservationState.STATUS_ACTIVE,
        first_seen_at=None,
        last_seen_at=None,
        status_changed_at=None,
        baseline_delta: float = 40.0,
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
            baseline_delta_mg_dl=baseline_delta,
            previous_baseline_delta_mg_dl=None,
            baseline_delta_change_mg_dl=None,
            evidence_window_days=90,
            evidence_id=ClinicalObservationState.APPROVED_EVIDENCE_ID,
            producer=ClinicalObservationState.APPROVED_PRODUCER,
            context_modifiers={"context": key},
            last_evidence_fingerprint="a" * 64,
        )

    @staticmethod
    def _advance_current_state(
        observation: ClinicalObservationState,
        *,
        anchor: CompanionReviewAnchor,
        status: str | None = None,
        baseline_delta: float | None = None,
        last_seen_days_after: int = 1,
    ) -> ClinicalObservationState:
        updates = {
            "last_seen_at": anchor.captured_at + timedelta(days=last_seen_days_after),
            "last_refreshed_at": anchor.captured_at + timedelta(days=last_seen_days_after),
        }
        if status is not None:
            updates["status"] = status
            updates["status_changed_at"] = anchor.captured_at + timedelta(hours=12)
        if baseline_delta is not None:
            updates["baseline_delta_mg_dl"] = baseline_delta
        ClinicalObservationState.objects.filter(pk=observation.pk).update(**updates)
        return ClinicalObservationState.objects.get(pk=observation.pk)

    def test_missing_anchor_fails_closed_without_fabricating_review_history(self):
        self._observation(self.patient)

        result = compare_since_last_companion_review(patient_id=self.patient.id)

        self.assertEqual(result.status, "insufficient_anchor")
        self.assertIsNone(result.anchor_id)
        self.assertEqual(result.changes, ())
        self.assertIn("no_explicit_companion_review_anchor", result.missing_data)

    def test_anchor_captures_only_patient_governed_state_and_exports_with_patient(self):
        own = self._observation(self.patient)
        self._observation(self.other, key="context:activity")

        anchor = capture_companion_review_anchor(patient_id=self.patient.id)

        self.assertEqual(anchor.patient_id, self.patient.id)
        self.assertEqual(anchor.source, CompanionReviewAnchor.SOURCE_EXPLICIT_REVIEW)
        self.assertEqual(anchor.snapshot_version, CompanionReviewAnchor.SNAPSHOT_VERSION)
        snapshots = list(anchor.observation_snapshots.all())
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0].observation_key, own.observation_key)
        self.assertEqual(snapshots[0].evidence_id, own.evidence_id)
        self.assertEqual(snapshots[0].producer, own.producer)

        export = build_patient_export(self.patient)
        records = export["data"]["records"]
        self.assertEqual(len(records["diabetes.companionreviewanchor"]), 1)
        self.assertEqual(
            len(records["diabetes.companionreviewobservationsnapshot"]),
            1,
        )

    def test_new_observation_after_review_is_new_not_diagnosis(self):
        anchor = capture_companion_review_anchor(patient_id=self.patient.id)
        later = anchor.captured_at + timedelta(hours=1)
        self._observation(
            self.patient,
            key="context:activity",
            first_seen_at=later,
            last_seen_at=later + timedelta(hours=1),
            status_changed_at=later,
        )

        result = compare_since_last_companion_review(patient_id=self.patient.id)

        self.assertEqual(result.status, "ready")
        self.assertEqual(len(result.changes), 1)
        change = result.changes[0]
        self.assertEqual(change.change_kind, "new")
        self.assertIn(
            "no_diagnosis_causality_or_treatment_response_inference",
            change.limitations,
        )

    def test_active_observation_with_post_review_evidence_is_persisting(self):
        observation = self._observation(self.patient, baseline_delta=40.0)
        anchor = capture_companion_review_anchor(patient_id=self.patient.id)
        self._advance_current_state(
            observation,
            anchor=anchor,
            baseline_delta=45.0,
        )

        result = compare_since_last_companion_review(patient_id=self.patient.id)

        self.assertEqual(result.changes[0].change_kind, "persisting")
        self.assertEqual(result.changes[0].baseline_delta_at_review_mg_dl, 40.0)
        self.assertEqual(result.changes[0].baseline_delta_now_mg_dl, 45.0)

    def test_delta_toward_personal_baseline_is_descriptive_improving_only(self):
        observation = self._observation(self.patient, baseline_delta=40.0)
        anchor = capture_companion_review_anchor(patient_id=self.patient.id)
        self._advance_current_state(
            observation,
            anchor=anchor,
            baseline_delta=20.0,
        )

        result = compare_since_last_companion_review(patient_id=self.patient.id)

        change = result.changes[0]
        self.assertEqual(change.change_kind, "improving")
        self.assertIn(
            "descriptive_delta_moved_toward_personal_window_baseline",
            change.limitations,
        )
        self.assertIn(
            "improving_does_not_mean_treatment_response_or_clinical_outcome",
            change.limitations,
        )

    def test_governed_inactive_transition_after_review_is_resolved(self):
        observation = self._observation(self.patient)
        anchor = capture_companion_review_anchor(patient_id=self.patient.id)
        self._advance_current_state(
            observation,
            anchor=anchor,
            status=ClinicalObservationState.STATUS_INACTIVE,
        )

        result = compare_since_last_companion_review(patient_id=self.patient.id)

        change = result.changes[0]
        self.assertEqual(change.change_kind, "resolved")
        self.assertIn(
            "resolved_by_governed_clinical_twin_lifecycle",
            change.limitations,
        )

    def test_no_post_review_evidence_is_unknown_not_persisting(self):
        self._observation(self.patient)
        capture_companion_review_anchor(patient_id=self.patient.id)

        result = compare_since_last_companion_review(patient_id=self.patient.id)

        self.assertEqual(result.changes[0].change_kind, "unknown")
        self.assertIn("no_eligible_post_review_evidence", result.changes[0].limitations)

    def test_missing_current_state_is_unknown_not_resolved(self):
        observation = self._observation(self.patient)
        capture_companion_review_anchor(patient_id=self.patient.id)
        observation.delete()

        result = compare_since_last_companion_review(patient_id=self.patient.id)

        self.assertEqual(result.changes[0].change_kind, "unknown")
        self.assertIn(
            "current_governed_state_missing_cannot_infer_resolution",
            result.changes[0].limitations,
        )

    def test_reactivation_after_review_is_new_with_explicit_limitation(self):
        observation = self._observation(
            self.patient,
            status=ClinicalObservationState.STATUS_INACTIVE,
            status_changed_at=self.now - timedelta(days=2),
        )
        anchor = capture_companion_review_anchor(patient_id=self.patient.id)
        self._advance_current_state(
            observation,
            anchor=anchor,
            status=ClinicalObservationState.STATUS_ACTIVE,
        )

        result = compare_since_last_companion_review(patient_id=self.patient.id)

        change = result.changes[0]
        self.assertEqual(change.change_kind, "new")
        self.assertIn("reactivated_after_review", change.limitations)

    def test_latest_patient_anchor_is_used_and_other_patient_anchor_is_ignored(self):
        observation = self._observation(self.patient, baseline_delta=40.0)
        first = capture_companion_review_anchor(patient_id=self.patient.id)
        self._advance_current_state(observation, anchor=first, baseline_delta=30.0)
        second = capture_companion_review_anchor(patient_id=self.patient.id)
        capture_companion_review_anchor(patient_id=self.other.id)
        self._advance_current_state(observation, anchor=second, baseline_delta=20.0)

        result = compare_since_last_companion_review(patient_id=self.patient.id)

        self.assertEqual(result.anchor_id, second.id)
        self.assertEqual(result.changes[0].baseline_delta_at_review_mg_dl, 30.0)
        self.assertEqual(result.changes[0].baseline_delta_now_mg_dl, 20.0)

    def test_source_erasure_invalidates_review_anchors_before_rebuild(self):
        self._observation(self.patient)
        anchor = capture_companion_review_anchor(patient_id=self.patient.id)
        self.assertTrue(
            CompanionReviewObservationSnapshot.objects.filter(anchor=anchor).exists()
        )

        reconcile_personal_response_memory_after_source_erasure(
            patient_id=self.patient.id
        )

        self.assertFalse(
            CompanionReviewAnchor.objects.filter(patient_id=self.patient.id).exists()
        )
        self.assertFalse(
            CompanionReviewObservationSnapshot.objects.filter(anchor_id=anchor.id).exists()
        )

    def test_account_deletion_cascades_anchor_and_snapshot(self):
        self._observation(self.patient)
        anchor = capture_companion_review_anchor(patient_id=self.patient.id)
        anchor_id = anchor.id

        self.patient.delete()

        self.assertFalse(CompanionReviewAnchor.objects.filter(pk=anchor_id).exists())
        self.assertFalse(
            CompanionReviewObservationSnapshot.objects.filter(anchor_id=anchor_id).exists()
        )

    def test_invalid_patient_identity_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "patient_id must be a positive integer"):
            capture_companion_review_anchor(patient_id=0)
        with self.assertRaisesRegex(ValueError, "patient_id must be a positive integer"):
            compare_since_last_companion_review(patient_id=True)
