"""V1-03: synthetic proof that patient summary narration stays local.

This suite does not certify other AI routes, provider policy, or clinical wording.
"""

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from ai.api.v1.ai import _call_llm_for_summary
from diabetes.models import LogEntry
from diabetes.services.clinical.engine import ClinicalPattern, DiabetesEngine


class V103LocalSummaryTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="v1-03-local-summary")
        self.client.force_login(self.patient)

    def _seed_observed_morning_night_difference(self):
        anchor = timezone.now() - timedelta(days=1)
        for day in range(3):
            logged_at = (anchor - timedelta(days=day)).replace(
                hour=7, minute=0, second=0, microsecond=0
            )
            LogEntry.objects.create(
                patient=self.patient, blood_sugar=175, logged_at=logged_at
            )
        for day in range(2):
            logged_at = (anchor - timedelta(days=day)).replace(
                hour=23, minute=0, second=0, microsecond=0
            )
            LogEntry.objects.create(
                patient=self.patient, blood_sugar=100, logged_at=logged_at
            )

    def test_summary_with_real_synthetic_rows_never_calls_model_formatter(self):
        self._seed_observed_morning_night_difference()
        with (
            patch(
                "diabetes.services.clinical.engine.get_gateway_llm",
                side_effect=AssertionError("clinical engine attempted a model call"),
            ) as engine_gateway,
            patch(
                "ai.api.v1.ai.get_gateway_llm",
                side_effect=AssertionError("summary API attempted a model call"),
            ) as api_gateway,
            patch(
                "ai.api.v1.ai._call_llm_for_summary",
                side_effect=AssertionError("duplicate summary formatter attempted"),
            ) as duplicate_formatter,
            patch(
                "diabetes.services.clinical.engine._format_with_llm",
                side_effect=AssertionError("model formatter must be unreachable"),
            ) as llm_formatter,
        ):
            response = self.client.post(
                "/api/v1/ai/summary",
                data='{"days": 21}',
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200, response.content[:500])
        payload = response.json()
        self.assertEqual(payload["ai_provider"], "fallback")
        self.assertGreaterEqual(payload["kpis"]["log_count"], 5)
        self.assertIn(
            "MORNING_NIGHT_GLUCOSE_DIFFERENCE",
            {insight["code"] for insight in payload["insights"]},
        )
        engine_gateway.assert_not_called()
        api_gateway.assert_not_called()
        duplicate_formatter.assert_not_called()
        llm_formatter.assert_not_called()

    def test_empty_summary_does_not_initialize_a_model(self):
        with patch(
            "diabetes.services.clinical.engine.get_gateway_llm",
            side_effect=AssertionError("model initialized without patterns"),
        ) as gateway:
            response = self.client.post(
                "/api/v1/ai/summary",
                data='{"days": 21}',
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200, response.content[:500])
        self.assertEqual(response.json()["insights"], [])
        self.assertEqual(response.json()["ai_provider"], "fallback")
        gateway.assert_not_called()

    def _seed_unverified_cgm_fraction(self):
        # Provenance: 80% labeled CGM, but no CGM sensor-session proof.
        anchor = timezone.now() - timedelta(days=1)
        for index in range(100):
            logged_at = (anchor - timedelta(days=index % 16)).replace(
                hour=12, minute=0, second=0, microsecond=0
            )
            LogEntry.objects.create(
                patient=self.patient,
                blood_sugar=240 if index % 2 == 0 else 90,
                source="cgm" if index < 80 else "manual",
                logged_at=logged_at,
            )

    def test_cgm_row_fraction_without_sensor_window_cannot_promote_clinical_metrics(self):
        self._seed_unverified_cgm_fraction()
        with patch(
            "diabetes.services.clinical.engine.get_gateway_llm",
            side_effect=AssertionError("unverified CGM evidence reached a model"),
        ) as gateway:
            response = self.client.post(
                "/api/v1/ai/summary",
                data='{"days": 21}',
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200, response.content[:500])
        payload = response.json()
        self.assertEqual(payload["kpis"]["log_count"], 100)
        self.assertGreaterEqual(payload["kpis"]["days_with_data"], 14)
        self.assertIsNotNone(payload["kpis"]["avg_glucose"])
        for normative in ("cv_pct", "tir_pct", "tar_pct", "tbr_pct", "gmi"):
            self.assertIsNone(payload["kpis"][normative], normative)
        self.assertIsNone(payload["kpis"]["gmi_confidence"])
        self.assertNotIn(
            "CGM_HIGH_VARIABILITY",
            {insight["code"] for insight in payload["insights"]},
        )
        gateway.assert_not_called()

    def test_companion_context_does_not_claim_cgm_tir_without_sensor_evidence(self):
        self._seed_unverified_cgm_fraction()
        with patch(
            "diabetes.services.clinical.engine.get_gateway_llm",
            side_effect=AssertionError("companion generated patient narration"),
        ) as gateway:
            context = DiabetesEngine().analyze(self.patient.id, days=21)

        self.assertTrue(context.has_sufficient_data)
        self.assertEqual(context.kpi_summary["log_count"], 100)
        self.assertIsNotNone(context.kpi_summary["avg_glucose"])
        for normative in ("cv_pct", "tir_pct", "tar_pct", "tbr_pct", "gmi"):
            self.assertIsNone(context.kpi_summary[normative], normative)
        self.assertNotIn("CGM_HIGH_VARIABILITY", context.detected_patterns)
        self.assertNotIn("CGM TIR", context.pivot_text)
        self.assertEqual(context.trend, {})
        self.assertEqual(context.primary_label, "recorded_glucose")
        gateway.assert_not_called()

    def test_legacy_summary_helper_does_not_forward_patient_pivot(self):
        pattern = ClinicalPattern(
            code="SYNTHETIC_OBSERVATION",
            priority=1,
            icon="activity",
            title="Synthetic local-only observation",
            evidence="3 readings at 210 mg/dL",
            fallback_content="Synthetic observation; clinical cause unknown.",
            fallback_action="Record more context.",
        )
        with patch(
            "diabetes.services.clinical.engine._format_with_llm",
            side_effect=AssertionError("legacy helper accessed model"),
        ) as formatter:
            result = _call_llm_for_summary(
                "private-synthetic-pivot 210 mg/dL",
                [pattern],
                "fr",
            )

        self.assertEqual(result[0]["code"], "SYNTHETIC_OBSERVATION")
        self.assertNotIn("private-synthetic-pivot", str(result))
        formatter.assert_not_called()
