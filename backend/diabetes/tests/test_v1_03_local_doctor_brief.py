"""V1-03 synthetic regression: Doctor Brief stays local and patient-isolated.

Clinical wording and native translations are candidates pending specialist review.
"""
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from diabetes.models import LogEntry
from diabetes.services.clinical.doctor_brief_local import build_local_doctor_brief
from diabetes.services.clinical.sql_analytics import AnalyticalKPIs


class V103LocalDoctorBriefTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="v1-03-doctor-local")
        self.other = User.objects.create_user(username="v1-03-other")

    def _seed(self, patient, *, count, glucose):
        for i in range(count):
            LogEntry.objects.create(
                patient=patient,
                blood_sugar=glucose,
                logged_at=timezone.now() - timedelta(days=i % 5, minutes=2),
                source="manual",
            )

    def test_authenticated_doctor_brief_never_accesses_model_even_without_ai_consent(self):
        self._seed(self.patient, count=5, glucose=125)
        self._seed(self.other, count=8, glucose=280)
        self.client.force_login(self.patient)
        # No global AI consent is present: local facts remain available.
        with (
            patch(
                "core.llm_gateway.GatewayLLM.complete",
                side_effect=AssertionError("Patient data sent to model gateway"),
            ) as gateway,
            patch(
                "llm.factory.get_llm",
                side_effect=AssertionError("Doctor Brief initialized a model"),
            ) as factory,
        ):
            response = self.client.get("/api/v1/ai/doctor-brief?days=14")

        self.assertEqual(response.status_code, 200, response.content[:500])
        data = response.json()
        self.assertEqual(data["days"], 14)
        self.assertTrue(data["has_sufficient_data"])
        self.assertIn("5 mesures", data["doctor_brief"])
        self.assertIn("125.0 mg/dL", data["doctor_brief"])
        self.assertNotIn("280.0", str(data))
        self.assertNotIn("CGM", data["key_insight"])
        self.assertNotIn("insuline", str(data).lower())
        gateway.assert_not_called()
        factory.assert_not_called()

    def test_insufficient_data_remains_local_without_fabricated_clinical_claims(self):
        self.client.force_login(self.patient)
        with patch(
            "core.llm_gateway.GatewayLLM.complete",
            side_effect=AssertionError("Unexpected model egress"),
        ) as gateway:
            response = self.client.get("/api/v1/ai/doctor-brief?days=14")

        self.assertEqual(response.status_code, 200, response.content[:500])
        data = response.json()
        self.assertFalse(data["has_sufficient_data"])
        self.assertEqual(data["doctor_brief"], "")
        self.assertEqual(data["key_insight"], "")
        self.assertIn("Pas assez", data["narrative"])
        gateway.assert_not_called()

    def test_unauthenticated_request_stays_denied(self):
        response = self.client.get("/api/v1/ai/doctor-brief?days=14")
        self.assertEqual(response.status_code, 401)

    def test_local_formatter_never_promotes_raw_cgm_kpis_in_four_locales(self):
        fake = AnalyticalKPIs(
            avg_glucose=123.0,
            std_dev=80.0,
            cv_pct=65.0,
            tir_pct=72.0,
            tar_pct=24.0,
            tbr_pct=4.0,
            gmi=7.6,
            log_count=10,
            days_with_data=4,
            cgm_active_pct=95.0,
        )
        for language in ("fr", "en", "ar", "ar-MA"):
            with self.subTest(language=language):
                result = build_local_doctor_brief(fake, days=14, language=language)
                joined = " ".join(result.values())
                self.assertIn("123.0 mg/dL", joined)
                for unverified in ("65.0%", "72.0%", "24.0%", "4.0%", "7.6%", "95.0%"):
                    self.assertNotIn(unverified, joined)
                self.assertEqual(result["key_insight"].count("10"), 1)
                self.assertTrue(result["narrative"])
