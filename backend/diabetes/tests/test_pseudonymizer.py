"""
PHIPseudonymizer — unit tests.

Verifies that patient identity is scrubbed before LLM transmission
and correctly restored in the final output.
"""
from django.test import SimpleTestCase

from llm.pseudonymizer import PHIPseudonymizer


class MaskPatientIdentityTest(SimpleTestCase):

    def setUp(self):
        self.pz = PHIPseudonymizer()

    def test_token_replaces_name_in_prompt(self):
        token, safe = self.pz.mask_patient_identity("Amina", "Bonjour Amina, ton taux est 140.")
        self.assertNotIn("Amina", safe)
        self.assertIn(token, safe)

    def test_token_starts_with_patient_prefix(self):
        token, _ = self.pz.mask_patient_identity("Karim", "Karim veut savoir.")
        self.assertTrue(token.startswith("PATIENT_"))

    def test_token_is_unique_per_call(self):
        pz2 = PHIPseudonymizer()
        token_a, _ = self.pz.mask_patient_identity("Alice", "Alice")
        token_b, _ = pz2.mask_patient_identity("Alice", "Alice")
        # Two separate instances produce different tokens (UUID-based)
        self.assertNotEqual(token_a, token_b)

    def test_prompt_without_name_unchanged(self):
        _, safe = self.pz.mask_patient_identity("Yasmine", "Quelle est la glycémie normale ?")
        # Name not present → prompt unmodified
        self.assertEqual(safe, "Quelle est la glycémie normale ?")

    def test_multiple_occurrences_all_replaced(self):
        _, safe = self.pz.mask_patient_identity("Leila", "Leila est là. Bonjour Leila.")
        self.assertNotIn("Leila", safe)


class UnmaskMedicalReportTest(SimpleTestCase):

    def setUp(self):
        self.pz = PHIPseudonymizer()

    def test_unmask_restores_name(self):
        token, _ = self.pz.mask_patient_identity("Nadia", "Nadia a un TIR de 72%.")
        report_with_token = f"Bonjour {token}, ton TIR est satisfaisant."
        restored = self.pz.unmask_medical_report(report_with_token)
        self.assertIn("Nadia", restored)
        self.assertNotIn(token, restored)

    def test_unmask_clears_session_map(self):
        """After unmask, session_map must be empty (security purge)."""
        token, _ = self.pz.mask_patient_identity("Omar", "Omar est là.")
        self.pz.unmask_medical_report(f"Rapport pour {token}.")
        self.assertEqual(len(self.pz.session_map), 0)

    def test_unmask_with_no_token_in_report(self):
        """Report containing no token should be returned as-is."""
        self.pz.mask_patient_identity("Reda", "Reda, TIR 60%.")
        original = "Aucun résultat pertinent."
        restored = self.pz.unmask_medical_report(original)
        self.assertEqual(restored, original)

    def test_double_mask_restores_both(self):
        """
        If two patients are masked in one session (edge case),
        both names should be restored in the final output.
        """
        pz = PHIPseudonymizer()
        tok_a, _ = pz.mask_patient_identity("Alice", "Alice présente.")
        tok_b, _ = pz.mask_patient_identity("Bob",   "Bob présente aussi.")
        report = f"{tok_a} et {tok_b} ont été vus."
        restored = pz.unmask_medical_report(report)
        self.assertIn("Alice", restored)
        self.assertIn("Bob",   restored)
