from datetime import timedelta
from pathlib import Path

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from core.contracts.truth import TruthKind
from diabetes.models.clinical_insight import ClinicalInsightState
from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.models.entry import LogEntry
from diabetes.services.clinical.observation_memory import refresh_personal_response_memory
from diabetes.services.clinical.proactive_attention import (
    EmergencyClearance,
    PriorityVector,
    select_next_proactive_insight,
)


class ProactiveAttentionTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="p2-proactive-patient")
        self.other_patient = User.objects.create_user(username="p2-proactive-other")
        self.now = timezone.now()

    def _log(
        self,
        *,
        patient=None,
        days_ago=0,
        glucose=120,
        stressed="",
        is_sick="",
    ) -> LogEntry:
        return LogEntry.objects.create(
            patient=patient or self.patient,
            logged_at=self.now - timedelta(days=days_ago),
            blood_sugar=glucose,
            source="manual",
            stressed=stressed,
            is_sick=is_sick,
        )

    def _stress_pattern(self, *, patient=None, values=(150, 160, 170)) -> list[LogEntry]:
        return [
            self._log(
                patient=patient,
                days_ago=day,
                glucose=glucose,
                stressed="yes",
            )
            for day, glucose in enumerate(values)
        ]

    def _neutral_background(self, *, patient=None, values=(100, 110, 120), start_day=3) -> list[LogEntry]:
        return [
            self._log(
                patient=patient,
                days_ago=start_day + offset,
                glucose=glucose,
            )
            for offset, glucose in enumerate(values)
        ]

    def _clear(self, *, patient_id=None):
        return select_next_proactive_insight(
            patient_id=patient_id or self.patient.id,
            emergency_clearance=EmergencyClearance.CLEAR,
        )

    def test_emergency_clearance_is_required_before_any_proactive_write(self):
        self._stress_pattern()

        unknown = select_next_proactive_insight(patient_id=self.patient.id)
        active = select_next_proactive_insight(
            patient_id=self.patient.id,
            emergency_clearance=EmergencyClearance.ACTIVE,
        )

        self.assertIsNone(unknown.candidate)
        self.assertEqual(unknown.suppression_reason, "emergency_clearance_required")
        self.assertIsNone(active.candidate)
        self.assertEqual(active.suppression_reason, "deterministic_emergency_active")
        self.assertFalse(ClinicalObservationState.objects.exists())
        self.assertFalse(ClinicalInsightState.objects.exists())

    def test_first_eligible_insight_surfaces_once_then_is_suppressed(self):
        self._stress_pattern()
        self._neutral_background()

        first = self._clear()
        self.assertIsNotNone(first.candidate)
        candidate = first.candidate
        assert candidate is not None
        self.assertEqual(candidate.observation_key, "context:stress")
        self.assertEqual(candidate.lifecycle_state, ClinicalInsightState.STATE_NEW)
        self.assertEqual(candidate.allowed_next_step, ClinicalInsightState.ACTION_MONITOR)
        self.assertIn("first_eligible_observation", candidate.what_changed)
        self.assertEqual(candidate.escalation_class, "none")
        self.assertEqual(candidate.priority_vector.safety_time_sensitivity, "routine_non_emergency")

        state = ClinicalInsightState.objects.get(observation__patient=self.patient)
        self.assertEqual(state.lifecycle_state, ClinicalInsightState.STATE_MONITORING)
        self.assertEqual(state.surface_count, 1)

        second = self._clear()
        state.refresh_from_db()
        self.assertIsNone(second.candidate)
        self.assertEqual(second.suppression_reason, "attention_budget_suppressed")
        self.assertEqual(state.surface_count, 1)

    def test_attention_budget_surfaces_one_candidate_at_a_time_without_losing_pending_reason(self):
        for day, glucose in enumerate((150, 160, 170, 180, 190)):
            self._log(days_ago=day, glucose=glucose, stressed="yes")
        for day, glucose in enumerate((130, 140, 150), start=5):
            self._log(days_ago=day, glucose=glucose, is_sick="yes")
        self._neutral_background(values=(100, 105, 110), start_day=8)

        first = self._clear()
        second = self._clear()
        third = self._clear()

        self.assertIsNotNone(first.candidate)
        self.assertIsNotNone(second.candidate)
        assert first.candidate is not None and second.candidate is not None
        self.assertEqual(first.candidate.observation_key, "context:stress")
        self.assertEqual(first.candidate.evidence_density["grade"], "moderate")
        self.assertEqual(second.candidate.observation_key, "context:illness")
        self.assertIn("first_eligible_observation", second.candidate.what_changed)
        self.assertIsNone(third.candidate)
        self.assertEqual(ClinicalInsightState.objects.filter(surface_count=1).count(), 2)

    def test_material_support_change_can_resurface_but_identical_read_cannot(self):
        self._stress_pattern()
        self._neutral_background()
        self._clear()

        self._log(days_ago=6, glucose=180, stressed="yes")
        changed = self._clear()
        repeated = self._clear()

        self.assertIsNotNone(changed.candidate)
        assert changed.candidate is not None
        self.assertTrue(
            {"supporting_observations_changed", "evidence_support_changed"}
            & set(changed.candidate.what_changed)
        )
        self.assertIsNone(repeated.candidate)

    def test_true_reactivation_becomes_persisting_and_repeat_is_suppressed(self):
        supporting = self._stress_pattern()
        self._neutral_background()
        self._clear()

        LogEntry.objects.filter(pk__in=[entry.pk for entry in supporting]).update(
            logged_at=self.now - timedelta(days=100)
        )
        inactive_wait = self._clear()
        self.assertIsNone(inactive_wait.candidate)
        source = ClinicalObservationState.objects.get(
            patient=self.patient,
            observation_key="context:stress",
        )
        self.assertEqual(source.status, ClinicalObservationState.STATUS_INACTIVE)
        self.assertEqual(source.recurrence_count, 1)

        for day, glucose in ((7, 180), (8, 190), (9, 200)):
            self._log(days_ago=day, glucose=glucose, stressed="yes")

        reactivated = self._clear()
        repeated = self._clear()

        self.assertIsNotNone(reactivated.candidate)
        assert reactivated.candidate is not None
        self.assertEqual(reactivated.candidate.lifecycle_state, ClinicalInsightState.STATE_PERSISTING)
        self.assertIn("observation_reactivated", reactivated.candidate.what_changed)
        self.assertIn("activation_episode_recurred", reactivated.candidate.what_changed)
        source.refresh_from_db()
        self.assertEqual(source.recurrence_count, 2)
        self.assertIsNone(repeated.candidate)

    def test_improving_means_only_movement_toward_recorded_baseline(self):
        self._stress_pattern(values=(200, 210, 220))
        self._neutral_background(values=(100, 110, 120))
        self._clear()

        before = ClinicalObservationState.objects.get(
            patient=self.patient,
            observation_key="context:stress",
        )
        self.assertEqual(before.baseline_delta_mg_dl, 50.0)

        self._neutral_background(values=(190, 195, 198), start_day=6)
        improving = self._clear()
        repeated = self._clear()

        self.assertIsNotNone(improving.candidate)
        assert improving.candidate is not None
        self.assertEqual(improving.candidate.lifecycle_state, ClinicalInsightState.STATE_IMPROVING)
        self.assertIn("moved_toward_recorded_baseline", improving.candidate.what_changed)
        self.assertLess(abs(improving.candidate.personal_baseline_delta_mg_dl), 50.0)
        self.assertEqual(improving.candidate.allowed_next_step, ClinicalInsightState.ACTION_MONITOR)
        self.assertEqual(improving.candidate.escalation_class, "none")
        self.assertIsNone(repeated.candidate)

    def test_resolved_requires_eligible_full_horizon_absence_and_is_not_clinical_resolution(self):
        supporting = self._stress_pattern()
        self._neutral_background()
        first = self._clear()
        self.assertIsNotNone(first.candidate)

        LogEntry.objects.filter(pk__in=[entry.pk for entry in supporting]).update(
            logged_at=self.now - timedelta(days=100)
        )
        source = ClinicalObservationState.objects.get(
            patient=self.patient,
            observation_key="context:stress",
        )
        old_seen = self.now - timedelta(days=100)
        ClinicalObservationState.objects.filter(pk=source.pk).update(last_seen_at=old_seen)

        resolved = self._clear()
        self.assertIsNotNone(resolved.candidate)
        assert resolved.candidate is not None
        self.assertEqual(resolved.candidate.lifecycle_state, ClinicalInsightState.STATE_RESOLVED)
        self.assertIn("lifecycle_resolved", resolved.candidate.what_changed)
        self.assertEqual(resolved.candidate.escalation_class, "none")
        self.assertNotIn("diagnosis", " ".join(resolved.candidate.what_changed).lower())
        self.assertNotIn("treatment", " ".join(resolved.candidate.what_changed).lower())

    def test_sparse_data_never_resolves_and_surfaces_collect_missing_data_once(self):
        supporting = self._stress_pattern()
        background = self._neutral_background()
        self._clear()

        LogEntry.objects.filter(
            pk__in=[entry.pk for entry in supporting + background]
        ).update(logged_at=self.now - timedelta(days=100))

        sparse = self._clear()
        repeated = self._clear()

        self.assertIsNotNone(sparse.candidate)
        assert sparse.candidate is not None
        self.assertNotEqual(sparse.candidate.lifecycle_state, ClinicalInsightState.STATE_RESOLVED)
        self.assertEqual(
            sparse.candidate.allowed_next_step,
            ClinicalInsightState.ACTION_COLLECT_MISSING_DATA,
        )
        self.assertIn("data_became_insufficient", sparse.candidate.what_changed)
        self.assertIsNone(repeated.candidate)

    def test_insufficient_data_cannot_promote_existing_lifecycle(self):
        supporting = self._stress_pattern(values=(200, 210, 220))
        background = self._neutral_background(values=(100, 110, 120))
        self._clear()

        source = ClinicalObservationState.objects.get(
            patient=self.patient,
            observation_key="context:stress",
        )
        state = ClinicalInsightState.objects.get(observation=source)
        self.assertEqual(state.lifecycle_state, ClinicalInsightState.STATE_MONITORING)

        # Simulate already-known historical recurrence/baseline evolution. The fresh
        # dataset then becomes insufficient. Neither stale signal may promote the
        # proactive lifecycle during that insufficient refresh.
        ClinicalObservationState.objects.filter(pk=source.pk).update(
            recurrence_count=2,
            previous_baseline_delta_mg_dl=50.0,
            baseline_delta_mg_dl=20.0,
            baseline_delta_change_mg_dl=-30.0,
        )
        ClinicalInsightState.objects.filter(pk=state.pk).update(
            recurrence_count_snapshot=2,
            baseline_delta_snapshot_mg_dl=20.0,
        )
        LogEntry.objects.filter(
            pk__in=[entry.pk for entry in supporting + background]
        ).update(logged_at=self.now - timedelta(days=100))

        sparse = self._clear()
        state.refresh_from_db()

        self.assertIsNotNone(sparse.candidate)
        assert sparse.candidate is not None
        self.assertEqual(
            sparse.candidate.allowed_next_step,
            ClinicalInsightState.ACTION_COLLECT_MISSING_DATA,
        )
        self.assertEqual(sparse.candidate.lifecycle_state, ClinicalInsightState.STATE_MONITORING)
        self.assertEqual(state.lifecycle_state, ClinicalInsightState.STATE_MONITORING)
        self.assertNotEqual(state.lifecycle_state, ClinicalInsightState.STATE_PERSISTING)
        self.assertNotEqual(state.lifecycle_state, ClinicalInsightState.STATE_IMPROVING)

    def test_reactivation_dominates_simultaneous_baseline_improvement(self):
        supporting = self._stress_pattern(values=(200, 210, 220))
        self._neutral_background(values=(100, 110, 120))
        self._clear()

        source = ClinicalObservationState.objects.get(
            patient=self.patient,
            observation_key="context:stress",
        )
        original_delta = source.baseline_delta_mg_dl

        LogEntry.objects.filter(pk__in=[entry.pk for entry in supporting]).update(
            logged_at=self.now - timedelta(days=100)
        )
        self._clear()
        source.refresh_from_db()
        self.assertEqual(source.status, ClinicalObservationState.STATUS_INACTIVE)

        for day, glucose in ((7, 130), (8, 140), (9, 150)):
            self._log(days_ago=day, glucose=glucose, stressed="yes")

        reactivated = self._clear()
        source.refresh_from_db()

        self.assertIsNotNone(reactivated.candidate)
        assert reactivated.candidate is not None
        self.assertEqual(source.recurrence_count, 2)
        self.assertLess(abs(source.baseline_delta_mg_dl), abs(original_delta))
        self.assertEqual(
            reactivated.candidate.lifecycle_state,
            ClinicalInsightState.STATE_PERSISTING,
        )
        self.assertIn("observation_reactivated", reactivated.candidate.what_changed)
        self.assertIn("activation_episode_recurred", reactivated.candidate.what_changed)
        self.assertIn("moved_toward_recorded_baseline", reactivated.candidate.what_changed)

    def test_patient_scope_is_strict(self):
        self._stress_pattern(patient=self.patient, values=(140, 150, 160))
        self._stress_pattern(patient=self.other_patient, values=(220, 230, 240))
        self._neutral_background(patient=self.patient)
        self._neutral_background(patient=self.other_patient)
        refresh_personal_response_memory(patient_id=self.other_patient.id)

        selected = self._clear(patient_id=self.patient.id)

        self.assertIsNotNone(selected.candidate)
        self.assertEqual(
            ClinicalObservationState.objects.filter(patient=self.other_patient).count(),
            1,
        )
        self.assertFalse(
            ClinicalInsightState.objects.filter(observation__patient=self.other_patient).exists()
        )
        self.assertEqual(
            ClinicalInsightState.objects.filter(observation__patient=self.patient).count(),
            1,
        )

    def test_database_rejects_unapproved_provenance_escalation_and_action(self):
        self._stress_pattern()
        self._neutral_background()
        self._clear()
        state = ClinicalInsightState.objects.get(observation__patient=self.patient)

        forbidden_updates = (
            {"truth_kind": TruthKind.MODEL_INFERENCE.value},
            {"producer": "companion.proactive.v0"},
            {"source_producer": "companion.deep_memory"},
            {"source_evidence_id": "rule.unreviewed.proactive.v0"},
            {"lifecycle_state": ClinicalInsightState.STATE_ESCALATED},
            {"allowed_next_step": "clinician_handoff"},
        )
        for update in forbidden_updates:
            with self.assertRaises(IntegrityError):
                with transaction.atomic():
                    ClinicalInsightState.objects.filter(pk=state.pk).update(**update)
            state.refresh_from_db()

        self.assertEqual(state.truth_kind, TruthKind.DETERMINISTIC_DERIVATION.value)
        self.assertEqual(state.producer, ClinicalInsightState.PRODUCER)
        self.assertEqual(state.source_producer, ClinicalInsightState.APPROVED_SOURCE_PRODUCER)
        self.assertEqual(
            state.source_evidence_id,
            ClinicalInsightState.APPROVED_SOURCE_EVIDENCE_ID,
        )
        self.assertNotEqual(state.lifecycle_state, ClinicalInsightState.STATE_ESCALATED)
        self.assertIn(
            state.allowed_next_step,
            (ClinicalInsightState.ACTION_MONITOR, ClinicalInsightState.ACTION_COLLECT_MISSING_DATA),
        )

    def test_priority_contract_is_explicit_and_has_no_companion_or_scalar_score_authority(self):
        fields = set(PriorityVector.__dataclass_fields__)
        self.assertEqual(
            fields,
            {
                "safety_time_sensitivity",
                "clinical_relevance",
                "persistence",
                "baseline_distance_mg_dl",
                "evidence_strength",
                "evidence_maturity",
                "actionability",
                "interruption_cost",
                "observations",
                "distinct_days",
                "recurrence_count",
                "last_seen_at",
            },
        )

        backend_root = Path(__file__).resolve().parents[2]
        source = (backend_root / "diabetes/services/clinical/proactive_attention.py").read_text()
        for forbidden in (
            "priority_score",
            "risk_score",
            "confidence_score",
            "concern_level",
            "clinical_mood",
            "IAminaDeepMemory",
            "companion.",
            "MODEL_INFERENCE",
        ):
            self.assertNotIn(forbidden, source)

        self.assertIn("EmergencyClearance.UNKNOWN", source)
        self.assertIn("emergency_clearance_required", source)
        self.assertIn("deterministic_emergency_active", source)
