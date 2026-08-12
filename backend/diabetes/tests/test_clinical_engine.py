"""End-to-end safety contracts for the diabetes clinical observation engine."""

from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase

from diabetes.services.clinical.engine import run_clinical_analysis
from diabetes.services.clinical.semantic_compressor import compress
from diabetes.services.clinical.sql_analytics import AnalyticalKPIs


def _kpis(**overrides):
    values = dict(
        avg_glucose=150.0,
        std_dev=30.0,
        cv_pct=20.0,
        tir_pct=70.0,
        tar_pct=25.0,
        tbr_pct=5.0,
        gmi=6.9,
        log_count=30,
        days_with_data=10,
        cgm_active_pct=0.0,
    )
    values.update(overrides)
    return AnalyticalKPIs(**values)


def _entry(
    hour,
    day,
    glucose,
    *,
    exercised="",
    source="manual",
):
    return SimpleNamespace(
        effective_time=datetime(2026, 4, 1) + timedelta(days=day, hours=hour),
        blood_sugar=Decimal(str(glucose)),
        meal_description="",
        exercised=exercised,
        sleep_quality="",
        stressed="",
        fatigue_level="",
        is_sick="",
        meal_type="",
        glycemic_context="",
        source=source,
    )


class EngineRuntimeAuthorityTests(SimpleTestCase):
    def test_empty_entries_keep_kpis_without_fabricating_normality(self):
        report = run_clinical_analysis([], _kpis())
        self.assertEqual(report.patterns, [])
        self.assertEqual(report.insights, [])

    def test_context_prototypes_are_not_in_active_summary_engine(self):
        entries = [
            SimpleNamespace(
                effective_time=datetime(2026, 4, 1) + timedelta(days=i, hours=12),
                blood_sugar=Decimal("220"),
                meal_description="couscous",
                exercised="",
                sleep_quality="bad",
                stressed="yes",
                fatigue_level="tired",
                is_sick="yes",
                meal_type="lunch",
                glycemic_context="post_meal",
                source="manual",
            )
            for i in range(4)
        ]
        with mock.patch(
            "diabetes.services.clinical.engine._format_with_llm",
            return_value=[],
        ):
            report = run_clinical_analysis(entries, _kpis())
        codes = {pattern.code for pattern in report.patterns}
        self.assertNotIn("GLUCOSE_WITH_RECORDED_STRESS", codes)
        self.assertNotIn("GLUCOSE_WITH_RECORDED_POOR_SLEEP", codes)
        self.assertNotIn("HIGH_GLUCOSE_WITH_RECORDED_MEAL_TEXT", codes)

    def test_sql_first_cgm_variability_requires_valid_wear(self):
        sparse = _kpis(
            cv_pct=44.0,
            log_count=200,
            days_with_data=7,
            cgm_active_pct=95.0,
        )
        with mock.patch(
            "diabetes.services.clinical.engine._format_with_llm",
            return_value=[],
        ):
            sparse_report = run_clinical_analysis([], sparse)
        self.assertNotIn(
            "CGM_HIGH_VARIABILITY",
            {pattern.code for pattern in sparse_report.patterns},
        )

        eligible = _kpis(
            cv_pct=44.0,
            log_count=1200,
            days_with_data=14,
            cgm_active_pct=90.0,
        )
        with mock.patch(
            "diabetes.services.clinical.engine._format_with_llm",
            return_value=[],
        ):
            eligible_report = run_clinical_analysis([], eligible)
        self.assertIn(
            "CGM_HIGH_VARIABILITY",
            {pattern.code for pattern in eligible_report.patterns},
        )

    def test_active_pattern_packet_contains_source_and_limitations(self):
        morning = [_entry(7, day, 175) for day in range(3)]
        night = [_entry(23, day, 105) for day in range(2)]
        with mock.patch(
            "diabetes.services.clinical.engine._format_with_llm",
            return_value=[],
        ):
            report = run_clinical_analysis(morning + night, _kpis())
        self.assertTrue(report.patterns)
        pattern = report.patterns[0]
        packet = pattern.narration_evidence().lower()
        self.assertIn("source=", packet)
        self.assertIn("limitations=", packet)
        self.assertNotIn("ajustement de", packet)
        self.assertNotIn("insuline basale", packet)

    def test_detector_exception_is_fail_soft_not_report_abort(self):
        morning = [_entry(7, day, 175) for day in range(3)]
        night = [_entry(23, day, 105) for day in range(2)]
        broken = mock.MagicMock(
            __name__="detect_dawn_phenomenon",
            side_effect=RuntimeError("boom"),
        )
        with mock.patch(
            "diabetes.services.clinical.engine._ACTIVE_ENTRY_DETECTORS",
            (broken,),
        ):
            report = run_clinical_analysis(morning + night, _kpis())
        self.assertIsNotNone(report)


class SemanticCompressorSafetyTests(SimpleTestCase):
    def test_no_patterns_does_not_claim_everything_normal(self):
        context = compress(_kpis(), [])
        summary = context.pattern_summary.lower()
        self.assertIn("does not mean", summary)
        self.assertNotIn("within normal range", summary)

    def test_manual_window_does_not_apply_cgm_target_judgment(self):
        context = compress(
            _kpis(
                cv_pct=44.0,
                days_with_data=14,
                cgm_active_pct=10.0,
            ),
            [],
        )
        self.assertIn("do not apply", context.kpi_summary.lower())
        self.assertNotIn("unstable (above ada threshold)", context.kpi_summary.lower())

    def test_eligible_cgm_window_can_state_general_reference(self):
        context = compress(
            _kpis(
                cv_pct=44.0,
                days_with_data=14,
                cgm_active_pct=90.0,
            ),
            [],
        )
        self.assertIn("ada 2026 general cgm reference", context.kpi_summary.lower())


class NoTreatmentSemanticsTests(SimpleTestCase):
    def test_every_active_pattern_is_observation_only(self):
        entries = [
            _entry(7, 0, 180),
            _entry(7, 1, 180),
            _entry(7, 2, 180),
            _entry(23, 0, 100),
            _entry(23, 1, 100),
        ]
        with mock.patch(
            "diabetes.services.clinical.engine._format_with_llm",
            return_value=[],
        ):
            report = run_clinical_analysis(entries, _kpis())
        text = " ".join(
            " ".join(
                (
                    p.title,
                    p.evidence,
                    p.fallback_content,
                    p.fallback_action,
                )
            )
            for p in report.patterns
        ).lower()
        for forbidden in (
            "insuline rapide",
            "insuline basale",
            "augmentez votre dose",
            "diminuez votre dose",
            "bolus",
            "traitez plutôt la cause",
        ):
            self.assertNotIn(forbidden, text)
