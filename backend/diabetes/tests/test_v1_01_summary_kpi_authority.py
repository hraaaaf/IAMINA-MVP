"""V1-01 regression: all patient-visible AI-summary KPI claims require CGM proof."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from ai.api.v1.ai import SummaryRequest, SummaryResponse, get_doctor_brief, get_summary
from diabetes.api.v1.kpis import project_patient_kpis
from diabetes.services.clinical.cgm_analytics import VerifiedCgmMetrics
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
            patch("ai.api.v1.ai.LogEntry.objects.filter") as logs,
            patch("ai.api.v1.ai.compute_verified_cgm_agp_profile") as agp_engine,
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
            logs.return_value.order_by.return_value = []
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
        agp_engine.assert_not_called()
        self.assertEqual(SummaryResponse.model_validate(response).model_dump()["agp_profile"], [])


    def test_doctor_brief_prompt_omits_unverified_cgm_claims(self):
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
        request = SimpleNamespace(user=SimpleNamespace(id=43))
        llm = SimpleNamespace(
            complete=MagicMock(
                return_value=SimpleNamespace(
                    content=(
                        '{"narrative":"Recorded readings summarized.",'
                        '"key_insight":"The recorded glucose average is available.",'
                        '"doctor_brief":"Descriptive recorded values only."}'
                    )
                )
            )
        )

        with (
            patch("ai.api.v1.ai._get_patient_language", return_value="fr"),
            patch(
                "diabetes.services.clinical.sql_analytics.compute_kpis",
                return_value=raw,
            ),
            patch(
                "diabetes.services.clinical.engine.run_clinical_analysis",
                return_value=SimpleNamespace(patterns=[]),
            ),
            patch("ai.api.v1.ai.LogEntry.objects.filter") as logs,
            patch("companion.memory.IAminaMemory.load"),
            patch(
                "companion.tone.select_tone",
                return_value=SimpleNamespace(mode=SimpleNamespace(value="practical")),
            ),
            patch("companion.tone.get_tone_instruction", return_value=""),
            patch("ai.api.v1.ai.get_gateway_llm", return_value=llm),
            patch(
                "diabetes.api.v1.kpis.assess_cgm_window",
                return_value=window,
            ),
        ):
            logs.return_value.order_by.return_value = []
            get_doctor_brief.__wrapped__(request, days=14)

        llm.complete.assert_called_once()
        prompt = llm.complete.call_args.args[1]
        self.assertIn("RECORDED_AVG_GLUCOSE: 130.0 mg/dL", prompt)
        self.assertNotIn("TIR:", prompt)
        self.assertNotIn("CV:", prompt)
        self.assertNotIn("GMI", prompt)
        self.assertNotIn("78.0%", prompt)
        self.assertNotIn("24.6%", prompt)


    def test_verified_sensor_metrics_replace_raw_row_metrics_but_not_candidate_gmi(self):
        raw = self._raw_manual_kpis()
        window = CgmWindowSufficiency(
            verified=True,
            reason="verified",
            window_days=14.0,
            active_window_pct=100.0,
            capture_pct=90.0,
            coverage_pct=90.0,
            expected_readings=4032,
            received_readings=3629,
            session_count=1,
            gap_count=0,
            evidence_id="source.ada.2026.section6",
        )
        observed = VerifiedCgmMetrics(
            cv_pct=17.3,
            tir_pct=84.4,
            tar_pct=12.2,
            tbr_pct=3.4,
            reading_count=3629,
        )
        with (
            patch(
                "diabetes.api.v1.kpis.assess_cgm_window",
                return_value=window,
            ),
            patch(
                "diabetes.api.v1.kpis.compute_verified_cgm_metrics",
                return_value=observed,
            ) as sensor_engine,
        ):
            output = project_patient_kpis(
                patient_id=42, days=14,
                target_low=70.0, target_high=180.0,
                kpis=raw,
            )

        self.assertEqual(output["avg_glucose"], 130.0)
        self.assertEqual(output["cv_pct"], 17.3)
        self.assertEqual(output["tir_pct"], 84.4)
        self.assertEqual(output["tar_pct"], 12.2)
        self.assertEqual(output["tbr_pct"], 3.4)
        self.assertIsNone(output["gmi"])
        self.assertIsNone(output["gmi_confidence"])
        self.assertEqual(output["cgm_metric_reading_count"], 3629)
        sensor_engine.assert_called_once()
        self.assertEqual(sensor_engine.call_args.kwargs["patient_id"], 42)
        self.assertEqual(sensor_engine.call_args.kwargs["target_low"], 70.0)
        self.assertEqual(sensor_engine.call_args.kwargs["target_high"], 180.0)

    def test_verified_sensor_with_nonstandard_target_does_not_promote_metrics(self):
        raw = self._raw_manual_kpis()
        window = CgmWindowSufficiency(
            verified=True,
            reason="verified",
            window_days=14.0,
            active_window_pct=100.0,
            capture_pct=90.0,
            coverage_pct=90.0,
            expected_readings=4032,
            received_readings=3629,
            session_count=1,
            gap_count=0,
            evidence_id="source.ada.2026.section6",
        )
        with (
            patch(
                "diabetes.api.v1.kpis.assess_cgm_window",
                return_value=window,
            ),
            patch(
                "diabetes.api.v1.kpis.compute_verified_cgm_metrics"
            ) as sensor_engine,
        ):
            output = project_patient_kpis(
                patient_id=42, days=14,
                target_low=72.5, target_high=180.0,
                kpis=raw,
            )
        sensor_engine.assert_not_called()
        self.assertIsNone(output["tir_pct"])
        self.assertIsNone(output["cv_pct"])
        self.assertIsNone(output["gmi"])
