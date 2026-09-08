"""P1-EVIDENCE runtime gates: descriptive rows must not become normative CGM truth."""
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from diabetes.services.clinical.cgm_analytics import VerifiedCgmMetrics
from diabetes.services.clinical.cgm_eligibility import CgmWindowSufficiency
from diabetes.services.clinical.evidence_engine import EvidenceGuardedDiabetesEngine
from diabetes.services.clinical.evidence_projection import (
    guard_normative_kpis,
    project_public_kpis,
)
from diabetes.services.clinical.sql_analytics import AnalyticalKPIs


def _raw_cgm_like_kpis() -> AnalyticalKPIs:
    """Snapshot that would have passed the former row-fraction proxy gate."""
    return AnalyticalKPIs(
        avg_glucose=154.0,
        std_dev=62.0,
        cv_pct=40.3,
        tir_pct=68.0,
        tar_pct=25.0,
        tbr_pct=7.0,
        gmi=7.0,
        log_count=100,
        days_with_data=21,
        gri=47.0,
        gri_zone="C",
        gri_label="Risque intermédiaire",
        tbr_level2_pct=2.0,
        tbr_level1_pct=5.0,
        tar_level1_pct=18.0,
        tar_level2_pct=7.0,
        cgm_active_pct=100.0,
    )


def _cgm_window(*, verified: bool) -> CgmWindowSufficiency:
    coverage = 100.0 if verified else 0.0
    received = 100 if verified else 0
    return CgmWindowSufficiency(
        verified=verified,
        reason="verified" if verified else "insufficient_coverage",
        window_days=21.0,
        active_window_pct=coverage,
        capture_pct=coverage,
        coverage_pct=coverage,
        expected_readings=100,
        received_readings=received,
        session_count=1,
        gap_count=0,
        evidence_id="rule.metric.gmi-cgm.v1",
    )


class EvidenceProjectionTests(SimpleTestCase):
    def test_row_fraction_never_proves_cgm_wear_time(self):
        raw = _raw_cgm_like_kpis()
        public = project_public_kpis(raw)

        self.assertFalse(public["cgm_sufficiency"]["verified"])
        self.assertEqual(public["cgm_row_fraction_pct"], 100.0)
        self.assertEqual(public["recorded_range_pct"], 68.0)
        self.assertEqual(public["recorded_cv_pct"], 40.3)
        self.assertIsNone(public["tir_pct"])
        self.assertIsNone(public["cv_pct"])
        self.assertIsNone(public["gmi"])
        self.assertIsNone(public["gri"])
        self.assertIsNone(public["gmi_confidence"])
        self.assertEqual(public["gmi_basis"], "couverture CGM non vérifiée")

    def test_guard_removes_every_normative_cgm_field(self):
        guarded = guard_normative_kpis(_raw_cgm_like_kpis())
        for value in (
            guarded.cv_pct,
            guarded.tir_pct,
            guarded.tar_pct,
            guarded.tbr_pct,
            guarded.gmi,
            guarded.gri,
            guarded.gri_zone,
            guarded.gri_label,
            guarded.tbr_level2_pct,
            guarded.tbr_level1_pct,
            guarded.tar_level1_pct,
            guarded.tar_level2_pct,
        ):
            self.assertIsNone(value)
        self.assertEqual(guarded.avg_glucose, 154.0)
        self.assertEqual(guarded.std_dev, 62.0)
        self.assertEqual(guarded.log_count, 100)

    def test_verified_cgm_metrics_promote_governed_fields_but_not_candidates(self):
        raw = _raw_cgm_like_kpis()
        window = _cgm_window(verified=True)
        metrics = VerifiedCgmMetrics(
            cv_pct=33.3,
            tir_pct=72.0,
            tar_pct=20.0,
            tbr_pct=8.0,
            reading_count=100,
        )

        guarded = guard_normative_kpis(
            raw,
            cgm_window=window,
            cgm_metrics=metrics,
        )
        public = project_public_kpis(
            raw,
            cgm_window=window,
            cgm_metrics=metrics,
        )

        self.assertEqual(guarded.tir_pct, 72.0)
        self.assertEqual(guarded.cv_pct, 33.3)
        self.assertNotEqual(guarded.tir_pct, raw.tir_pct)
        self.assertNotEqual(guarded.cv_pct, raw.cv_pct)
        self.assertIsNone(guarded.gmi)
        self.assertIsNone(guarded.gri)
        self.assertIsNone(guarded.gri_zone)
        self.assertEqual(public["tir_pct"], 72.0)
        self.assertEqual(public["recorded_range_pct"], 68.0)
        self.assertIsNone(public["gmi"])
        self.assertIsNone(public["gri"])
        self.assertIsNone(public["gmi_confidence"])
        self.assertEqual(public["gmi_basis"], "règle GMI non promue")

    def test_projection_exposes_versioned_evidence_metadata(self):
        evidence = project_public_kpis(_raw_cgm_like_kpis())["evidence"]
        self.assertEqual(evidence["gmi"]["evidence_id"], "rule.metric.gmi-cgm.v1")
        self.assertEqual(
            evidence["tir_pct"]["evidence_id"],
            "rule.metric.recorded-range-fractions.v1",
        )
        self.assertIn("reviewed_at", evidence["gmi"])
        self.assertIn("population", evidence["gmi"])
        self.assertIn("modality", evidence["gmi"])


class EvidenceGuardedEngineTests(SimpleTestCase):
    @patch("diabetes.services.clinical.evidence_engine.assess_cgm_window")
    @patch("diabetes.services.clinical.evidence_engine.build_chat_context", return_value="descriptive")
    @patch("diabetes.services.clinical.evidence_engine.run_clinical_analysis_with_integrity")
    @patch("diabetes.services.clinical.evidence_engine.LogEntry.objects.filter")
    @patch("diabetes.services.clinical.evidence_engine.compute_kpis")
    def test_engine_closes_normative_cgm_paths_before_patterns_tone_and_trend(
        self,
        compute_kpis_mock,
        filter_mock,
        clinical_analysis_mock,
        build_context_mock,
        assess_window_mock,
    ):
        raw = _raw_cgm_like_kpis()
        compute_kpis_mock.return_value = raw
        assess_window_mock.return_value = _cgm_window(verified=False)
        filter_mock.return_value.order_by.return_value = []
        clinical_analysis_mock.return_value = (
            SimpleNamespace(patterns=[], insights=[]),
            [],
        )

        context = EvidenceGuardedDiabetesEngine().analyze(patient_id=7, language="fr", days=21)

        guarded_seen = clinical_analysis_mock.call_args.args[1]
        self.assertIsNone(guarded_seen.cv_pct)
        self.assertIsNone(guarded_seen.tir_pct)
        self.assertIsNone(guarded_seen.gmi)
        self.assertEqual(context.tone_signals, {"primary": None, "stability": None})
        self.assertEqual(context.trend, {})
        self.assertEqual(context.primary_label, "Recorded glucose")
        self.assertEqual(context.kpi_summary["recorded_range_pct"], 68.0)
        self.assertIsNone(context.kpi_summary["tir_pct"])
        build_context_mock.assert_called_once()

    @patch("diabetes.api.v1.kpis.assess_cgm_window")
    @patch("diabetes.api.v1.kpis.cache")
    @patch("diabetes.api.v1.kpis.compute_kpis")
    def test_kpi_endpoint_projection_returns_null_normative_fields(
        self,
        compute_kpis_mock,
        cache_mock,
        assess_window_mock,
    ):
        from diabetes.api.v1.kpis import get_kpis

        compute_kpis_mock.return_value = _raw_cgm_like_kpis()
        assess_window_mock.return_value = _cgm_window(verified=False)
        cache_mock.get.return_value = None
        request = SimpleNamespace(user=SimpleNamespace(id=9))

        result = get_kpis(request, days=21, target_low=70.0, target_high=180.0)

        self.assertIsNone(result["tir_pct"])
        self.assertIsNone(result["cv_pct"])
        self.assertIsNone(result["gmi"])
        self.assertIsNone(result["gri"])
        self.assertEqual(result["avg_glucose"], 154.0)
        cache_mock.set.assert_called_once()
