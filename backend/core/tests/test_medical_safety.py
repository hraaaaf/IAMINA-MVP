from django.test import SimpleTestCase, override_settings

from core.medical_safety import (
    _FORBIDDEN_PATTERNS,
    apply_no_prescription_policy,
    diagnosis_allowed,
    insulin_advice_allowed,
    is_insulin_prescription_request,
    medical_pilot_mode_enabled,
    medical_streaming_enabled,
    violates_no_prescription_policy,
)


class MedicalSafetyPolicyTests(SimpleTestCase):
    def test_blocks_insulin_adjustment_phrase(self):
        blocked = apply_no_prescription_policy("Augmente ta dose d'insuline ce soir.", "fr")
        self.assertIn("Je ne peux pas prescrire", blocked)

    def test_blocks_treatment_stop_phrase(self):
        blocked = apply_no_prescription_policy("Arrete ton traitement pendant 2 jours.", "fr")
        self.assertIn("Je ne peux pas prescrire", blocked)

    def test_blocks_diagnosis_phrase(self):
        blocked = apply_no_prescription_policy("Tu as surement un diabete desequilibre.", "fr")
        self.assertIn("Je ne peux pas prescrire", blocked)

    def test_blocks_no_doctor_phrase(self):
        blocked = apply_no_prescription_policy("Pas besoin de medecin pour ca.", "fr")
        self.assertIn("Je ne peux pas prescrire", blocked)

    def test_safe_text_is_preserved(self):
        original = "Ton sucre semble monter apres certains repas. Note ce qui se repete."
        self.assertEqual(apply_no_prescription_policy(original, "fr"), original)

    def test_violation_detection(self):
        self.assertTrue(violates_no_prescription_policy("Diminue ton insuline."))
        self.assertFalse(violates_no_prescription_policy("Continue a suivre tes mesures."))


class MedicalSafetyFlagTests(SimpleTestCase):
    @override_settings(
        MEDICAL_PILOT_MODE=False,
        LLM_MEDICAL_STREAMING=False,
        ALLOW_INSULIN_ADVICE=False,
        ALLOW_DIAGNOSIS=False,
    )
    def test_safe_defaults_are_false(self):
        self.assertFalse(medical_pilot_mode_enabled())
        self.assertFalse(medical_streaming_enabled())
        self.assertFalse(insulin_advice_allowed())
        self.assertFalse(diagnosis_allowed())


class ForbiddenPatternCoverageTests(SimpleTestCase):
    def test_blocks_bolus(self):
        blocked = apply_no_prescription_policy("Fais un bolus de 4 unités.", "fr")
        self.assertIn("Je ne peux pas prescrire", blocked)

    def test_blocks_insuline_rapide(self):
        blocked = apply_no_prescription_policy("Utilise de l'insuline rapide.", "fr")
        self.assertIn("Je ne peux pas prescrire", blocked)

    def test_blocks_prends_unites(self):
        blocked = apply_no_prescription_policy("Prends 10 unités avant le repas.", "fr")
        self.assertIn("Je ne peux pas prescrire", blocked)

    def test_ar_ma_block_message(self):
        blocked = apply_no_prescription_policy("Augmente ta dose.", "ar-MA")
        self.assertIn("nbadel lik traitement", blocked)

    def test_empty_string_preserved(self):
        result = apply_no_prescription_policy("", "fr")
        self.assertEqual(result, "")

    def test_none_input_returns_none(self):
        result = apply_no_prescription_policy(None)
        self.assertIsNone(result)

    def test_violates_none_returns_false(self):
        self.assertFalse(violates_no_prescription_policy(None))

    def test_forbidden_pattern_count_at_least_10(self):
        self.assertGreaterEqual(len(_FORBIDDEN_PATTERNS), 10)


class InsulinInputBlockerTests(SimpleTestCase):
    """Input-side detection: blocks insulin dose/prescription requests before LLM."""

    def test_detects_combien_unites_insuline(self):
        self.assertTrue(is_insulin_prescription_request(
            "J'ai 250 de glycémie, combien d'unités d'insuline je dois prendre ?"
        ))

    def test_detects_dose_insuline(self):
        self.assertTrue(is_insulin_prescription_request(
            "Quelle dose d'insuline je dois prendre ?"
        ))

    def test_detects_prends_combien_unites(self):
        self.assertTrue(is_insulin_prescription_request(
            "Prends combien d'unités d'insuline ?"
        ))

    def test_detects_bolus_amount_request(self):
        self.assertTrue(is_insulin_prescription_request(
            "Quelle quantité de bolus je dois mettre ?"
        ))

    def test_detects_darija_chhal_nakhod_insuline(self):
        self.assertTrue(is_insulin_prescription_request(
            "Chhal nakhod insulin pour mon repas ?"
        ))

    def test_detects_arabic_insulin_units(self):
        self.assertTrue(is_insulin_prescription_request(
            "كم وحدة أنسولين يجب أن آخذ؟"
        ))

    def test_detects_je_dois_prendre_insuline(self):
        self.assertTrue(is_insulin_prescription_request(
            "Je dois prendre combien d'insuline ce soir ?"
        ))

    def test_detects_augmenter_insuline(self):
        self.assertTrue(is_insulin_prescription_request(
            "Je veux augmenter mon insuline"
        ))

    def test_detects_combien_insuline_simple(self):
        self.assertTrue(is_insulin_prescription_request(
            "Combien d'insuline je prends ?"
        ))

    def test_does_not_block_educational_insulin_question(self):
        self.assertFalse(is_insulin_prescription_request(
            "C'est quoi l'insuline ?"
        ))

    def test_does_not_block_storage_insulin_question(self):
        self.assertFalse(is_insulin_prescription_request(
            "Comment conserver l'insuline ?"
        ))

    def test_does_not_block_purpose_insulin_question(self):
        self.assertFalse(is_insulin_prescription_request(
            "A quoi sert l'insuline ?"
        ))

    def test_does_not_block_explain_insulin(self):
        self.assertFalse(is_insulin_prescription_request(
            "Explique moi l'insuline"
        ))

    def test_none_input_returns_false(self):
        self.assertFalse(is_insulin_prescription_request(None))

    def test_empty_string_returns_false(self):
        self.assertFalse(is_insulin_prescription_request(""))
