from django.test import TestCase

from companion.prompts import LANGUAGE_LABELS, get_language_label
from diabetes.services.clinical.shield import ClinicalShield
from diabetes.services.clinical.unit_guard import UnitGuard


class ClinicalIntelligenceTest(TestCase):
    """
    Sprint 2 — Backend Tests (Phase 6)
    ==================================
    Unit tests for Unit Guard, Clinical Shield, and Prompt Language Layer.

    NOTE: normalize_to_pivot() (llm/pivot.py) was deleted in the P2 dead-code
    cleanup (2026-05-26). The pivot responsibility now lives in reactor.py which
    builds English Pivot Text inline. Tests for prompt language injection are
    provided here instead.
    """

    def test_unit_guard_conversions(self):
        # mg/dL -> mmol/L
        self.assertEqual(UnitGuard.mg_dl_to_mmol_l(180.18), 10.0)
        self.assertEqual(UnitGuard.mg_dl_to_mmol_l(100), 5.55)

        # mmol/L -> mg/dL
        self.assertEqual(UnitGuard.mmol_l_to_mg_dl(10.0), 180.2)

        # mg/dL -> g/L
        self.assertEqual(UnitGuard.mg_dl_to_g_l(100), 1.0)
        self.assertEqual(UnitGuard.mg_dl_to_g_l(250), 2.5)

    def test_clinical_shield_safety_logic(self):
        # Safe queries
        self.assertTrue(ClinicalShield.check_safety("Comment se passe ma journée ?"))
        self.assertTrue(ClinicalShield.check_safety("Puis-je manger une pomme ?"))

        # Emergency patterns (Strictly forbidden for IA reasoning)
        self.assertFalse(ClinicalShield.check_safety("Je suis dans le coma."))
        self.assertFalse(ClinicalShield.check_safety("J'ai une douleur à la poitrine."))

        # Symptomatic DKA patterns
        self.assertFalse(ClinicalShield.check_safety("J'ai envie de vomir et mon sucre est à 300."))
        self.assertFalse(ClinicalShield.check_safety("Mon haleine sent la pomme."))

        # Forbidden scope
        self.assertFalse(ClinicalShield.check_safety("Où acheter de la drogue ?"))

    def test_triage_vital_thresholds(self):
        # Hypo emergency
        self.assertEqual(ClinicalShield.triage_vital(40), "VITAL_EMERGENCY_HYPO")
        self.assertEqual(ClinicalShield.triage_vital(53), "VITAL_EMERGENCY_HYPO")

        # Hyper emergency
        self.assertEqual(ClinicalShield.triage_vital(401), "VITAL_EMERGENCY_HYPER")

        # Stable
        self.assertEqual(ClinicalShield.triage_vital(120), "STABLE")
        self.assertEqual(ClinicalShield.triage_vital(70), "STABLE")

    def test_language_labels_completeness(self):
        """Verify all supported language codes produce non-empty instructions."""
        for code in ("fr", "ar-MA", "ar"):
            label = get_language_label(code)
            self.assertTrue(label, f"Language label for '{code}' must not be empty")
            self.assertIsInstance(label, str)

    def test_language_label_fallback(self):
        """Unknown language codes fall back to the raw code (no crash)."""
        unknown = "zh-CN"
        result = get_language_label(unknown)
        self.assertEqual(result, unknown)

    def test_darija_label_contains_key_vocabulary(self):
        """ar-MA label must contain Darija markers in Arabic script (not Latin transliteration)."""
        label = LANGUAGE_LABELS["ar-MA"]
        self.assertIn("الدارجة", label)  # "Darija" in Arabic script
        self.assertIn("واش", label)      # wach — in Arabic script
        self.assertIn("مزيان", label)    # mzyan — in Arabic script

    def test_arabic_label_uses_msa(self):
        """ar label must instruct the LLM to use Modern Standard Arabic (MSA)."""
        label = LANGUAGE_LABELS["ar"]
        # MSA instruction is embedded in the Arabic text
        self.assertIn("MSA", label)
