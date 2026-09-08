import datetime as dt
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from ninja.errors import HttpError
from pydantic import ValidationError

from core.models import BasePatientProfile
from diabetes.api.v1.profile import ProfilePatchSchema, patch_profile
from diabetes.models import DiabetesProfile
from diabetes.services.clinical.cgm_analytics import VerifiedCgmMetrics
from diabetes.services.clinical.cgm_eligibility import CgmWindowSufficiency
from diabetes.services.clinical.evidence_engine import EvidenceGuardedDiabetesEngine
from diabetes.services.clinical.sql_analytics import AnalyticalKPIs
from diabetes.services.clinical.target_applicability import (
    assess_target_authority,
    build_target_assessment,
    target_narration_evidence,
)


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
        reason="synthetic verified window",
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


class TargetAuthorityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="analysis6-target")
        self.base = BasePatientProfile.objects.create(
            patient=self.user,
            date_of_birth=dt.date(1980, 1, 1),
        )
        self.profile = DiabetesProfile.objects.create(
            base_profile=self.base,
            diabetes_type="type2",
            treatment_type="oral_meds",
        )

    def _confirm_target(self):
        self.profile.target_range_low = 80
        self.profile.target_range_high = 160
        self.profile.target_range_provenance = "clinician_confirmed"
        self.profile.target_population_context = "individualized"
        self.profile.target_time_in_range_goal_pct = 70.0
        self.profile.target_confirmed_at = timezone.now() - dt.timedelta(days=1)
        self.profile.save()

    def test_legacy_default_is_descriptive_only(self):
        authority = assess_target_authority(self.profile)
        self.assertFalse(authority.verified)
        self.assertEqual(authority.reason_code, "target_not_clinician_confirmed")
        self.assertEqual(authority.provenance, "legacy_default")

    def test_demographics_do_not_auto_infer_population_applicability(self):
        self.profile.target_range_provenance = "clinician_confirmed"
        self.profile.target_confirmed_at = timezone.now() - dt.timedelta(days=1)
        self.profile.target_time_in_range_goal_pct = 70.0
        self.profile.target_population_context = "unknown"
        self.profile.save()

        authority = assess_target_authority(self.profile)
        self.assertFalse(authority.verified)
        self.assertEqual(authority.reason_code, "target_population_unknown")

    def test_future_confirmation_fails_closed(self):
        self._confirm_target()
        self.profile.target_confirmed_at = timezone.now() + dt.timedelta(minutes=1)
        self.profile.save(update_fields=["target_confirmed_at"])

        authority = assess_target_authority(self.profile)
        self.assertFalse(authority.verified)
        self.assertEqual(authority.reason_code, "target_confirmation_future")

    def test_invalid_percentage_goal_fails_closed(self):
        self._confirm_target()
        self.profile.target_time_in_range_goal_pct = 101.0
        self.profile.save(update_fields=["target_time_in_range_goal_pct"])

        authority = assess_target_authority(self.profile)
        self.assertFalse(authority.verified)
        self.assertEqual(authority.reason_code, "target_percentage_goal_invalid")

    def test_clinician_confirmed_target_with_population_is_authorized(self):
        self._confirm_target()
        authority = assess_target_authority(self.profile)

        self.assertTrue(authority.verified)
        self.assertEqual(authority.reason_code, "target_authority_verified")
        self.assertEqual(authority.target_low_mg_dl, 80.0)
        self.assertEqual(authority.target_high_mg_dl, 160.0)
        self.assertEqual(authority.target_time_in_range_goal_pct, 70.0)

    def test_verified_authority_still_requires_verified_cgm(self):
        self._confirm_target()
        authority = assess_target_authority(self.profile)
        assessment = build_target_assessment(
            authority,
            cgm_verified=False,
            target_range_pct=80.0,
        )

        self.assertEqual(assessment["status"], "unavailable")
        self.assertEqual(assessment["reason_code"], "target_cgm_window_not_verified")
        self.assertEqual(target_narration_evidence(assessment), "")

    def test_confirmed_goal_comparison_is_explicit_and_non_prescriptive(self):
        self._confirm_target()
        authority = assess_target_authority(self.profile)
        assessment = build_target_assessment(
            authority,
            cgm_verified=True,
            target_range_pct=65.0,
        )
        evidence = target_narration_evidence(assessment)

        self.assertEqual(assessment["status"], "below_confirmed_goal")
        self.assertEqual(assessment["target_range_pct"], 65.0)
        self.assertIn("is below the recorded minimum goal", evidence)
        self.assertIn("does not diagnose", evidence)
        self.assertIn("does not", evidence)
        self.assertNotIn("increase your", evidence.lower())
        self.assertNotIn("decrease your", evidence.lower())


class TargetProfilePatchTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="analysis6-profile")
        self.base = BasePatientProfile.objects.create(
            patient=self.user,
            date_of_birth=dt.date(1980, 1, 1),
        )
        self.profile = DiabetesProfile.objects.create(
            base_profile=self.base,
            diabetes_type="type2",
            treatment_type="oral_meds",
            target_range_low=80,
            target_range_high=160,
            target_range_provenance="clinician_confirmed",
            target_population_context="individualized",
            target_time_in_range_goal_pct=70.0,
            target_confirmed_at=timezone.now() - dt.timedelta(days=1),
        )
        self.request = SimpleNamespace(user=self.user)

    @patch("diabetes.services.session_cache.invalidate")
    def test_patient_range_edit_downgrades_clinical_authority(self, _invalidate_mock):
        patch_profile(
            self.request,
            ProfilePatchSchema(target_range_low=85, target_range_high=165),
        )
        self.profile.refresh_from_db()

        self.assertEqual(self.profile.target_range_low, 85)
        self.assertEqual(self.profile.target_range_high, 165)
        self.assertEqual(self.profile.target_range_provenance, "patient_declared")
        self.assertEqual(self.profile.target_population_context, "unknown")
        self.assertIsNone(self.profile.target_time_in_range_goal_pct)
        self.assertIsNone(self.profile.target_confirmed_at)

    @patch("diabetes.services.session_cache.invalidate")
    def test_context_change_marks_clinician_confirmation_stale(self, _invalidate_mock):
        patch_profile(
            self.request,
            ProfilePatchSchema(diabetes_type="type1"),
        )
        self.profile.refresh_from_db()

        self.assertEqual(
            self.profile.target_range_provenance,
            "clinician_confirmation_stale",
        )
        self.assertEqual(self.profile.target_population_context, "unknown")
        self.assertIsNone(self.profile.target_time_in_range_goal_pct)
        self.assertIsNone(self.profile.target_confirmed_at)

    def test_public_patch_schema_rejects_internal_authority_fields(self):
        with self.assertRaises(ValidationError):
            ProfilePatchSchema.model_validate(
                {
                    "target_range_provenance": "clinician_confirmed",
                    "target_population_context": "individualized",
                    "target_time_in_range_goal_pct": 90,
                }
            )

    def test_crossed_range_is_rejected(self):
        with self.assertRaises(HttpError) as caught:
            patch_profile(
                self.request,
                ProfilePatchSchema(target_range_low=180, target_range_high=120),
            )
        self.assertEqual(caught.exception.status_code, 422)


class TargetAssessmentEngineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="analysis6-engine")
        self.base = BasePatientProfile.objects.create(
            patient=self.user,
            date_of_birth=dt.date(1980, 1, 1),
        )
        self.profile = DiabetesProfile.objects.create(
            base_profile=self.base,
            diabetes_type="type2",
            treatment_type="oral_meds",
            target_range_low=80,
            target_range_high=160,
            target_range_provenance="clinician_confirmed",
            target_population_context="individualized",
            target_time_in_range_goal_pct=70.0,
            target_confirmed_at=timezone.now() - dt.timedelta(days=1),
        )

    @patch("diabetes.services.clinical.evidence_engine.build_chat_context", return_value="base")
    @patch("diabetes.services.clinical.evidence_engine.run_clinical_analysis_with_integrity")
    @patch("diabetes.services.clinical.evidence_engine.assess_cgm_window")
    @patch("diabetes.services.clinical.evidence_engine.compute_kpis")
    @patch("diabetes.services.clinical.evidence_engine.compute_verified_cgm_metrics")
    def test_custom_confirmed_range_is_separate_from_standard_tir(
        self,
        compute_metrics_mock,
        compute_kpis_mock,
        assess_window_mock,
        clinical_analysis_mock,
        _build_context_mock,
    ):
        compute_kpis_mock.return_value = _raw_kpis()
        assess_window_mock.return_value = _verified_window()
        clinical_analysis_mock.return_value = (
            SimpleNamespace(patterns=[], insights=[]),
            [],
        )
        compute_metrics_mock.side_effect = [
            VerifiedCgmMetrics(
                cv_pct=32.0,
                tir_pct=75.0,
                tar_pct=20.0,
                tbr_pct=5.0,
                reading_count=337,
            ),
            VerifiedCgmMetrics(
                cv_pct=32.0,
                tir_pct=65.0,
                tar_pct=25.0,
                tbr_pct=10.0,
                reading_count=337,
            ),
        ]

        context = EvidenceGuardedDiabetesEngine().analyze(
            patient_id=self.user.id,
            language="en",
            days=14,
        )
        target = context.kpi_summary["target_assessment"]

        self.assertEqual(context.kpi_summary["tir_pct"], 75.0)
        self.assertEqual(target["target_range_pct"], 65.0)
        self.assertEqual(target["status"], "below_confirmed_goal")
        self.assertEqual(target["target_low_mg_dl"], 80.0)
        self.assertEqual(target["target_high_mg_dl"], 160.0)
        self.assertIn("CLINICIAN-CONFIRMED TARGET EVIDENCE", context.pivot_text)
        self.assertEqual(context.tone_signals, {"primary": None, "stability": None})
        self.assertEqual(context.analysis_status, "complete")

    @patch("diabetes.services.clinical.evidence_engine.build_chat_context", return_value="base")
    @patch("diabetes.services.clinical.evidence_engine.run_clinical_analysis_with_integrity")
    @patch("diabetes.services.clinical.evidence_engine.assess_cgm_window")
    @patch("diabetes.services.clinical.evidence_engine.compute_kpis")
    @patch("diabetes.services.clinical.evidence_engine.compute_verified_cgm_metrics")
    def test_target_metric_failure_is_partial_not_false_target_or_total_outage(
        self,
        compute_metrics_mock,
        compute_kpis_mock,
        assess_window_mock,
        clinical_analysis_mock,
        _build_context_mock,
    ):
        compute_kpis_mock.return_value = _raw_kpis()
        assess_window_mock.return_value = _verified_window()
        clinical_analysis_mock.return_value = (
            SimpleNamespace(patterns=[], insights=[]),
            [],
        )

        def metrics_side_effect(**kwargs):
            if kwargs.get("target_low") == 80.0:
                raise RuntimeError("synthetic target metric failure")
            return VerifiedCgmMetrics(
                cv_pct=32.0,
                tir_pct=75.0,
                tar_pct=20.0,
                tbr_pct=5.0,
                reading_count=337,
            )

        compute_metrics_mock.side_effect = metrics_side_effect

        context = EvidenceGuardedDiabetesEngine().analyze(
            patient_id=self.user.id,
            language="en",
            days=14,
        )
        target = context.kpi_summary["target_assessment"]

        self.assertEqual(context.kpi_summary["tir_pct"], 75.0)
        self.assertEqual(target["status"], "unavailable")
        self.assertEqual(target["reason_code"], "target_range_metric_unavailable")
        self.assertEqual(context.analysis_status, "partial")
        self.assertIn("target_metric_compute_failed", context.analysis_degradations)
        self.assertNotIn("CLINICIAN-CONFIRMED TARGET EVIDENCE", context.pivot_text)
