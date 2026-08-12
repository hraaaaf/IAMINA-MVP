from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.models.entry import LogEntry
from diabetes.models.proactive_insight import ProactiveInsightState
from diabetes.services.clinical.proactive_intelligence import evaluate_proactive_insights


class ProactiveReactivationSafetyTests(TestCase):
    def test_reactivated_observation_cannot_remain_resolved_with_matching_fingerprint(self):
        patient = User.objects.create_user(username="p2-proactive-reactivation")
        now = timezone.now()
        supporting = []
        for day, glucose in enumerate((150, 160, 170)):
            supporting.append(
                LogEntry.objects.create(
                    patient=patient,
                    logged_at=now - timedelta(days=day),
                    blood_sugar=glucose,
                    source="manual",
                    stressed="yes",
                )
            )
        LogEntry.objects.create(
            patient=patient,
            logged_at=now - timedelta(days=3),
            blood_sugar=110,
            source="manual",
        )

        evaluate_proactive_insights(patient_id=patient.id, evaluated_at=now)
        observation = ClinicalObservationState.objects.get(patient=patient)
        proactive = ProactiveInsightState.objects.get(observation=observation)
        original_fingerprint = observation.last_evidence_fingerprint

        # Reproduce the fail-closed edge directly: the Clinical Twin is active
        # again with a recurrence, but the supporting-evidence fingerprint is
        # byte-identical to the prior episode.
        observation.status = ClinicalObservationState.STATUS_ACTIVE
        observation.recurrence_count = 2
        observation.last_evidence_fingerprint = original_fingerprint
        observation.save(
            update_fields=(
                "status",
                "recurrence_count",
                "last_evidence_fingerprint",
                "last_refreshed_at",
            )
        )
        proactive.state = ProactiveInsightState.STATE_RESOLVED
        proactive.last_observation_fingerprint = original_fingerprint
        proactive.save(update_fields=("state", "last_observation_fingerprint", "updated_at"))

        result = evaluate_proactive_insights(
            patient_id=patient.id,
            evaluated_at=now + timedelta(hours=25),
        )

        proactive.refresh_from_db()
        self.assertEqual(proactive.state, ProactiveInsightState.STATE_PERSISTING)
        self.assertNotEqual(proactive.state, ProactiveInsightState.STATE_RESOLVED)
        self.assertIn(result.status, {"surfaced", "no_change"})
