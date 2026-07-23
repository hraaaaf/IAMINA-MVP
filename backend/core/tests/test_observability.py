"""
Tests for core.observability — Phase 1 (track) + Phase 2 (ClinicalLogger).
"""

from unittest.mock import patch

from django.test import TestCase

from core.observability import (
    EVT_CHAT_MESSAGE,
    EVT_INACTIVE_7D,
    EVT_LOG_CREATED,
    EVT_SESSION_START,
    EVT_STREAK_BROKEN,
    EVT_STREAK_CONTINUED,
    EVT_SUMMARY_VIEWED,
    track,
)
from core.observability.events import ObservabilityEvent

# ══════════════════════════════════════════════════════════════════════════════
# Phase 1 — track() tests
# ══════════════════════════════════════════════════════════════════════════════

class TrackNominalTest(TestCase):
    """track() writes a row to the DB on success."""

    def test_track_nominal(self):
        track(EVT_LOG_CREATED, patient_id=42, props={"log_id": 1})
        self.assertTrue(
            ObservabilityEvent.objects.filter(
                event_type=EVT_LOG_CREATED,
                patient_id=42,
            ).exists()
        )

    def test_track_default_props(self):
        track(EVT_SESSION_START, patient_id=99)
        event = ObservabilityEvent.objects.get(event_type=EVT_SESSION_START, patient_id=99)
        self.assertEqual(event.props, {})

    def test_track_db_failure_is_swallowed(self):
        """track() must not raise even when the DB write fails."""
        with patch(
            "core.observability.events.ObservabilityEvent.objects.create",
            side_effect=Exception("boom"),
        ):
            with self.assertLogs("core.observability.events", level="WARNING") as log_ctx:
                # Should not raise
                track(EVT_LOG_CREATED, patient_id=1)
            self.assertTrue(
                any("track() failed" in line for line in log_ctx.output)
            )

    def test_track_no_phi_in_props(self):
        """Props must not contain PHI fields."""
        track(EVT_CHAT_MESSAGE, patient_id=7, props={"count": 1})
        event = ObservabilityEvent.objects.get(event_type=EVT_CHAT_MESSAGE, patient_id=7)
        self.assertNotIn("email", event.props)
        self.assertNotIn("name", event.props)

    def test_constants_are_strings(self):
        """All EVT_* constants are non-empty strings."""
        constants = [
            EVT_LOG_CREATED,
            EVT_SESSION_START,
            EVT_CHAT_MESSAGE,
            EVT_STREAK_CONTINUED,
            EVT_STREAK_BROKEN,
            EVT_SUMMARY_VIEWED,
            EVT_INACTIVE_7D,
        ]
        for c in constants:
            with self.subTest(constant=c):
                self.assertIsInstance(c, str)
                self.assertTrue(c)  # non-empty


# ══════════════════════════════════════════════════════════════════════════════
# Phase 2 — ClinicalLogger tests
# ══════════════════════════════════════════════════════════════════════════════

class ClinicalLoggerTest(TestCase):
    """ClinicalLogger emits to amina.clinical logger — zero DB writes."""

    def setUp(self):
        # Import here so Phase 2 tests fail clearly if ClinicalLogger not yet implemented
        from core.observability import ClinicalLogger
        self.ClinicalLogger = ClinicalLogger

    def test_clinical_logger_analysis_emits_log(self):
        with self.assertLogs("amina.clinical", level="INFO") as log_ctx:
            self.ClinicalLogger.analysis("hyperglycemia", 42, 3, 12.5)
        combined = " ".join(log_ctx.output)
        self.assertIn("clinical_analysis", combined)
        # Must not write to DB
        self.assertEqual(ObservabilityEvent.objects.count(), 0)

    def test_clinical_logger_emergency_emits_log(self):
        with self.assertLogs("amina.clinical", level="INFO") as log_ctx:
            self.ClinicalLogger.emergency("hypoglycemia", 5, "severe", "fr")
        combined = " ".join(log_ctx.output)
        self.assertIn("clinical_emergency", combined)

    def test_clinical_logger_llm_call_emits_log(self):
        with self.assertLogs("amina.clinical", level="INFO") as log_ctx:
            self.ClinicalLogger.llm_call("gemini", 512, 340.0, False)
        combined = " ".join(log_ctx.output)
        self.assertIn("llm_call", combined)

    def test_clinical_logger_middleware_intercept_emits_log(self):
        with self.assertLogs("amina.clinical", level="INFO") as log_ctx:
            self.ClinicalLogger.middleware_intercept("TriageVitalMiddleware", "emergency_glucose")
        combined = " ".join(log_ctx.output)
        self.assertIn("middleware_intercept", combined)

    def test_clinical_logger_no_db_write(self):
        """Calling all four ClinicalLogger methods must not create any ObservabilityEvent rows."""
        self.ClinicalLogger.analysis("hyperglycemia", 1, 2, 5.0)
        self.ClinicalLogger.emergency("hypoglycemia", 2, "mild", "ar-MA")
        self.ClinicalLogger.llm_call("kimi", 200, 100.0, True)
        self.ClinicalLogger.middleware_intercept("UnitGuardMiddleware", "unit_conversion")
        self.assertEqual(ObservabilityEvent.objects.count(), 0)
