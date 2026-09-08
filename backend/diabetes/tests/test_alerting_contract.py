from datetime import timedelta

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from core.registry import ModuleRegistry
from diabetes.models import LogEntry
from diabetes.services.clinical.alerting_authority import (
    EvidenceGuardedAlertingDiabetesEngine,
)
from diabetes.services.clinical.alerts import AlertLevel, AlertType, evaluate


class AlertStateMachineBoundaryTests(SimpleTestCase):
    def test_exact_thresholds_and_priority_are_deterministic(self):
        cases = (
            (53.9, None, AlertType.HYPO_SEVERE, AlertLevel.EMERGENCY),
            (54.0, None, AlertType.HYPO_MODERATE, AlertLevel.WARNING),
            (69.9, None, AlertType.HYPO_MODERATE, AlertLevel.WARNING),
            (70.0, None, None, AlertLevel.NONE),
            (250.0, [260, 270], None, AlertLevel.NONE),
            (251.0, [260, 270], AlertType.HYPER_SUSTAINED, AlertLevel.WARNING),
            (300.0, [260, 270], AlertType.HYPER_SUSTAINED, AlertLevel.WARNING),
            (300.1, [260, 270], AlertType.HYPER_SEVERE, AlertLevel.CRITICAL),
        )
        for glucose, history, alert_type, level in cases:
            with self.subTest(glucose=glucose):
                result = evaluate(glucose, recent_readings=history)
                self.assertEqual(result.alert_type, alert_type)
                self.assertEqual(result.level, level)

    def test_sustained_hyper_requires_two_prior_high_readings(self):
        self.assertEqual(evaluate(251, [260]).level, AlertLevel.NONE)
        self.assertEqual(evaluate(251, [249, 270]).level, AlertLevel.NONE)
        self.assertEqual(evaluate(251, [251, 252]).alert_type, AlertType.HYPER_SUSTAINED)

    def test_emergency_templates_do_not_invent_country_numbers(self):
        for value in (53, 301):
            response = evaluate(value)
            for message in (response.message_fr, response.message_darija):
                self.assertNotIn("112", message)
                self.assertNotIn("911", message)
                self.assertNotIn("15", message)


class RegisteredAlertAuthorityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="analysis2-alert-user")
        self.other = User.objects.create_user(username="analysis2-alert-other")
        self.now = timezone.now()

    def _entry(self, patient, glucose, minutes_ago):
        return LogEntry.objects.create(
            patient=patient,
            blood_sugar=glucose,
            logged_at=self.now - timedelta(minutes=minutes_ago),
        )

    def test_registry_uses_alert_correct_evidence_engine(self):
        registered = ModuleRegistry.get("diabetes")
        self.assertIs(registered.engine_class, EvidenceGuardedAlertingDiabetesEngine)

    def test_public_engine_reaches_sustained_hyper_from_same_patient_history(self):
        self._entry(self.user, 260, 30)
        self._entry(self.user, 270, 20)
        self._entry(self.other, 500, 10)
        current = self._entry(self.user, 251, 5)

        alert = ModuleRegistry.get("diabetes").engine_class().evaluate_alert(current)

        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, "warning")
        self.assertFalse(alert.blocking)
        self.assertEqual(alert.event_type, "alert")
        self.assertEqual(alert.value, 251.0)

    def test_public_engine_abstains_without_two_same_patient_prior_highs(self):
        self._entry(self.user, 260, 30)
        self._entry(self.other, 270, 20)
        current = self._entry(self.user, 251, 5)

        alert = ModuleRegistry.get("diabetes").engine_class().evaluate_alert(current)

        self.assertIsNone(alert)

    def test_severe_current_readings_keep_priority_and_block(self):
        self._entry(self.user, 260, 30)
        self._entry(self.user, 270, 20)

        severe_hypo = self._entry(self.user, 53, 10)
        hypo_alert = ModuleRegistry.get("diabetes").engine_class().evaluate_alert(severe_hypo)
        self.assertEqual(hypo_alert.severity, "emergency")
        self.assertTrue(hypo_alert.blocking)
        self.assertEqual(hypo_alert.event_type, "emergency")

        severe_hyper = self._entry(self.user, 301, 5)
        hyper_alert = ModuleRegistry.get("diabetes").engine_class().evaluate_alert(severe_hyper)
        self.assertEqual(hyper_alert.severity, "critical")
        self.assertTrue(hyper_alert.blocking)
        self.assertEqual(hyper_alert.event_type, "emergency")

    def test_supported_arabic_locales_use_arabic_message(self):
        current = self._entry(self.user, 53, 5)
        engine = ModuleRegistry.get("diabetes").engine_class()

        for language in ("ar-MA", "ar"):
            with self.subTest(language=language):
                alert = engine.evaluate_alert(current, language=language)
                self.assertIn("تنبيه", alert.message)
