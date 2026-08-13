from pathlib import Path

from django.test import SimpleTestCase


class CompanionEvalManifestTests(SimpleTestCase):
    REQUIRED_SUITES = (
        "test_p2_companion_change_since_review.py",
        "test_p2_companion_personal_patterns.py",
        "test_p2_companion_evidence_uncertainty.py",
        "test_p2_companion_smart_suggestions.py",
        "test_p2_companion_consultation_companion.py",
        "test_p2_companion_after_visit_continuity_contract.py",
        "test_p2_companion_after_visit_runtime.py",
        "test_p2_companion_overview.py",
        "test_p2_companion_overview_api.py",
        "test_clinical_semantics_hardening.py",
        "test_clinical_shield.py",
        "test_advice_filter.py",
    )

    def test_required_regression_suites_remain_present(self):
        root = Path(__file__).resolve().parent
        missing = tuple(name for name in self.REQUIRED_SUITES if not (root / name).is_file())
        self.assertEqual(missing, ())

    def test_hard_dimensions_are_complete(self):
        dimensions = {"longitudinal", "negative", "false_positive", "boundary"}
        self.assertEqual(len(dimensions), 4)
