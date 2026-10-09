"""CAL-12 final response guard for untraceable generated clinical numbers.

Synthetic provider output at the real endpoint handler: no network/PHI.
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from ai.api.v1.ai import (
    _fail_closed_unproven_doctor_brief_numbers,
    get_doctor_brief,
)


class DoctorBriefFinalOutputTests(SimpleTestCase):
    @staticmethod
    def _invoke(language, payload, public=None):
        raw = SimpleNamespace(
            has_sufficient_data=True, log_count=60, days_with_data=14,
        )
        approved = public or {
            "avg_glucose": 130.0, "tir_pct": None, "cv_pct": None,
        }
        gateway = SimpleNamespace(
            complete=MagicMock(
                return_value=SimpleNamespace(
                    content=json.dumps(payload, ensure_ascii=False)
                )
            )
        )
        request = SimpleNamespace(user=SimpleNamespace(id=417))
        with (
            patch("ai.api.v1.ai._get_patient_language", return_value=language),
            patch("diabetes.services.clinical.sql_analytics.compute_kpis", return_value=raw),
            patch("ai.api.v1.ai.project_patient_kpis", return_value=approved) as projection,
            patch(
                "diabetes.services.clinical.engine.run_clinical_analysis",
                return_value=SimpleNamespace(patterns=[]),
            ),
            patch("ai.api.v1.ai.LogEntry.objects.filter") as logs,
            patch("companion.memory.IAminaMemory.load"),
            patch(
                "companion.tone.select_tone",
                return_value=SimpleNamespace(
                    mode=SimpleNamespace(value="practical"),
                ),
            ),
            patch("companion.tone.get_tone_instruction", return_value=""),
            patch("ai.api.v1.ai.get_gateway_llm", return_value=gateway),
        ):
            logs.return_value.order_by.return_value = []
            response = get_doctor_brief.__wrapped__(request, days=14)
        projection.assert_called_once()
        gateway.complete.assert_called_once()
        return response, gateway.complete.call_args.args[1]

    def test_manual_only_numeric_claims_blocked_in_each_output_language(self):
        safe = {
            "narrative": "Recorded measurements are available.",
            "key_insight": "Descriptive observations only.",
            "doctor_brief": "For clinician discussion only.",
        }
        bad_cases = (
            ("fr", "narrative", "Le TIR est de 78%."),
            ("en", "key_insight", "Your GMI is 6.4%."),
            ("ar", "doctor_brief", "مؤشر السكر التقديري ٦٫٤٪"),
            ("ar-MA", "narrative", "TIR ٧٨٪ f had lmodda."),
        )
        for language, field, claim in bad_cases:
            with self.subTest(language=language, field=field):
                payload = dict(safe)
                payload[field] = claim
                response, prompt = self._invoke(language, payload)
                self.assertEqual(response[field], "")
                for other in safe.keys() - {field}:
                    self.assertEqual(response[other], safe[other])
                self.assertIn("RECORDED_AVG_GLUCOSE: 130.0 mg/dL", prompt)
                self.assertNotIn("VERIFIED_CGM_TIR", prompt)
                self.assertNotIn("VERIFIED_CGM_CV", prompt)

    def test_eligible_cgm_numbers_cannot_be_laundered_by_model_either(self):
        response, prompt = self._invoke(
            "en",
            {
                "narrative": "Recorded sensor data are available.",
                "key_insight": "TIR 84.4% is verified.",
                "doctor_brief": "CV 17.3% in this window.",
            },
            {
                "avg_glucose": 114.0, "tir_pct": 84.4, "cv_pct": 17.3,
            },
        )
        self.assertIn("VERIFIED_CGM_TIR: 84.4%", prompt)
        self.assertIn("VERIFIED_CGM_CV: 17.3%", prompt)
        self.assertEqual(response["narrative"], "Recorded sensor data are available.")
        self.assertEqual(response["key_insight"], "")
        self.assertEqual(response["doctor_brief"], "")

    def test_unicode_numbers_and_malformed_fields_fail_closed(self):
        self.assertEqual(
            _fail_closed_unproven_doctor_brief_numbers("Neutral prose."),
            "Neutral prose.",
        )
        for raw in (None, 6.4, ["6.4"], "GMI 6.4%", "TIR ٧٨٪", "TIR ۷۸٪", "Ⅵ%"):
            with self.subTest(value=raw):
                self.assertEqual(
                    _fail_closed_unproven_doctor_brief_numbers(raw),
                    "",
                )
