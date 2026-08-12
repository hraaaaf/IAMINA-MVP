from datetime import timedelta
from inspect import signature
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from diabetes.models.entry import LogEntry
from diabetes.models.proactive_insight import ProactiveInsightState
from diabetes.services.clinical.companion_change import (
    capture_companion_review_anchor,
)
from diabetes.services.clinical.companion_smart_suggestions import (
    ACTIVE_V1_SUGGESTION_CLASSES,
    ALLOWED_SUGGESTION_CLASSES,
    SOURCE_VERSION,
    evaluate_companion_smart_suggestion,
)
from diabetes.services.clinical.observation_memory import (
    refresh_personal_response_memory,
)


class CompanionSmartSuggestionTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="p2-companion-smart")
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

    def test_contract_lists_six_classes_but_v1_activates_only_existing_authority(self):
        self.assertEqual(
            ALLOWED_SUGGESTION_CLASSES,
            (
                "UNDERSTAND_DATA",
                "MONITOR",
                "COLLECT_MISSING_DATA",
                "LEARN",
                "PREPARE_CLINICIAN_DISCUSSION",
                "FOLLOW_UP_RECORD",
            ),
        )
        self.assertEqual(
            ACTIVE_V1_SUGGESTION_CLASSES,
            (
                "UNDERSTAND_DATA",
                "MONITOR",
                "PREPARE_CLINICIAN_DISCUSSION",
            ),
        )

    def test_first_eligible_observation_becomes_understand_data_with_p2_3_envelope(self):
        self._stress_pattern()
        self._log(days_ago=3, glucose=110)

        result = evaluate_companion_smart_suggestion(
            patient_id=self.patient.id,
            evaluated_at=self.now,
        )

        self.assertEqual(result.status, "suggested")
        self.assertEqual(result.source_version, SOURCE_VERSION)
        self.assertIsNotNone(result.suggestion)
        suggestion = result.suggestion
        assert suggestion is not None
        self.assertEqual(suggestion.suggestion_class, "UNDERSTAND_DATA")
        self.assertEqual(suggestion.observation_key, "context:stress")
        self.assertEqual(suggestion.proactive_state, ProactiveInsightState.STATE_NEW)
        self.assertIsNone(suggestion.change_since_review)
        self.assertEqual(
            suggestion.evidence_context.provenance.evidence_id,
            "rule.personal-response.repetition.v1",
        )
        self.assertEqual(
            suggestion.evidence_context.provenance.producer,
            "diabetes.personal_response.v1",
        )
        self.assertIn(
            "no_medication_or_insulin_dose_change_authority",
            suggestion.limitations,
        )
        self.assertNotIn(
            suggestion.suggestion_class,
            {"COLLECT_MISSING_DATA", "LEARN", "FOLLOW_UP_RECORD"},
        )

    def test_same_material_state_never_creates_a_second_suggestion(self):
        self._stress_pattern()
        self._log(days_ago=3, glucose=110)

        first = evaluate_companion_smart_suggestion(
            patient_id=self.patient.id,
            evaluated_at=self.now,
        )
        second = evaluate_companion_smart_suggestion(
            patient_id=self.patient.id,
            evaluated_at=self.now + timedelta(hours=25),
        )

        self.assertEqual(first.status, "suggested")
        self.assertEqual(second.status, "no_change")
        self.assertIsNone(second.suggestion)

    def test_review_worthy_persistence_uses_existing_clinician_discussion_authority(self):
        self._stress_pattern()
        self._log(days_ago=5, glucose=110)
        evaluate_companion_smart_suggestion(
            patient_id=self.patient.id,
            evaluated_at=self.now,
        )

        self._log(days_ago=3, glucose=180, stressed="yes")
        self._log(days_ago=4, glucose=190, stressed="yes")
        result = evaluate_companion_smart_suggestion(
            patient_id=self.patient.id,
            evaluated_at=self.now + timedelta(hours=25),
        )

        self.assertEqual(result.status, "suggested")
        assert result.suggestion is not None
        self.assertEqual(
            result.suggestion.suggestion_class,
            "PREPARE_CLINICIAN_DISCUSSION",
        )
        self.assertEqual(
            result.suggestion.reason,
            "existing_proactive_authority_marks_observation_review_worthy",
        )

    def test_attention_budget_still_allows_only_one_non_urgent_suggestion(self):
        for day, glucose in enumerate((150, 160, 170)):
            self._log(
                days_ago=day,
                glucose=glucose,
                stressed="yes",
                exercised="yes",
            )
        self._log(days_ago=3, glucose=110)

        first = evaluate_companion_smart_suggestion(
            patient_id=self.patient.id,
            evaluated_at=self.now,
        )
        blocked = evaluate_companion_smart_suggestion(
            patient_id=self.patient.id,
            evaluated_at=self.now + timedelta(hours=1),
        )
        next_day = evaluate_companion_smart_suggestion(
            patient_id=self.patient.id,
            evaluated_at=self.now + timedelta(hours=25),
        )

        self.assertEqual(first.status, "suggested")
        self.assertEqual(first.pending_count, 1)
        self.assertEqual(blocked.status, "cooldown")
        self.assertIsNone(blocked.suggestion)
        self.assertEqual(next_day.status, "suggested")
        assert first.suggestion is not None
        assert next_day.suggestion is not None
        self.assertNotEqual(
            first.suggestion.observation_key,
            next_day.suggestion.observation_key,
        )

    def test_eligible_resolution_maps_to_monitor_without_treatment_claim(self):
        supporting = self._stress_pattern()
        neutral = self._log(days_ago=3, glucose=110)
        evaluate_companion_smart_suggestion(
            patient_id=self.patient.id,
            evaluated_at=self.now,
        )

        LogEntry.objects.filter(id__in=[entry.id for entry in supporting]).update(
            logged_at=self.now - timedelta(days=100)
        )
        neutral.logged_at = self.now
        neutral.save(update_fields=("logged_at",))
        insufficient = evaluate_companion_smart_suggestion(
            patient_id=self.patient.id,
            evaluated_at=self.now + timedelta(hours=25),
        )
        self.assertEqual(insufficient.status, "insufficient_data")

        self._log(days_ago=1, glucose=115)
        self._log(days_ago=2, glucose=120)
        result = evaluate_companion_smart_suggestion(
            patient_id=self.patient.id,
            evaluated_at=self.now + timedelta(hours=50),
        )

        self.assertEqual(result.status, "suggested")
        assert result.suggestion is not None
        self.assertEqual(result.suggestion.suggestion_class, "MONITOR")
        self.assertEqual(result.suggestion.proactive_state, "resolved")
        self.assertEqual(
            result.suggestion.reason,
            "continue_observing_without_assuming_permanent_resolution",
        )
        self.assertIn(
            "no_diagnosis_causality_prediction_or_treatment_inference",
            result.suggestion.limitations,
        )

    def test_change_since_review_is_descriptive_metadata_not_new_authority(self):
        self._stress_pattern()
        self._log(days_ago=3, glucose=110)
        refresh_personal_response_memory(patient_id=self.patient.id)
        anchor = capture_companion_review_anchor(patient_id=self.patient.id)

        self.now = anchor.captured_at + timedelta(days=1)
        self._log(days_ago=0, glucose=175, stressed="yes")
        result = evaluate_companion_smart_suggestion(
            patient_id=self.patient.id,
            evaluated_at=self.now,
        )

        self.assertEqual(result.status, "suggested")
        assert result.suggestion is not None
        self.assertEqual(result.suggestion.change_since_review, "persisting")
        self.assertIn(
            result.suggestion.suggestion_class,
            ACTIVE_V1_SUGGESTION_CLASSES,
        )

    def test_downstream_validation_failure_rolls_back_attention_consumption(self):
        self._stress_pattern()
        self._log(days_ago=3, glucose=110)

        with patch(
            "diabetes.services.clinical.companion_smart_suggestions._matching_pattern",
            side_effect=ValueError("tampered provenance"),
        ):
            with self.assertRaisesRegex(ValueError, "tampered provenance"):
                evaluate_companion_smart_suggestion(
                    patient_id=self.patient.id,
                    evaluated_at=self.now,
                )

        self.assertFalse(
            ProactiveInsightState.objects.filter(
                observation__patient=self.patient,
            ).exists()
        )

    def test_public_entrypoint_has_no_generative_or_free_text_authority_input(self):
        parameters = tuple(signature(evaluate_companion_smart_suggestion).parameters)
        self.assertEqual(parameters, ("patient_id", "evaluated_at"))

    def test_invalid_patient_id_fails_closed(self):
        for value in (0, -1, True, "1", None):
            with self.assertRaises(ValueError):
                evaluate_companion_smart_suggestion(patient_id=value)  # type: ignore[arg-type]
