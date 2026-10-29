"""D19: AI-summary never promotes row-based glucose statistics into CGM metrics."""

from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from ai.api.v1.ai import SummaryRequest, SummaryResponse, get_summary
from diabetes.services.clinical.cgm_analytics import VerifiedCgmMetrics
from diabetes.services.clinical.cgm_eligibility import CgmWindowSufficiency
from diabetes.services.clinical.sql_analytics import AnalyticalKPIs


class SummaryCgmAuthorityTests(SimpleTestCase):
    @staticmethod
    def _raw() -> AnalyticalKPIs:
        # High-density manual entries still do not prove sensor wear-time.
        return AnalyticalKPIs(
            avg_glucose=130.0,
            std_dev=32.0,
            cv_pct=24.6,
            tir_pct=78.0,
            tar_pct=17.0,
            tbr_pct=5.0,
            gmi=6.4,
            log_count=60,
            days_with_data=14,
            cgm_active_pct=0.0,
        )

    @staticmethod
    def _window(verified: bool) -> CgmWindowSufficiency:
        return CgmWindowSufficiency(
            verified=verified,
            reason="verified" if verified else "no_verified_sensor_session",
            window_days=14.0,
            active_window_pct=100.0 if verified else 0.0,
            capture_pct=90.0 if verified else 0.0,
            coverage_pct=90.0 if verified else 0.0,
            expected_readings=4032 if verified else 0,
            received_readings=3629 if verified else 0,
            session_count=1 if verified else 0,
            gap_count=0,
            evidence_id="synthetic-test-source",
        )

    def _summary(self, *, verified=False, target_low=70.0, target_high=180.0):
        request = SimpleNamespace(user=SimpleNamespace(id=42))
        prompts = []
        observed = VerifiedCgmMetrics(
            cv_pct=17.3,
            tir_pct=84.4,
            tar_pct=12.2,
            tbr_pct=3.4,
            reading_count=3629,
        )
        with (
            patch("ai.api.v1.ai._get_patient_language", return_value="fr"),
            patch("ai.api.v1.ai.compute_kpis", return_value=self._raw()),
            patch(
                "ai.api.v1.ai.run_clinical_analysis",
                return_value=SimpleNamespace(patterns=[]),
            ) as analysis,
            patch(
                "ai.api.v1.ai._call_llm_for_summary",
                side_effect=lambda pivot, patterns, language: prompts.append(pivot) or [],
            ),
            patch("core.medical_safety.sanitize_patient_visible", return_value=[]),
            patch("ai.api.v1.ai.LogEntry.objects.filter") as logs,
            patch("ai.api.v1.ai.compute_daily_averages", return_value=[]),
            patch("ai.api.v1.ai.track"),
            patch("ai.api.v1.ai.get_ai_provider_name", return_value="fallback"),
            patch(
                "diabetes.api.v1.kpis.assess_cgm_window",
                return_value=self._window(verified),
            ) as window,
            patch(
                "diabetes.api.v1.kpis.compute_verified_cgm_metrics",
                return_value=observed,
            ) as sensor,
        ):
            logs.return_value.order_by.return_value = []
            result = get_summary.__wrapped__(
                request,
                SummaryRequest(days=14, target_low=target_low, target_high=target_high),
            )
        return result, prompts, analysis, window, sensor

    def test_manual_rows_cannot_publish_or_narrate_cgm_claims(self):
        result, prompts, analysis, window, sensor = self._summary()
        self.assertEqual(result["kpis"]["avg_glucose"], 130.0)
        self.assertEqual(result["kpis"]["log_count"], 60)
        for field in ("cv_pct", "tir_pct", "tar_pct", "tbr_pct", "gmi", "gmi_confidence"):
            with self.subTest(field=field):
                self.assertIsNone(result["kpis"][field])
        self.assertIn("CGM", result["kpis"]["gmi_basis"])
        self.assertEqual(result["agp_profile"], [])
        self.assertEqual(len(prompts), 1)
        for unsupported in ("78.0%", "24.6%", "6.4%", "CGM Time In Range"):
            self.assertNotIn(unsupported, prompts[0])
        self.assertIsNone(analysis.call_args.args[1].cv_pct)
        self.assertIsNone(analysis.call_args.args[1].tir_pct)
        self.assertIsNone(analysis.call_args.args[1].cgm_active_pct)
        window.assert_called_once()
        self.assertEqual(window.call_args.kwargs["patient_id"], 42)
        sensor.assert_not_called()
        SummaryResponse.model_validate(result)

    def test_verified_session_promotes_only_sensor_metrics_in_public_response(self):
        result, prompts, analysis, window, sensor = self._summary(verified=True)
        for key, value in (
            ("cv_pct", 17.3),
            ("tir_pct", 84.4),
            ("tar_pct", 12.2),
            ("tbr_pct", 3.4),
        ):
            self.assertEqual(result["kpis"][key], value)
        self.assertIsNone(result["kpis"]["gmi"])
        self.assertIsNone(result["kpis"]["gmi_confidence"])
        self.assertEqual(result["agp_profile"], [])
        self.assertNotIn("78.0%", prompts[0])
        self.assertIsNone(analysis.call_args.args[1].cv_pct)
        sensor.assert_called_once()
        self.assertEqual(sensor.call_args.kwargs["patient_id"], 42)
        self.assertEqual(sensor.call_args.kwargs["target_low"], 70.0)
        self.assertEqual(sensor.call_args.kwargs["target_high"], 180.0)
        window.assert_called_once()
        SummaryResponse.model_validate(result)

    def test_verified_session_with_different_target_stays_fail_closed(self):
        result, prompts, analysis, window, sensor = self._summary(
            verified=True, target_low=72.5
        )
        for field in ("cv_pct", "tir_pct", "tar_pct", "tbr_pct", "gmi"):
            self.assertIsNone(result["kpis"][field])
        self.assertNotIn("78.0%", prompts[0])
        self.assertEqual(result["agp_profile"], [])
        self.assertIsNone(analysis.call_args.args[1].tir_pct)
        sensor.assert_not_called()
        window.assert_called_once()
