"""V1-01 regression: all patient-visible AI-summary KPI claims require CGM proof."""

from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from ai.api.v1.ai import SummaryRequest, get_summary
from diabetes.services.clinical.cgm_eligibility import CgmWindowSufficiency
from diabetes.services.clinical.sql_analytics import AnalyticalKPIs


class SummaryKpiAuthorityTests(SimpleTestCase):
    @staticmethod
    def _raw_manual_kpis() -> AnalyticalKPIs:
        # Deliberately high manual-sample count. It never establishes CGM wear time.
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

    def test_manual_only_summary_does_not_publish_raw_cgm_metrics(self):
        raw = self._raw_manual_kpis()
        window = CgmWindowSufficiency(
            verified=False,
            reason="no_verified_sensor_session",
            window_days=14.0,
            active_window_pct=0.0,
            capture_pct=0.0,
            coverage_pct=0.0,
            expected_readings=0,
            received_readings=0,
            session_count=0,
            gap_count=0,
            evidence_id="source.ada.2026.section6",
        )
        request = SimpleNamespace(user=SimpleNamespace(id=42))

        with (
            patch("ai.api.v1.ai._get_patient_language", return_value="fr"),
            patch("ai.api.v1.ai.compute_kpis", return_value=raw),
            patch(
                "ai.api.v1.ai.run_clinical_analysis",
                return_value=SimpleNamespace(patterns=[]),
            ),
            patch(
                "ai.api.v1.ai.compress",
                return_value=SimpleNamespace(full_pivot_text="synthetic safe context"),
            ),
            patch("ai.api.v1.ai._call_llm_for_summary", return_value=[]),
            patch("core.medical_safety.sanitize_patient_visible", return_value=[]),
            patch("ai.api.v1.ai.compute_agp_profile", return_value=[]),
            patch("ai.api.v1.ai.compute_daily_averages", return_value=[]),
            patch("ai.api.v1.ai.track"),
            patch("ai.api.v1.ai.get_ai_provider_name", return_value="fallback"),
            patch(
                "diabetes.api.v1.kpis.assess_cgm_window",
                return_value=window,
            ) as window_check,
            patch(
                "diabetes.api.v1.kpis.compute_verified_cgm_metrics"
            ) as verified_metric_engine,
        ):
            # Unit-test the actual endpoint implementation without executing its
            # consent decorator: zero network/LLM calls, fixed synthetic patient.
            response = get_summary.__wrapped__(request, SummaryRequest(days=14))

        public = response["kpis"]
        self.assertEqual(public["avg_glucose"], 130.0)
        self.assertEqual(public["log_count"], 60)
        self.assertEqual(public["days_with_data"], 14)
        for field in (
            "cv_pct", "tir_pct", "tar_pct", "tbr_pct", "gmi", "gmi_confidence"
        ):
            with self.subTest(field=field):
                self.assertIsNone(public[field])
        self.assertIn("CGM", public["gmi_basis"])
        window_check.assert_called_once()
        self.assertEqual(window_check.call_args.kwargs["patient_id"], 42)
        verified_metric_engine.assert_not_called()
