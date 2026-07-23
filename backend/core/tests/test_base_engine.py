"""
BaseEngine ABC seam — unit tests (DA-03 S1).

Covers:
  1. BaseEngine cannot be instantiated directly (ABC contract).
  2. DiabetesEngine is instantiable and is a proper subclass of BaseEngine.
  3. DiabetesEngine.analyze() delegates to run_clinical_analysis() and returns
     the same ClinicalReport.
"""
from decimal import Decimal
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase

from core.engine import BaseEngine
from diabetes.services.clinical.engine import DiabetesEngine, run_clinical_analysis
from diabetes.services.clinical.sql_analytics import AnalyticalKPIs

# ─────────────────────────────────────────────
# Helpers (mirrors test_clinical_engine.py style)
# ─────────────────────────────────────────────

def _dummy_kpis(**overrides):
    defaults = dict(
        avg_glucose=180.0, std_dev=20.0, cv_pct=11.0,
        tir_pct=85.0, tar_pct=10.0, tbr_pct=5.0,
        gmi=7.5, log_count=0, days_with_data=0,
    )
    defaults.update(overrides)
    return AnalyticalKPIs(**defaults)


# ─────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────

class BaseEngineABCTests(SimpleTestCase):
    """Test the ABC contract of BaseEngine."""

    def test_base_engine_cannot_be_instantiated(self):
        """Test 1: Directly instantiating BaseEngine must raise TypeError."""
        with self.assertRaises(TypeError):
            BaseEngine()  # type: ignore[abstract]

    def test_diabetes_engine_is_subclass_and_instantiable(self):
        """Test 2: DiabetesEngine is a proper subclass and can be instantiated."""
        self.assertTrue(issubclass(DiabetesEngine, BaseEngine))
        engine = DiabetesEngine()
        self.assertIsInstance(engine, BaseEngine)
        self.assertIsInstance(engine, DiabetesEngine)

    def test_analyze_returns_empty_domain_context_when_insufficient(self):
        """Test 3 (P4.5): analyze(patient_id) returns an empty DomainContext when
        the patient has insufficient data — no DB access beyond compute_kpis."""
        from core.contracts.domain_context import DomainContext

        insufficient = _dummy_kpis(log_count=0, days_with_data=0)  # <5 → insufficient
        with mock.patch(
            "diabetes.services.clinical.sql_analytics.compute_kpis",
            return_value=insufficient,
        ):
            result = DiabetesEngine().analyze(patient_id=1, language="fr", days=14)

        self.assertIsInstance(result, DomainContext)
        self.assertFalse(result.has_sufficient_data)
        self.assertEqual(result.language, "fr")

    def test_evaluate_alert_blocks_on_severe_hypo(self):
        """Test 4 (P4.5): severe hypoglycemia returns a blocking DomainAlert."""
        entry = type("E", (), {"blood_sugar": 45.0})()  # < 54 mg/dL
        alert = DiabetesEngine().evaluate_alert(entry, language="fr")
        self.assertIsNotNone(alert)
        self.assertTrue(alert.blocking)
        self.assertEqual(alert.value, 45.0)

    def test_evaluate_alert_none_when_normal(self):
        """Test 5 (P4.5): normal glucose raises no alert."""
        entry = type("E", (), {"blood_sugar": 110.0})()
        self.assertIsNone(DiabetesEngine().evaluate_alert(entry, language="fr"))
