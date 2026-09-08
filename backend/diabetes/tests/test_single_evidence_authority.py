from pathlib import Path

from django.test import SimpleTestCase

from core.registry import ModuleRegistry
from diabetes.middleware.unit_guard import UnitConversionError, validate_mg_dl
from diabetes.services import summary as legacy_summary
from diabetes.services.clinical.alerting_authority import (
    EvidenceGuardedAlertingDiabetesEngine,
)


class SingleEvidenceAuthorityTests(SimpleTestCase):
    def test_registered_diabetes_engine_is_evidence_guarded_alert_authority(self):
        registered = ModuleRegistry.get("diabetes")
        self.assertIs(registered.engine_class, EvidenceGuardedAlertingDiabetesEngine)

    def test_legacy_summary_entry_points_fail_closed(self):
        calls = (
            lambda: legacy_summary.prepare_clinical_metrics([], 70, 180),
            lambda: legacy_summary.generate_ai_summary(object(), []),
            lambda: legacy_summary.generate_fallback_summary(object(), []),
        )
        for call in calls:
            with self.subTest(call=call):
                with self.assertRaises(legacy_summary.LegacyClinicalSummaryDisabled):
                    call()

    def test_legacy_unit_guard_helper_uses_canonical_range(self):
        self.assertEqual(validate_mg_dl(30), 30.0)
        self.assertEqual(validate_mg_dl(600), 600.0)
        for value in (20, 29.9, 600.1, 700):
            with self.subTest(value=value):
                with self.assertRaises(UnitConversionError):
                    validate_mg_dl(value)

    def test_raw_diabetes_engine_has_no_production_importers_except_evidence_wrapper(self):
        backend_dir = Path(__file__).resolve().parents[2]
        diabetes_dir = backend_dir / "diabetes"
        needle = "from diabetes.services.clinical.engine import DiabetesEngine"
        allowed = {
            diabetes_dir / "services" / "clinical" / "evidence_engine.py",
        }
        offenders = []
        for path in diabetes_dir.rglob("*.py"):
            if "tests" in path.parts or "migrations" in path.parts:
                continue
            if needle in path.read_text(encoding="utf-8") and path not in allowed:
                offenders.append(str(path.relative_to(backend_dir)))
        self.assertEqual(offenders, [])

    def test_retired_summary_contains_no_treatment_or_fabricated_claim_payload(self):
        summary_path = Path(legacy_summary.__file__)
        text = summary_path.read_text(encoding="utf-8")
        forbidden = (
            "Augmentez légèrement la dose",
            "Fixez vos ratios insuline",
            "5 pics hyperglycémiques",
            "Hypoglycémies nocturnes retardées",
        )
        for fragment in forbidden:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, text)
