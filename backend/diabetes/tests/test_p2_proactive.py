from datetime import timedelta

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.utils import timezone

from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.models.entry import LogEntry
from diabetes.models.proactive_insight import ProactiveInsightState
from diabetes.services.clinical.evidence_registry import PERSONAL_RESPONSE_EVIDENCE_ID
from diabetes.services.clinical.proactive_intelligence import (
    ATTENTION_BUDGET,
    PROACTIVE_RULE_VERSION,
    evaluate_proactive_insights,
)


class ProactiveInsightLifecycleTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="p2-proactive-patient")
        self.now = timezone.now()

    def _log(
        self,
        *,
        days_ago: int,
        glucose: int,
        stressed: str = "",
        exercised: str = "",
    ) -> LogEntry:
        return LogEntry.objects.create(
            patient=self.patient,
            logged_at=self.now - timedelta(days=days_ago),
            blood_sugar=glucose,
            source="manual",
            stressed=stressed,
            exercised=exercised,
        )

    def _stress_pattern(self) -> list[LogEntry]:
        return [
            self._log(days_ago=day, glucose=glucose, stressed="yes")
            for day, glucose in enumerate((150, 160, 170))
        ]

    def test_first_eligible_observation_surfaces_once_with_bounded_authority(self):
        self._stress_pattern()
        self._log(days_ago=3, glucose=110)

        result = evaluate_proactive_insights(
            patient_id=self.patient.id,
            evaluated_at=self.now,
        )

        self.assertEqual(result.status, "surfaced")
        self.assertEqual(result.attention_budget, ATTENTION_BUDGET)
        self.assertEqual(result.pending_count, 0)
        self.assertIsNotNone(result.item)
        item = result.item
        assert item is not None
        self.assertEqual(item.observation_key, "context:stress")
        self.assertEqual(item.state, ProactiveInsightState.STATE_NEW)
        self.assertTrue(item.surface_now)
        self.assertEqual(item.allowed_next_step, ProactiveInsightState.ACTION_MONITOR)
        self.assertEqual(item.escalation_class, "none")
        self.assertEqual(item.evidence_id, PERSONAL_RESPONSE_EVIDENCE_ID)
        self.assertEqual(item.source_version, PROACTIVE_RULE_VERSION)
        self.assertEqual(item.priority.safety_time_sensitivity, "non_urgent_observation")
        self.assertEqual(item.priority.clinical_relevance, "observational")
        self.assertEqual(item.priority.evidence_density, "limited")
        self.assertEqual(item.priority.evidence_maturity, "internal_governed_rule")
        self.assertIn(
            "no_causality_diagnosis_or_treatment_inference",
            item.limitations_or_missing_data,
        )

        state = ProactiveInsightState.objects.get(
            observation__patient=self.patient,
            observation__observation_key="context:stress",
        )
        self.assertEqual(state.last_delivered_signature, state.current_signature)
        self.assertEqual(state.escalation_class, "none")

    def test_same_material_state_never_resurfaces_even_after_cooldown(self):
        self._stress_pattern()
        self._log(days_ago=3, glucose=110)

        first = evaluate_proactive_insights(
            patient_id=self.patient.id,
            evaluated_at=self.now,
        )
        second = evaluate_proactive_insights(
            patient_id=self.patient.id,
            evaluated_at=self.now + timedelta(hours=25),
        )

        self.assertEqual(first.status, "surfaced")
        self.assertEqual(second.status, "no_change")
        self.assertIsNone(second.item)

    def test_attention_budget_surfaces_only_one_pending_observation_per_24_hours(self):
        for day, glucose in enumerate((150, 160, 170)):
            self._log(
                days_ago=day,
                glucose=glucose,
                stressed="yes",
                exercised="yes",
            )
        self._log(days_ago=3, glucose=110)

        first = evaluate_proactive_insights(
            patient_id=self.patient.id,
            evaluated_at=self.now,
        )
        blocked = evaluate_proactive_insights(
            patient_id=self.patient.id,
            evaluated_at=self.now + timedelta(hours=1),
        )
        next_day = evaluate_proactive_insights(
            patient_id=self.patient.id,
            evaluated_at=self.now + timedelta(hours=25),
        )

        self.assertEqual(first.status, "surfaced")
        self.assertEqual(first.pending_count, 1)
        self.assertEqual(blocked.status, "cooldown")
        self.assertEqual(blocked.pending_count, 1)
        self.assertIsNone(blocked.item)
        self.assertEqual(next_day.status, "surfaced")
        self.assertEqual(next_day.pending_count, 0)
        assert first.item is not None
        assert next_day.item is not None
        self.assertNotEqual(first.item.observation_key, next_day.item.observation_key)

    def test_strengthening_repeatability_moves_to_persisting_and_clinician_preparation(self):
        self._stress_pattern()
        self._log(days_ago=5, glucose=110)
        evaluate_proactive_insights(
            patient_id=self.patient.id,
            evaluated_at=self.now,
        )

        self._log(days_ago=3, glucose=180, stressed="yes")
        self._log(days_ago=4, glucose=190, stressed="yes")
        result = evaluate_proactive_insights(
            patient_id=self.patient.id,
            evaluated_at=self.now + timedelta(hours=25),
        )

        self.assertEqual(result.status, "surfaced")
        assert result.item is not None
        self.assertEqual(result.item.state, ProactiveInsightState.STATE_PERSISTING)
        self.assertEqual(result.item.priority.clinical_relevance, "review_worthy")
        self.assertEqual(result.item.priority.evidence_density, "moderate")
        self.assertEqual(
            result.item.allowed_next_step,
            ProactiveInsightState.ACTION_PREPARE_CLINICIAN_DISCUSSION,
        )
        self.assertEqual(result.item.escalation_class, "none")

    def test_missing_data_cannot_resolve_but_eligible_absence_can(self):
        supporting = self._stress_pattern()
        neutral = self._log(days_ago=3, glucose=110)
        evaluate_proactive_insights(
            patient_id=self.patient.id,
            evaluated_at=self.now,
        )

        LogEntry.objects.filter(id__in=[entry.id for entry in supporting]).update(
            logged_at=self.now - timedelta(days=100)
        )
        neutral.logged_at = self.now
        neutral.save(update_fields=("logged_at",))

        insufficient = evaluate_proactive_insights(
            patient_id=self.patient.id,
            evaluated_at=self.now + timedelta(hours=25),
        )
        self.assertEqual(insufficient.status, "insufficient_data")

        observation = ClinicalObservationState.objects.get(
            patient=self.patient,
            observation_key="context:stress",
        )
        proactive = ProactiveInsightState.objects.get(observation=observation)
        self.assertEqual(observation.status, ClinicalObservationState.STATUS_ACTIVE)
        self.assertEqual(proactive.state, ProactiveInsightState.STATE_NEW)

        self._log(days_ago=1, glucose=115)
        self._log(days_ago=2, glucose=120)
        resolved = evaluate_proactive_insights(
            patient_id=self.patient.id,
            evaluated_at=self.now + timedelta(hours=50),
        )

        observation.refresh_from_db()
        proactive.refresh_from_db()
        self.assertEqual(observation.status, ClinicalObservationState.STATUS_INACTIVE)
        self.assertEqual(proactive.state, ProactiveInsightState.STATE_RESOLVED)
        self.assertEqual(resolved.status, "surfaced")
        assert resolved.item is not None
        self.assertEqual(resolved.item.state, ProactiveInsightState.STATE_RESOLVED)
        self.assertEqual(resolved.item.allowed_next_step, ProactiveInsightState.ACTION_MONITOR)

    def test_database_rejects_escalation_for_descriptive_personal_response_source(self):
        self._stress_pattern()
        self._log(days_ago=3, glucose=110)
        evaluate_proactive_insights(
            patient_id=self.patient.id,
            evaluated_at=self.now,
        )
        state = ProactiveInsightState.objects.get(
            observation__patient=self.patient,
        )

        for values in (
            {"state": ProactiveInsightState.STATE_ESCALATED},
            {"escalation_class": "clinician_handoff"},
            {"action_class": "CHANGE_TREATMENT"},
        ):
            with self.assertRaises(IntegrityError):
                with transaction.atomic():
                    ProactiveInsightState.objects.filter(pk=state.pk).update(**values)
            state.refresh_from_db()

        self.assertNotEqual(state.state, ProactiveInsightState.STATE_ESCALATED)
        self.assertEqual(state.escalation_class, "none")


class ProactiveInsightApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.patient = User.objects.create_user(username="p2-proactive-api")
        self.other = User.objects.create_user(username="p2-proactive-other")
        self.now = timezone.now()

    def _pattern(self, patient: User, *, base: int) -> None:
        for day, glucose in enumerate((base, base + 10, base + 20)):
            LogEntry.objects.create(
                patient=patient,
                logged_at=self.now - timedelta(days=day),
                blood_sugar=glucose,
                source="manual",
                stressed="yes",
            )
        LogEntry.objects.create(
            patient=patient,
            logged_at=self.now - timedelta(days=3),
            blood_sugar=base - 30,
            source="manual",
        )

    def test_feed_is_patient_scoped_and_returns_at_most_one_nonurgent_item(self):
        self._pattern(self.patient, base=150)
        self._pattern(self.other, base=220)
        self.client.force_login(self.patient)

        response = self.client.get("/api/v1/proactive-insights/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["attention_budget"], ATTENTION_BUDGET)
        self.assertIn(payload["status"], {"surfaced", "no_change"})
        self.assertIn("does not diagnose", payload["safety_notice"])
        if payload["item"] is not None:
            self.assertEqual(payload["item"]["escalation_class"], "none")
            self.assertEqual(
                payload["item"]["priority"]["safety_time_sensitivity"],
                "non_urgent_observation",
            )

        self.assertEqual(
            ProactiveInsightState.objects.filter(
                observation__patient=self.patient
            ).count(),
            1,
        )
        self.assertEqual(
            ProactiveInsightState.objects.filter(
                observation__patient=self.other
            ).count(),
            0,
        )
