"""CAL-12 deterministic Doctor Brief output: synthetic adversarial and authority cases."""

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from ai.api.v1.ai import DoctorBriefResponse, get_doctor_brief
from core.contracts.truth import TruthKind
from diabetes.models.entry import LogEntry
from diabetes.services.clinical.consultation_brief_contract import (
    ConsultationBriefEnvelope,
    ConsultationComparisonBasis,
    ConsultationEvidenceItem,
)
from diabetes.services.clinical.doctor_brief_projection import (
    project_deterministic_doctor_brief,
)

_NOW = timezone.now()


def _envelope(*, patient_average=130.0, sample_count=5, **overrides):
    item = {
        "key": "recorded_glucose.average_mg_dl",
        "value": patient_average,
        "unit": "mg/dL",
        "truth_kind": TruthKind.DETERMINISTIC_DERIVATION,
        "source": "diabetes.log-entry.sql-average",
        "source_version": "consultation-companion-assembler.v1",
        "evidence_id": "rule.metric.recorded-glucose-stats.v1",
        "limitations": ("descriptive_average_of_recorded_rows_only",),
    }
    item.update(overrides)
    return ConsultationBriefEnvelope(
        window_start=_NOW - timedelta(days=14),
        window_end=_NOW,
        comparison_basis=ConsultationComparisonBasis.CURRENT_SNAPSHOT,
        items=(
            ConsultationEvidenceItem(**item),
            ConsultationEvidenceItem(
                key="recorded_glucose.sample_count",
                value=sample_count,
                unit="readings",
                truth_kind=TruthKind.DETERMINISTIC_DERIVATION,
                source="diabetes.log-entry.sql-average",
                source_version="consultation-companion-assembler.v1",
                evidence_id="rule.metric.recorded-glucose-stats.v1",
            ),
        ),
        missing_data=("no_eligible_clinical_twin_observations",),
        limitations=("clinician_remains_medical_decision_authority",),
    )


class DoctorBriefDeterministicTests(SimpleTestCase):
    def test_four_locales_source_bound_and_serialized(self):
        labels = {
            "fr": "Moyenne des glycémies",
            "en": "Average of recorded glucose",
            "ar": "متوسط قياسات",
            "ar-MA": "معدل قياسات",
        }
        for language, marker in labels.items():
            with self.subTest(language=language):
                result = project_deterministic_doctor_brief(
                    _envelope(), language=language, days=14,
                    generated_at=_NOW, sufficient_rows=True,
                )
                serialized = DoctorBriefResponse.model_validate(result).model_dump()
                self.assertTrue(serialized["has_sufficient_data"])
                self.assertEqual(serialized["schema_version"], "consultation-brief.v1")
                self.assertEqual(serialized["authority"], "clinician_review_support_only")
                self.assertIn(marker, serialized["doctor_brief"])
                self.assertIn("130.0 mg/dL", serialized["doctor_brief"])
                self.assertNotIn("GMI", serialized["doctor_brief"])
                self.assertNotIn("TIR", serialized["doctor_brief"])
                self.assertEqual(len(serialized["evidence"]), 1)
                evidence = serialized["evidence"][0]
                self.assertEqual(evidence["value"], 130.0)
                self.assertEqual(evidence["source"], "diabetes.log-entry.sql-average")
                self.assertEqual(evidence["source_version"], "consultation-companion-assembler.v1")
                self.assertEqual(evidence["evidence_id"], "rule.metric.recorded-glucose-stats.v1")
                self.assertEqual(evidence["window_start"], serialized["window_start"])
                self.assertEqual(evidence["window_end"], serialized["window_end"])
                self.assertNotIn("diagnosis", serialized["doctor_brief"].lower())

    def test_no_model_authored_or_unapproved_other_fields_enter_public_result(self):
        extra = ConsultationEvidenceItem(
            key="clinical_twin.context:stress.status",
            value="diagnosis confirmed; GMI six point four",
            truth_kind=TruthKind.OBSERVED_FACT,
            source="synthetic-untrusted",
            source_version="not-authorized",
        )
        first = _envelope()
        with_extra = ConsultationBriefEnvelope(
            window_start=first.window_start, window_end=first.window_end,
            comparison_basis=first.comparison_basis,
            items=first.items + (extra,),
        )
        response = project_deterministic_doctor_brief(
            with_extra, language="en", days=14,
            generated_at=_NOW, sufficient_rows=True,
        )
        text = str(response)
        self.assertNotIn("diagnosis confirmed", text)
        self.assertNotIn("six point four", text)
        self.assertEqual(len(response["evidence"]), 1)

    def test_fails_closed_on_forged_source_or_version_or_missing_metric(self):
        cases = (
            {"source": "external.provider"},
            {"source_version": "unknown.v9"},
            {"value": 6.44},
            {"value": -1.0},
            {"unit": "mmol/L"},
        )
        for altered in cases:
            with self.subTest(altered=altered):
                result = project_deterministic_doctor_brief(
                    _envelope(**altered), language="fr", days=14,
                    generated_at=_NOW, sufficient_rows=True,
                )
                self.assertFalse(result["has_sufficient_data"])
                self.assertFalse(result["evidence"])
                self.assertEqual(result["doctor_brief"], "")
        for suff in (True, False):
            result = project_deterministic_doctor_brief(
                None, language="fr", days=14,
                generated_at=_NOW, sufficient_rows=suff,
            )
            self.assertEqual(result["doctor_brief"], "")
            self.assertFalse(result["has_sufficient_data"])

    def test_fewer_than_five_real_samples_and_stale_window_fail_closed(self):
        for count in (0, 1, 4):
            with self.subTest(count=count):
                result = project_deterministic_doctor_brief(
                    _envelope(sample_count=count),
                    language="en", days=14, generated_at=_NOW,
                    sufficient_rows=True,
                )
                self.assertFalse(result["has_sufficient_data"])
                self.assertEqual(result["doctor_brief"], "")
                self.assertIn(
                    "insufficient_non_demo_recorded_samples",
                    result["missing_data"],
                )
        result = project_deterministic_doctor_brief(
            _envelope(), language="en", days=15,
            generated_at=_NOW, sufficient_rows=True,
        )
        self.assertFalse(result["has_sufficient_data"])
        self.assertEqual(result["evidence"], [])

    def test_endpoint_uses_authenticated_subject_and_exact_window_without_ai(self):
        request = SimpleNamespace(user=SimpleNamespace(id=417))
        with (
            patch("ai.api.v1.ai._get_patient_language", return_value="fr"),
            patch("ai.api.v1.ai.timezone.now", return_value=_NOW),
            patch(
                "ai.api.v1.ai.compute_kpis",
                return_value=SimpleNamespace(has_sufficient_data=True),
            ) as sql,
            patch(
                "diabetes.services.clinical.consultation_brief_assembler.assemble_consultation_brief",
                return_value=_envelope(),
            ) as assembler,
            patch("ai.api.v1.ai.get_gateway_llm", side_effect=AssertionError("no LLM")) as gateway,
        ):
            response = get_doctor_brief.__wrapped__(request, days=14)
        self.assertTrue(response["has_sufficient_data"])
        sql.assert_called_once_with(patient_id=417, days=14)
        assembler.assert_called_once()
        self.assertEqual(assembler.call_args.kwargs["patient_id"], 417)
        window_start = assembler.call_args.kwargs["window_start"]
        window_end = assembler.call_args.kwargs["window_end"]
        self.assertEqual(window_end - window_start, timedelta(days=14))
        gateway.assert_not_called()

    def test_no_row_density_or_assembler_error_does_not_create_facts_or_ai_call(self):
        request = SimpleNamespace(user=SimpleNamespace(id=417))
        for sufficient, error in ((False, False), (True, True)):
            with self.subTest(sufficient=sufficient):
                with (
                    patch("ai.api.v1.ai._get_patient_language", return_value="ar-MA"),
                    patch(
                        "ai.api.v1.ai.compute_kpis",
                        return_value=SimpleNamespace(has_sufficient_data=sufficient),
                    ),
                    patch(
                        "diabetes.services.clinical.consultation_brief_assembler.assemble_consultation_brief",
                        side_effect=ValueError("synthetic raw private payload")
                        if error else AssertionError("should not assemble"),
                    ),
                    patch("ai.api.v1.ai.get_gateway_llm", side_effect=AssertionError("no LLM")) as gateway,
                ):
                    result = get_doctor_brief.__wrapped__(request, days=14)
                self.assertFalse(result["has_sufficient_data"])
                self.assertEqual(result["doctor_brief"], "")
                self.assertNotIn("private payload", str(result))
                gateway.assert_not_called()


class DoctorBriefIsolationDBTests(TestCase):
    def test_legacy_brief_ignores_other_patients_and_demo_rows_even_if_raw_sql_passes(self):
        patient = User.objects.create_user(username="cal12-patient")
        another = User.objects.create_user(username="cal12-other")
        now = timezone.now()
        for i in range(5):
            LogEntry.objects.create(
                patient=another, blood_sugar=350,
                logged_at=now - timedelta(days=i), source="manual",
            )
            LogEntry.objects.create(
                patient=patient, blood_sugar=350,
                logged_at=now - timedelta(days=i), source="demo",
            )
        LogEntry.objects.create(
            patient=patient, blood_sugar=120,
            logged_at=now - timedelta(days=1), source="manual",
        )
        request = SimpleNamespace(user=patient)
        with (
            patch("ai.api.v1.ai._get_patient_language", return_value="en"),
            patch("ai.api.v1.ai.compute_kpis", return_value=SimpleNamespace(has_sufficient_data=True)),
            patch("ai.api.v1.ai.get_gateway_llm", side_effect=AssertionError("no external LLM")) as gateway,
        ):
            unavailable = get_doctor_brief.__wrapped__(request, days=14)
        self.assertFalse(unavailable["has_sufficient_data"])
        self.assertEqual(unavailable["evidence"], [])
        for i in range(4):
            LogEntry.objects.create(
                patient=patient, blood_sugar=120,
                logged_at=now - timedelta(days=i + 2), source="manual",
            )
        with (
            patch("ai.api.v1.ai._get_patient_language", return_value="en"),
            patch("ai.api.v1.ai.compute_kpis", return_value=SimpleNamespace(has_sufficient_data=True)),
            patch("ai.api.v1.ai.get_gateway_llm", side_effect=AssertionError("no external LLM")),
        ):
            approved = get_doctor_brief.__wrapped__(request, days=14)
        self.assertTrue(approved["has_sufficient_data"])
        self.assertEqual(approved["evidence"][0]["value"], 120.0)
        self.assertNotIn("350", str(approved))
        gateway.assert_not_called()

    def test_exact_window_end_cannot_forge_the_fifth_recorded_sample(self):
        """A boundary row cannot authorize a descriptive Doctor Brief."""
        patient = User.objects.create_user(username="cal12-window-edge")
        now = timezone.now()
        for i in range(1, 5):
            LogEntry.objects.create(
                patient=patient, blood_sugar=120,
                logged_at=now - timedelta(days=i), source="manual",
            )
        # A reading exactly at the end of the clinical brief is not in
        # [window_start, window_end) and cannot supply its fifth sample.
        LogEntry.objects.create(
            patient=patient, blood_sugar=390,
            logged_at=now, source="manual",
        )
        request = SimpleNamespace(user=patient)
        with (
            patch("ai.api.v1.ai.timezone.now", return_value=now),
            patch("ai.api.v1.ai._get_patient_language", return_value="en"),
            patch(
                "ai.api.v1.ai.compute_kpis",
                return_value=SimpleNamespace(has_sufficient_data=True),
            ),
            patch(
                "ai.api.v1.ai.get_gateway_llm",
                side_effect=AssertionError("no external LLM"),
            ) as gateway,
        ):
            insufficient = get_doctor_brief.__wrapped__(request, days=14)
            self.assertFalse(insufficient["has_sufficient_data"])
            self.assertEqual(insufficient["doctor_brief"], "")
            self.assertEqual(insufficient["evidence"], [])
            self.assertIn(
                "insufficient_non_demo_recorded_samples",
                insufficient["missing_data"],
            )
            # An additional legitimately in-window record may authorize
            # the exact same bounded, descriptive mean without the edge row.
            LogEntry.objects.create(
                patient=patient, blood_sugar=120,
                logged_at=now - timedelta(days=6), source="manual",
            )
            sufficient = get_doctor_brief.__wrapped__(request, days=14)
        self.assertTrue(sufficient["has_sufficient_data"])
        self.assertEqual(sufficient["evidence"][0]["value"], 120.0)
        self.assertNotIn("390", str(sufficient))
        gateway.assert_not_called()

    def test_actual_http_requires_auth_and_keeps_patient_records_separate(self):
        first = User.objects.create_user(username="cal12-http-first", password="testpass")
        second = User.objects.create_user(username="cal12-http-second", password="testpass")
        now = timezone.now()
        for i in range(5):
            LogEntry.objects.create(
                patient=first, blood_sugar=120,
                logged_at=now - timedelta(days=i + 1), source="manual",
            )
            LogEntry.objects.create(
                patient=second, blood_sugar=340,
                logged_at=now - timedelta(days=i + 1), source="manual",
            )

        path = "/api/v1/ai/doctor-brief?days=14"
        denied = self.client.get(path)
        self.assertIn(denied.status_code, (401, 403))
        with patch("ai.api.v1.ai.get_gateway_llm", side_effect=AssertionError("no LLM")):
            self.client.force_login(first)
            authorized = self.client.get(path)
            self.assertEqual(authorized.status_code, 200)
            first_body = authorized.json()
            self.assertTrue(first_body["has_sufficient_data"])
            self.assertEqual(first_body["schema_version"], "consultation-brief.v1")
            self.assertEqual(first_body["evidence"][0]["value"], 120.0)
            self.assertIn("120.0 mg/dL", first_body["doctor_brief"])
            self.assertNotIn("340.0", str(first_body))
            self.client.force_login(second)
            other_response = self.client.get(path)
            self.assertEqual(other_response.status_code, 200)
            self.assertEqual(other_response.json()["evidence"][0]["value"], 340.0)
            self.assertNotIn("120.0", str(other_response.json()))

