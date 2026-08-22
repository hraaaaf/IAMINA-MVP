"""
PHIPseudonymizer — unit tests.

Verifies that patient identity is scrubbed before LLM transmission
and correctly restored in the final output.
"""
from datetime import date

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase

from core.ai_egress import TEXT, ai_egress_scope
from core.models import BasePatientProfile
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
        self.assertNotEqual(token_a, token_b)

    def test_prompt_without_name_unchanged(self):
        _, safe = self.pz.mask_patient_identity("Yasmine", "Quelle est la glycémie normale ?")
        self.assertEqual(safe, "Quelle est la glycémie normale ?")

    def test_multiple_occurrences_all_replaced(self):
        _, safe = self.pz.mask_patient_identity("Leila", "Leila est là. Bonjour Leila.")
        self.assertNotIn("Leila", safe)

    def test_calibrated_identity_and_generic_identifiers_are_redacted(self):
        self.pz.calibrate(
            first_name="Nadia",
            last_name="Bennani",
            date_of_birth="1988-04-12",
            email="nadia@example.ma",
        )

        safe = self.pz.mask(
            "Nadia Bennani née le 12/04/1988, nadia@example.ma, "
            "CIN AB123456, téléphone +212 6 12 34 56 78, glycémie 126 mg/dL."
        )

        for forbidden in (
            "Nadia",
            "Bennani",
            "12/04/1988",
            "nadia@example.ma",
            "AB123456",
            "+212 6 12 34 56 78",
        ):
            self.assertNotIn(forbidden, safe)
        self.assertIn("126 mg/dL", safe)


class CurrentPatientBoundaryTest(TestCase):
    def test_current_patient_identity_is_redacted_without_manual_calibration(self):
        patient = User.objects.create_user(
            username="amina.patient",
            first_name="Amina",
            last_name="El Mansouri",
            email="amina@example.ma",
        )
        profile, _ = BasePatientProfile.objects.get_or_create(patient=patient)
        profile.date_of_birth = date(1990, 5, 14)
        profile.save(update_fields=["date_of_birth"])

        raw = (
            "Amina El Mansouri, 14/05/1990, amina@example.ma, "
            "CIN AB123456, téléphone 0612345678, glycémie 126 mg/dL."
        )
        with ai_egress_scope(patient.id, "document_ingest", TEXT):
            safe = PHIPseudonymizer().mask(raw)

        for forbidden in (
            "Amina",
            "El Mansouri",
            "14/05/1990",
            "amina@example.ma",
            "AB123456",
            "0612345678",
        ):
            self.assertNotIn(forbidden, safe)
        self.assertIn("126 mg/dL", safe)

    def test_user_identity_is_redacted_even_if_base_profile_row_is_missing(self):
        patient = User.objects.create_user(
            username="karim.patient",
            first_name="Karim",
            last_name="Alaoui",
            email="karim@example.ma",
        )
        BasePatientProfile.objects.filter(patient=patient).delete()

        with ai_egress_scope(patient.id, "document_ingest", TEXT):
            safe = PHIPseudonymizer().mask(
                "Karim Alaoui karim@example.ma, glycémie 118 mg/dL."
            )

        self.assertNotIn("Karim", safe)
        self.assertNotIn("Alaoui", safe)
        self.assertNotIn("karim@example.ma", safe)
        self.assertIn("118 mg/dL", safe)


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
        token, _ = self.pz.mask_patient_identity("Omar", "Omar est là.")
        self.pz.unmask_medical_report(f"Rapport pour {token}.")
        self.assertEqual(len(self.pz.session_map), 0)

    def test_unmask_with_no_token_in_report(self):
        self.pz.mask_patient_identity("Reda", "Reda, TIR 60%.")
        original = "Aucun résultat pertinent."
        restored = self.pz.unmask_medical_report(original)
        self.assertEqual(restored, original)

    def test_double_mask_restores_both(self):
        pz = PHIPseudonymizer()
        tok_a, _ = pz.mask_patient_identity("Alice", "Alice présente.")
        tok_b, _ = pz.mask_patient_identity("Bob", "Bob présente aussi.")
        report = f"{tok_a} et {tok_b} ont été vus."
        restored = pz.unmask_medical_report(report)
        self.assertIn("Alice", restored)
        self.assertIn("Bob", restored)
