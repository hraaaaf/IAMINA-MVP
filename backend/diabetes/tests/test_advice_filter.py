"""
Tests for the medical-advice disclaimer throttle.

Covers:
- contains_medical_advice: FR, Darija Arabic, MSA, false positives
- strip_medical_advice: surgical removal, clean join, non-empty result
- apply_advice_throttle: full state-machine (keep+stamp, suppress, no-op)
- Anti-regression: suppression must NOT update last_advice_given_at
- deep_memory: record_advice_given, advice_given_within edge cases
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from django.test import SimpleTestCase

from companion.advice_filter import (
    apply_advice_throttle,
    contains_medical_advice,
    strip_medical_advice,
)

# ── Minimal deep memory stub ──────────────────────────────────────────────────

@dataclass
class _FakeDeep:
    last_advice_given_at: Optional[str] = None
    _saved: bool = False

    def advice_given_within(self, hours: int = 24) -> bool:
        if not self.last_advice_given_at:
            return False
        try:
            last = datetime.fromisoformat(self.last_advice_given_at)
            return (datetime.now(timezone.utc) - last) < timedelta(hours=hours)
        except (ValueError, TypeError):
            return False

    def record_advice_given(self) -> None:
        self.last_advice_given_at = datetime.now(timezone.utc).isoformat()

    def save(self) -> None:
        self._saved = True


# ── contains_medical_advice ───────────────────────────────────────────────────

class ContainsMedicalAdviceTest(SimpleTestCase):

    def test_french_consult(self):
        self.assertTrue(contains_medical_advice("Consulte ton médecin dès que possible."))

    def test_french_parle_en(self):
        self.assertTrue(contains_medical_advice("Parles-en à ton médecin avant de changer."))

    def test_french_equipe_soignante(self):
        self.assertTrue(contains_medical_advice("Contacte ton équipe soignante."))

    def test_french_professionnel_sante(self):
        self.assertTrue(contains_medical_advice("Vois un professionnel de santé rapidement."))

    def test_darija_arabic_chof_tbib(self):
        self.assertTrue(contains_medical_advice("السكر عالي، شوف الطبيب."))

    def test_darija_arabic_twasal(self):
        self.assertTrue(contains_medical_advice("تواصل مع الطبيب ديالك دابا."))

    def test_msa_istasher(self):
        self.assertTrue(contains_medical_advice("يجب أن تستشر طبيبك في هذا الأمر."))

    def test_msa_rajia(self):
        self.assertTrue(contains_medical_advice("راجع طبيبك في أقرب وقت."))

    def test_no_disclaimer_fr(self):
        self.assertFalse(contains_medical_advice("Ton TIR est à 72%, continue comme ça !"))

    def test_no_disclaimer_darija(self):
        self.assertFalse(contains_medical_advice("السكر ديالك في الميزان — زوينة!"))

    def test_no_disclaimer_empty(self):
        self.assertFalse(contains_medical_advice(""))

    def test_case_insensitive(self):
        self.assertTrue(contains_medical_advice("CONSULTE TON MÉDECIN."))

    def test_partial_word_no_false_positive(self):
        # "médecine" should not trigger
        self.assertFalse(contains_medical_advice("La médecine préventive est importante."))


# ── strip_medical_advice ──────────────────────────────────────────────────────

class StripMedicalAdviceTest(SimpleTestCase):

    def test_removes_disclaimer_sentence(self):
        reply = "Ton TIR est stable. Consulte ton médecin pour le suivi. Continue à logger !"
        result = strip_medical_advice(reply)
        self.assertNotIn("médecin", result)
        self.assertIn("TIR", result)
        self.assertIn("logger", result)

    def test_result_is_non_empty(self):
        reply = "Bien noté ! Parles-en à ton médecin."
        result = strip_medical_advice(reply)
        self.assertTrue(result.strip())

    def test_no_disclaimer_unchanged(self):
        reply = "Ton TIR est à 72%."
        self.assertEqual(strip_medical_advice(reply), reply)

    def test_arabic_disclaimer_removed(self):
        reply = "السكر ديالك مزيان. شوف الطبيب إن كان عندك أسئلة."
        result = strip_medical_advice(reply)
        self.assertNotIn("شوف الطبيب", result)
        self.assertIn("السكر", result)

    def test_darija_comma_clause_disclaimer_not_empty(self):
        # ، doesn't split — whole reply is one unit — strip returns "" — throttle returns original
        reply = "الماكلة زينة، شوف الطبيب."
        result = strip_medical_advice(reply)
        # strip returns "" because nothing survives
        self.assertEqual(result, "")

    def test_only_disclaimer_returns_empty(self):
        # strip_medical_advice returns "" when nothing survives — caller handles it
        reply = "Consulte ton médecin."
        result = strip_medical_advice(reply)
        self.assertEqual(result, "")

    def test_result_coherent_after_removal(self):
        reply = "Super semaine ! Consulte ton médecin régulièrement. Tu fais bien."
        result = strip_medical_advice(reply)
        self.assertIn("Super semaine", result)
        self.assertIn("Tu fais bien", result)


# ── apply_advice_throttle ─────────────────────────────────────────────────────

class AdviceThrottleTest(SimpleTestCase):

    def _reply_with(self, text="Consulte ton médecin."):
        return text

    def test_first_disclaimer_kept_and_stamped(self):
        """First disclaimer in a clean window → kept, timestamp set."""
        deep = _FakeDeep()
        reply = "Bien joué ! Consulte ton médecin pour le suivi."
        result = apply_advice_throttle(reply, deep)
        self.assertIn("médecin", result)
        self.assertIsNotNone(deep.last_advice_given_at)

    def test_second_disclaimer_within_24h_suppressed(self):
        """Second disclaimer within 24h → stripped, timestamp NOT updated."""
        deep = _FakeDeep()
        deep.record_advice_given()
        ts_before = deep.last_advice_given_at

        reply = "Bon travail ! Consulte ton médecin."
        result = apply_advice_throttle(reply, deep)
        self.assertNotIn("médecin", result)
        self.assertEqual(deep.last_advice_given_at, ts_before)  # no re-stamp

    def test_disclaimer_after_24h_kept_and_restamped(self):
        """Disclaimer after 24h window → kept, timestamp refreshed."""
        deep = _FakeDeep()
        old_ts = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
        deep.last_advice_given_at = old_ts

        reply = "Continue ! Consulte ton médecin pour le bilan."
        result = apply_advice_throttle(reply, deep)
        self.assertIn("médecin", result)
        self.assertNotEqual(deep.last_advice_given_at, old_ts)  # re-stamped

    def test_no_disclaimer_no_stamp(self):
        """Reply without disclaimer → unchanged, no stamp."""
        deep = _FakeDeep()
        reply = "Ton TIR est à 72%, super !"
        result = apply_advice_throttle(reply, deep)
        self.assertEqual(result, reply)
        self.assertIsNone(deep.last_advice_given_at)

    def test_suppression_does_not_restamp(self):
        """Anti-regression: suppression must never shift the 24h window."""
        deep = _FakeDeep()
        ts_fixed = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        deep.last_advice_given_at = ts_fixed

        apply_advice_throttle("Consulte ton médecin.", deep)
        self.assertEqual(deep.last_advice_given_at, ts_fixed)

    def test_darija_disclaimer_suppressed_within_window(self):
        """Darija Arabic disclaimer also throttled."""
        deep = _FakeDeep()
        deep.record_advice_given()

        reply = "السكر مزيان. شوف الطبيب إن كان عندك شك."
        result = apply_advice_throttle(reply, deep)
        self.assertNotIn("شوف الطبيب", result)

    def test_darija_comma_clause_suppression_returns_non_empty(self):
        """
        Blocage 3 guard: Darija reply joined by ، (no sentence split).
        Suppression would leave empty — throttle must return original, never empty.
        Timestamp must NOT be updated.
        """
        deep = _FakeDeep()
        deep.record_advice_given()
        ts_before = deep.last_advice_given_at

        reply = "الماكلة زينة، شوف الطبيب."
        result = apply_advice_throttle(reply, deep)

        # Non-empty: throttle returned original rather than empty
        self.assertTrue(result.strip(), "throttle must never return empty response")
        # Timestamp unchanged — not re-stamped on failed suppression
        self.assertEqual(deep.last_advice_given_at, ts_before)

    def test_french_first_darija_second_still_throttled(self):
        """First FR disclaimer stamps; second Darija disclaimer within window is suppressed."""
        deep = _FakeDeep()

        first = apply_advice_throttle("Consulte ton médecin.", deep)
        self.assertIn("médecin", first)

        # Reply has content + disclaimer so strip_medical_advice has something to keep
        second = apply_advice_throttle("السكر مزيان. شوف الطبيب دابا.", deep)
        self.assertNotIn("شوف الطبيب", second)
        self.assertIn("السكر", second)


# ── deep_memory: record_advice_given + advice_given_within ───────────────────

class DeepMemoryAdviceTimingTest(SimpleTestCase):

    def test_advice_given_within_none(self):
        from companion.deep_memory import IAminaDeepMemory
        m = IAminaDeepMemory(patient_id=1)
        self.assertFalse(m.advice_given_within(24))

    def test_advice_given_within_just_now(self):
        from companion.deep_memory import IAminaDeepMemory
        m = IAminaDeepMemory(patient_id=1)
        m.record_advice_given()
        self.assertTrue(m.advice_given_within(24))

    def test_advice_given_outside_window(self):
        from companion.deep_memory import IAminaDeepMemory
        m = IAminaDeepMemory(patient_id=1)
        m.last_advice_given_at = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
        self.assertFalse(m.advice_given_within(24))

    def test_advice_given_at_boundary(self):
        from companion.deep_memory import IAminaDeepMemory
        m = IAminaDeepMemory(patient_id=1)
        m.last_advice_given_at = (datetime.now(timezone.utc) - timedelta(hours=24, seconds=1)).isoformat()
        self.assertFalse(m.advice_given_within(24))

    def test_malformed_timestamp_returns_false(self):
        from companion.deep_memory import IAminaDeepMemory
        m = IAminaDeepMemory(patient_id=1)
        m.last_advice_given_at = "not-a-date"
        self.assertFalse(m.advice_given_within(24))
