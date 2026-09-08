"""ANALYSIS-0 execution-integrity tests for the active diabetes authority path."""
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase

from diabetes.services.clinical.analysis_integrity import (
    run_clinical_analysis_with_integrity,
)
from diabetes.services.clinical.evidence_engine import EvidenceGuardedDiabetesEngine


def _kpis(*, sufficient=True):
    return SimpleNamespace(
        has_sufficient_data=sufficient,
        cv_pct=None,
        days_with_data=0,
        cgm_active_pct=None,
        log_count=0,
    )


class AnalysisIntegrityRunnerTests(SimpleTestCase):
    def test_detector_failure_is_explicit_partial_evidence(self):
        broken = mock.MagicMock(__name__="detect_example", side_effect=RuntimeError("boom"))
        with (
            mock.patch(
                "diabetes.services.clinical.analysis_integrity.engine._ACTIVE_ENTRY_DETECTORS",
                (broken,),
            ),
            mock.patch(
                "diabetes.services.clinical.analysis_integrity.engine._high_variability_from_kpis",
                return_value=None,
            ),
        ):
            report, degradations = run_clinical_analysis_with_integrity([], _kpis())

        self.assertEqual(report.patterns, [])
        self.assertEqual(degradations, ["detector_failed_detect_example"])
        self.assertNotIn("boom", " ".join(degradations))

    def test_successful_empty_analysis_has_no_degradation(self):
        with (
            mock.patch(
                "diabetes.services.clinical.analysis_integrity.engine._ACTIVE_ENTRY_DETECTORS",
                (),
            ),
            mock.patch(
                "diabetes.services.clinical.analysis_integrity.engine._high_variability_from_kpis",
                return_value=None,
            ),
        ):
            report, degradations = run_clinical_analysis_with_integrity([], _kpis())

        self.assertEqual(report.patterns, [])
        self.assertEqual(degradations, [])


class EvidenceGuardedEngineIntegrityTests(SimpleTestCase):
    def test_kpi_failure_returns_unavailable_not_insufficient_data(self):
        with mock.patch(
            "diabetes.services.clinical.evidence_engine.compute_kpis",
            side_effect=RuntimeError("database unavailable"),
        ):
            context = EvidenceGuardedDiabetesEngine().analyze(123, language="fr")

        self.assertEqual(context.analysis_status, "unavailable")
        self.assertEqual(context.analysis_degradations, ["kpi_compute_failed"])
        self.assertFalse(context.has_sufficient_data)

    def test_valid_but_sparse_data_is_insufficient_not_unavailable(self):
        with mock.patch(
            "diabetes.services.clinical.evidence_engine.compute_kpis",
            return_value=_kpis(sufficient=False),
        ):
            context = EvidenceGuardedDiabetesEngine().analyze(123, language="fr")

        self.assertEqual(context.analysis_status, "insufficient_data")
        self.assertEqual(context.analysis_degradations, [])
        self.assertFalse(context.has_sufficient_data)

    def test_pipeline_failure_returns_unavailable(self):
        with (
            mock.patch(
                "diabetes.services.clinical.evidence_engine.compute_kpis",
                return_value=_kpis(sufficient=True),
            ),
            mock.patch(
                "diabetes.services.clinical.evidence_engine.assess_cgm_window",
                return_value=SimpleNamespace(verified=False),
            ),
            mock.patch(
                "diabetes.services.clinical.evidence_engine.project_public_kpis",
                side_effect=RuntimeError("projection failed"),
            ),
        ):
            context = EvidenceGuardedDiabetesEngine().analyze(123, language="fr")

        self.assertEqual(context.analysis_status, "unavailable")
        self.assertEqual(context.analysis_degradations, ["analysis_pipeline_failed"])

    def test_detector_degradation_propagates_as_partial(self):
        public = {
            "cgm_sufficiency": {"verified": False},
            "tir_pct": None,
            "cv_pct": None,
        }
        report = SimpleNamespace(patterns=[], insights=[])
        queryset = mock.MagicMock()
        queryset.order_by.return_value = []

        with (
            mock.patch(
                "diabetes.services.clinical.evidence_engine.compute_kpis",
                return_value=_kpis(sufficient=True),
            ),
            mock.patch(
                "diabetes.services.clinical.evidence_engine.assess_cgm_window",
                return_value=SimpleNamespace(verified=False),
            ),
            mock.patch(
                "diabetes.services.clinical.evidence_engine.project_public_kpis",
                return_value=public,
            ),
            mock.patch(
                "diabetes.services.clinical.evidence_engine.guard_normative_kpis",
                return_value=_kpis(sufficient=True),
            ),
            mock.patch(
                "diabetes.services.clinical.evidence_engine.LogEntry.objects.filter",
                return_value=queryset,
            ),
            mock.patch(
                "diabetes.services.clinical.evidence_engine.run_clinical_analysis_with_integrity",
                return_value=(report, ["detector_failed_detect_example"]),
            ),
            mock.patch(
                "diabetes.services.clinical.evidence_engine.build_chat_context",
                return_value="",
            ),
        ):
            context = EvidenceGuardedDiabetesEngine().analyze(123, language="fr")

        self.assertEqual(context.analysis_status, "partial")
        self.assertEqual(
            context.analysis_degradations,
            ["detector_failed_detect_example"],
        )
        self.assertTrue(context.has_sufficient_data)
