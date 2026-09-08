from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from diabetes.services.clinical.cgm_analytics import VerifiedCgmMetrics
from diabetes.services.clinical.cgm_eligibility import CgmWindowSufficiency
from diabetes.services.clinical.evidence_engine import EvidenceGuardedDiabetesEngine
from diabetes.services.clinical.sql_analytics import AnalyticalKPIs


def _raw_kpis() -> AnalyticalKPIs:
    return AnalyticalKPIs(
        avg_glucose=145.0,
        std_dev=50.0,
        cv_pct=40.0,
        tir_pct=60.0,
        tar_pct=30.0,
        tbr_pct=10.0,
        gmi=7.2,
        log_count=100,
        days_with_data=14,
        cgm_active_pct=100.0,
    )


def _verified_window() -> CgmWindowSufficiency:
    return CgmWindowSufficiency(
        verified=True,
        reason="verified",
        window_days=14.0,
        active_window_pct=100.0,
        capture_pct=100.0,
        coverage_pct=100.0,
        expected_readings=337,
        received_readings=337,
        session_count=1,
        gap_count=0,
        evidence_id="rule.metric.gmi-cgm.v1",
    )


class A5TargetToneBoundaryTests(SimpleTestCase):
    @patch("diabetes.services.clinical.evidence_engine.build_chat_context", return_value="")
    @patch("diabetes.services.clinical.evidence_engine.run_clinical_analysis_with_integrity")
    @patch("diabetes.services.clinical.evidence_engine.LogEntry.objects.filter")
    @patch("diabetes.services.clinical.evidence_engine.compute_verified_cgm_metrics")
    @patch("diabetes.services.clinical.evidence_engine.assess_cgm_window")
    @patch("diabetes.services.clinical.evidence_engine.compute_kpis")
    def test_verified_tir_is_exposed_but_cannot_drive_target_tone_before_a6(
        self,
        compute_kpis_mock,
        assess_window_mock,
        compute_metrics_mock,
        filter_mock,
        clinical_analysis_mock,
        _build_context_mock,
    ):
        compute_kpis_mock.return_value = _raw_kpis()
        assess_window_mock.return_value = _verified_window()
        compute_metrics_mock.return_value = VerifiedCgmMetrics(
            cv_pct=32.0,
            tir_pct=75.0,
            tar_pct=20.0,
            tbr_pct=5.0,
            reading_count=337,
        )
        filter_mock.return_value.order_by.return_value = []
        clinical_analysis_mock.return_value = (
            SimpleNamespace(patterns=[], insights=[]),
            [],
        )

        engine = EvidenceGuardedDiabetesEngine()
        context = engine.analyze(patient_id=7, language="en", days=14)

        self.assertEqual(context.kpi_summary["tir_pct"], 75.0)
        self.assertEqual(context.kpi_summary["cv_pct"], 32.0)
        self.assertEqual(context.tone_signals, {"primary": None, "stability": None})
        self.assertNotIn("within target", engine.offline_fallback(context, language="en"))
