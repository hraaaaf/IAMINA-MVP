"""Clinical semantics hardening regression gates."""

from django.test import SimpleTestCase

from diabetes.services.clinical.alerts import AlertLevel, evaluate


class JurisdictionNeutralDiabetesAlertTests(SimpleTestCase):
    def test_diabetes_alert_layer_contains_no_france_specific_emergency_resource(self):
        responses = [
            evaluate(45),
            evaluate(65),
            evaluate(320),
            evaluate(260, recent_readings=[270, 280]),
        ]
        combined = " ".join(
            response.message_fr + " " + response.message_darija
            for response in responses
        ).lower()
        self.assertNotIn("samu", combined)
        self.assertNotIn("appelle le 15", combined)
        self.assertNotIn("عيط للإسعاف (15)", combined)
        self.assertIn("services d'urgence locaux", combined)

    def test_severe_low_remains_deterministic_emergency(self):
        response = evaluate(45)
        self.assertEqual(response.level, AlertLevel.EMERGENCY)
        self.assertTrue(response.action_required)
        self.assertTrue(response.call_emergency)

    def test_no_alert_for_in_range_value(self):
        self.assertEqual(evaluate(120).level, AlertLevel.NONE)
