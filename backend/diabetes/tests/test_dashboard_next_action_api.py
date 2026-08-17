from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase


class DashboardNextActionApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.patient = User.objects.create_user(username="dashboard-next-action")
        self.client.force_login(self.patient)

    def test_next_action_is_post_only_and_never_a_passive_dashboard_read(self):
        response = self.client.get("/api/v1/companion/next-action/evaluate/")
        self.assertEqual(response.status_code, 405)

    @patch("diabetes.api.v1.companion.evaluate_companion_smart_suggestion")
    def test_explicit_post_returns_only_bounded_v1_suggestion(self, evaluate):
        evaluate.return_value = SimpleNamespace(
            status="suggested",
            attention_budget="one_non_urgent_item_per_24h",
            pending_count=0,
            suggestion=SimpleNamespace(
                suggestion_class="PREPARE_CLINICIAN_DISCUSSION",
                observation_key="context:stress",
                reason="existing_proactive_authority_marks_observation_review_worthy",
                proactive_state="persisting",
                change_since_review="persisting",
                missing_data=("meal_context",),
                limitations=(
                    "no_diagnosis_causality_prediction_or_treatment_inference",
                    "no_medication_or_insulin_dose_change_authority",
                ),
                proactive_source_version="proactive.personal-response.lifecycle.v1",
                pattern_source_version="companion-patterns.v1",
                source_version="companion-smart-suggestions.v1",
            ),
        )

        response = self.client.post("/api/v1/companion/next-action/evaluate/")

        self.assertEqual(response.status_code, 200)
        evaluate.assert_called_once_with(patient_id=self.patient.id)
        payload = response.json()
        self.assertEqual(payload["status"], "suggested")
        self.assertEqual(
            payload["suggestion"]["suggestion_class"],
            "PREPARE_CLINICIAN_DISCUSSION",
        )
        self.assertEqual(payload["suggestion"]["observation_key"], "context:stress")
        self.assertIn("may consume", payload["safety_notice"])
        self.assertIn("never diagnoses", payload["safety_notice"])

    @patch("diabetes.api.v1.companion.evaluate_companion_smart_suggestion")
    def test_cooldown_and_insufficient_states_do_not_fabricate_an_action(self, evaluate):
        for status in ("cooldown", "no_change", "insufficient_data"):
            with self.subTest(status=status):
                evaluate.reset_mock()
                evaluate.return_value = SimpleNamespace(
                    status=status,
                    attention_budget="one_non_urgent_item_per_24h",
                    pending_count=1 if status == "cooldown" else 0,
                    suggestion=None,
                )
                response = self.client.post(
                    "/api/v1/companion/next-action/evaluate/"
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["status"], status)
                self.assertIsNone(response.json()["suggestion"])
                evaluate.assert_called_once_with(patient_id=self.patient.id)
