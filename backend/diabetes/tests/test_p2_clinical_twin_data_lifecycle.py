from datetime import timedelta
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, TestCase
from django.utils import timezone

from core.data_portability import build_patient_export
from core.retention_policy import ACCOUNT_DELETION, validated_retention_schedule
from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.models.entry import LogEntry
from diabetes.models.proactive_insight import ProactiveInsightState
from diabetes.services.clinical.observation_memory import refresh_personal_response_memory


class ClinicalTwinDataLifecycleTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="p2-twin-lifecycle")
        self.client = Client()
        self.client.force_login(self.patient)
        self.now = timezone.now()

    def _log(self, *, days_ago: int, glucose: int, stressed: str = "") -> LogEntry:
        return LogEntry.objects.create(
            patient=self.patient,
            logged_at=self.now - timedelta(days=days_ago),
            blood_sugar=glucose,
            stressed=stressed,
            source="manual",
        )

    def test_explicit_source_erasure_does_not_leave_stale_derived_observation(self):
        supporting = [
            self._log(days_ago=0, glucose=150, stressed="yes"),
            self._log(days_ago=1, glucose=160, stressed="yes"),
            self._log(days_ago=2, glucose=170, stressed="yes"),
        ]
        self._log(days_ago=3, glucose=110)
        refresh_personal_response_memory(patient_id=self.patient.id)
        self.assertTrue(
            ClinicalObservationState.objects.filter(
                patient=self.patient,
                observation_key="context:stress",
            ).exists()
        )

        response = self.client.delete(f"/api/v1/logs/{supporting[0].id}")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            ClinicalObservationState.objects.filter(patient=self.patient).exists()
        )

    def test_explicit_source_erasure_rebuilds_only_from_surviving_support(self):
        supporting = [
            self._log(days_ago=0, glucose=150, stressed="yes"),
            self._log(days_ago=1, glucose=160, stressed="yes"),
            self._log(days_ago=2, glucose=170, stressed="yes"),
            self._log(days_ago=3, glucose=180, stressed="yes"),
        ]
        refresh_personal_response_memory(patient_id=self.patient.id)
        before = ClinicalObservationState.objects.get(patient=self.patient)
        before_fingerprint = before.last_evidence_fingerprint
        self.assertEqual(before.observations, 4)
        ProactiveInsightState.objects.create(
            observation=before,
            state=ProactiveInsightState.STATE_NEW,
            clinical_relevance=ProactiveInsightState.RELEVANCE_OBSERVATIONAL,
            action_class=ProactiveInsightState.ACTION_MONITOR,
            escalation_class=ProactiveInsightState.ESCALATION_NONE,
            last_observation_fingerprint=before.last_evidence_fingerprint,
            current_signature="a" * 64,
        )

        response = self.client.delete(f"/api/v1/logs/{supporting[0].id}")

        self.assertEqual(response.status_code, 204)
        after = ClinicalObservationState.objects.get(
            patient=self.patient,
            observation_key="context:stress",
        )
        self.assertEqual(after.observations, 3)
        self.assertEqual(after.recurrence_count, 1)
        self.assertNotEqual(after.last_evidence_fingerprint, before_fingerprint)
        self.assertFalse(ProactiveInsightState.objects.exists())

    def test_patient_export_contains_persisted_clinical_observation_state(self):
        for day, glucose in enumerate((150, 160, 170)):
            self._log(days_ago=day, glucose=glucose, stressed="yes")
        refresh_personal_response_memory(patient_id=self.patient.id)

        bundle = build_patient_export(self.patient)

        records = bundle["data"]["records"]
        self.assertIn("diabetes.clinicalobservationstate", records)
        observations = records["diabetes.clinicalobservationstate"]
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0]["observation_key"], "context:stress")
        self.assertEqual(
            bundle["manifest"]["models"]["diabetes.clinicalobservationstate"],
            1,
        )

    def test_verified_account_erasure_cascades_to_clinical_observation_state(self):
        for day, glucose in enumerate((150, 160, 170)):
            self._log(days_ago=day, glucose=glucose, stressed="yes")
        refresh_personal_response_memory(patient_id=self.patient.id)
        patient_id = self.patient.id
        observation_id = ClinicalObservationState.objects.get(patient=self.patient).id

        call_command(
            "delete_patient_data",
            user_id=patient_id,
            requested_at=timezone.localdate() - timedelta(days=31),
            approval_reference="REQ-P2-TWIN-LIFECYCLE",
            export_sha256="f" * 64,
            legal_hold_status="CLEARED",
            execute=True,
            confirm=f"DELETE-PATIENT-{patient_id}",
            stdout=StringIO(),
        )

        self.assertFalse(User.objects.filter(pk=patient_id).exists())
        self.assertFalse(
            ClinicalObservationState.objects.filter(pk=observation_id).exists()
        )

    def test_clinical_twin_uses_existing_patient_application_retention_rule(self):
        rule = next(
            rule
            for rule in validated_retention_schedule(today=timezone.localdate())
            if rule.dataset == "patient_application_records"
        )

        self.assertEqual(rule.trigger, ACCOUNT_DELETION)
        self.assertEqual(rule.retention_days, 30)
        self.assertIn("Django relational cascade", rule.deletion_action)
        self.assertTrue(rule.legal_hold_supported)
