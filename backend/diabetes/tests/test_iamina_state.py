"""
Tests for engine.services.iamina.state — IAminaState computation.
Pure Python logic (no DB, no LLM, no Django models needed).
"""
from django.test import SimpleTestCase

from companion.deep_memory import IAminaDeepMemory
from companion.memory import IAminaMemory
from companion.state import IAminaState, compute_state, state_to_prompt
from core.contracts.domain_context import DomainContext

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _memory(**kwargs) -> IAminaMemory:
    defaults = dict(
        patient_id=1,
        patterns=[],
        last_concern=None,
        current_tone="encouraging",
        emotional_signals=[],
        milestones_celebrated=[],
        cached_stats={},
    )
    defaults.update(kwargs)
    return IAminaMemory(**defaults)


def _deep(**kwargs) -> IAminaDeepMemory:
    defaults = dict(
        patient_id=1,
        significant_events=[],
        food_sensitivities={},
        peak_hours=[],
        relationship_stage="new",
        communication_style="unknown",
        total_interactions=0,
        last_log_date=None,
        consecutive_log_days=0,
        longest_streak=0,
    )
    defaults.update(kwargs)
    return IAminaDeepMemory(**defaults)


def _ctx(**kwargs) -> DomainContext:
    """Build a DomainContext from legacy diabetes kwargs (tir_pct/cv_pct/tir_trend)."""
    return DomainContext(
        kpi_summary={},
        detected_patterns=kwargs.get("pattern_codes", []),
        insights=[],
        pivot_text=kwargs.get("pivot_text", ""),
        language="fr",
        has_sufficient_data=kwargs.get("has_sufficient_data", False),
        tone_signals={
            "primary": kwargs.get("tir_pct"),
            "stability": kwargs.get("cv_pct"),
        },
        trend=kwargs.get("tir_trend", {}),
        primary_label="TIR",
    )


# ─── satisfaction ─────────────────────────────────────────────────────────────

class SatisfactionTest(SimpleTestCase):

    def test_high_tir_gives_high_satisfaction(self):
        state = compute_state(_memory(), _deep(), _ctx(tir_pct=75.0))
        self.assertGreaterEqual(state.satisfaction, 0.5)

    def test_mid_tir_gives_moderate_satisfaction(self):
        state = compute_state(_memory(), _deep(), _ctx(tir_pct=60.0))
        # +0.3 for tir 50-70, no streak, no milestone → 0.3
        self.assertAlmostEqual(state.satisfaction, 0.3)

    def test_low_tir_gives_low_satisfaction(self):
        state = compute_state(_memory(), _deep(), _ctx(tir_pct=35.0))
        # +0.1 for tir < 50
        self.assertAlmostEqual(state.satisfaction, 0.1)

    def test_no_tir_gives_zero_base_satisfaction(self):
        state = compute_state(_memory(), _deep(), _ctx(tir_pct=None))
        self.assertAlmostEqual(state.satisfaction, 0.0)

    def test_streak_7_adds_02(self):
        state = compute_state(_memory(), _deep(consecutive_log_days=7), _ctx(tir_pct=None))
        self.assertAlmostEqual(state.satisfaction, 0.2)

    def test_streak_3_adds_01(self):
        state = compute_state(_memory(), _deep(consecutive_log_days=3), _ctx(tir_pct=None))
        self.assertAlmostEqual(state.satisfaction, 0.1)

    def test_milestone_adds_01(self):
        mem = _memory(milestones_celebrated=["first_10_logs"])
        state = compute_state(mem, _deep(), _ctx(tir_pct=None))
        self.assertAlmostEqual(state.satisfaction, 0.1)

    def test_satisfaction_capped_at_1(self):
        mem = _memory(milestones_celebrated=["first_10_logs"])
        deep = _deep(consecutive_log_days=7)
        # tir >= 70 (+0.5) + streak 7 (+0.2) + milestone (+0.1) = 0.8 ≤ 1.0
        state = compute_state(mem, deep, _ctx(tir_pct=80.0))
        self.assertLessEqual(state.satisfaction, 1.0)
        self.assertAlmostEqual(state.satisfaction, 0.8)

    def test_satisfaction_cannot_exceed_1_extreme(self):
        """Even with maximum bonuses the value stays ≤ 1."""
        mem = _memory(milestones_celebrated=["m1", "m2", "m3"])
        deep = _deep(consecutive_log_days=10)
        state = compute_state(mem, deep, _ctx(tir_pct=90.0))
        self.assertLessEqual(state.satisfaction, 1.0)


# ─── concern_level ────────────────────────────────────────────────────────────

class ConcernLevelTest(SimpleTestCase):

    def test_very_low_tir_gives_high_concern(self):
        state = compute_state(_memory(), _deep(), _ctx(tir_pct=30.0))
        self.assertGreaterEqual(state.concern_level, 0.5)

    def test_moderate_low_tir(self):
        # tir 40–55 → +0.3
        state = compute_state(_memory(), _deep(), _ctx(tir_pct=48.0))
        self.assertAlmostEqual(state.concern_level, 0.3)

    def test_high_cv_adds_concern(self):
        state = compute_state(_memory(), _deep(), _ctx(tir_pct=65.0, cv_pct=40.0))
        # tir 65 → 0 concern from tir, cv > 36 → +0.2
        self.assertAlmostEqual(state.concern_level, 0.2)

    def test_downward_trend_adds_concern(self):
        ctx = _ctx(tir_pct=65.0, tir_trend={"direction": "down"})
        state = compute_state(_memory(), _deep(), ctx)
        self.assertAlmostEqual(state.concern_level, 0.2)

    def test_discouragement_signal_adds_concern(self):
        mem = _memory(emotional_signals=["discouragement"])
        state = compute_state(mem, _deep(), _ctx(tir_pct=65.0))
        self.assertAlmostEqual(state.concern_level, 0.2)

    def test_fear_signal_adds_concern(self):
        mem = _memory(emotional_signals=["fear"])
        state = compute_state(mem, _deep(), _ctx(tir_pct=65.0))
        self.assertAlmostEqual(state.concern_level, 0.2)

    def test_combined_low_tir_high_cv_concern(self):
        state = compute_state(_memory(), _deep(), _ctx(tir_pct=38.0, cv_pct=38.0))
        # tir < 40 (+0.5) + cv > 36 (+0.2) = 0.7
        self.assertAlmostEqual(state.concern_level, 0.7)

    def test_concern_capped_at_1(self):
        mem = _memory(emotional_signals=["discouragement", "fear"])
        ctx = _ctx(tir_pct=30.0, cv_pct=40.0, tir_trend={"direction": "down"})
        state = compute_state(mem, _deep(), ctx)
        self.assertLessEqual(state.concern_level, 1.0)

    def test_no_concern_high_tir(self):
        state = compute_state(_memory(), _deep(), _ctx(tir_pct=72.0))
        self.assertAlmostEqual(state.concern_level, 0.0)

    def test_stale_log_adds_concern(self):
        """consecutive_log_days == 0 and last_log_date > 3 days ago → +0.1"""
        from datetime import date, timedelta
        old_date = (date.today() - timedelta(days=5)).isoformat()
        deep = _deep(consecutive_log_days=0, last_log_date=old_date)
        state = compute_state(_memory(), deep, _ctx(tir_pct=None))
        self.assertAlmostEqual(state.concern_level, 0.1)

    def test_recent_log_no_extra_concern(self):
        """consecutive_log_days == 0 but last_log_date is recent → no +0.1"""
        from datetime import date, timedelta
        recent = (date.today() - timedelta(days=1)).isoformat()
        deep = _deep(consecutive_log_days=0, last_log_date=recent)
        state = compute_state(_memory(), deep, _ctx(tir_pct=None))
        self.assertAlmostEqual(state.concern_level, 0.0)


# ─── engagement ───────────────────────────────────────────────────────────────

class EngagementTest(SimpleTestCase):

    def test_zero_interactions_new_stage(self):
        state = compute_state(_memory(), _deep(total_interactions=0, relationship_stage="new"), _ctx())
        self.assertAlmostEqual(state.engagement, 0.0)

    def test_50_interactions_contributes_06(self):
        deep = _deep(total_interactions=50, relationship_stage="new")
        state = compute_state(_memory(), deep, _ctx())
        self.assertAlmostEqual(state.engagement, 0.6)

    def test_relationship_building_adds_01(self):
        deep = _deep(total_interactions=0, relationship_stage="building")
        state = compute_state(_memory(), deep, _ctx())
        self.assertAlmostEqual(state.engagement, 0.1)

    def test_relationship_trusted_adds_02(self):
        deep = _deep(total_interactions=0, relationship_stage="trusted")
        state = compute_state(_memory(), deep, _ctx())
        self.assertAlmostEqual(state.engagement, 0.2)

    def test_relationship_companion_adds_03(self):
        deep = _deep(total_interactions=0, relationship_stage="companion")
        state = compute_state(_memory(), deep, _ctx())
        self.assertAlmostEqual(state.engagement, 0.3)

    def test_streak_5_adds_01(self):
        deep = _deep(consecutive_log_days=5, relationship_stage="new", total_interactions=0)
        state = compute_state(_memory(), deep, _ctx())
        self.assertAlmostEqual(state.engagement, 0.1)

    def test_engagement_capped_at_1(self):
        deep = _deep(total_interactions=200, relationship_stage="companion", consecutive_log_days=10)
        state = compute_state(_memory(), deep, _ctx())
        self.assertLessEqual(state.engagement, 1.0)


# ─── clinical_mood ────────────────────────────────────────────────────────────

class ClinicalMoodTest(SimpleTestCase):

    def test_alarmed_when_concern_above_06(self):
        # tir < 40 (+0.5) + cv > 36 (+0.2) = 0.7 → alarmed
        state = compute_state(_memory(), _deep(), _ctx(tir_pct=30.0, cv_pct=40.0))
        self.assertEqual(state.clinical_mood, "alarmed")

    def test_concerned_when_concern_between_035_and_06(self):
        # tir 40–55 (+0.3) + cv > 36 (+0.2) = 0.5 → concerned
        state = compute_state(_memory(), _deep(), _ctx(tir_pct=48.0, cv_pct=38.0))
        self.assertEqual(state.clinical_mood, "concerned")

    def test_optimistic_when_high_satisfaction_low_concern(self):
        # tir >= 70 (+0.5) + streak 7 (+0.2) = 0.7 satisfaction, 0 concern → optimistic
        state = compute_state(_memory(), _deep(consecutive_log_days=7), _ctx(tir_pct=75.0))
        self.assertEqual(state.clinical_mood, "optimistic")

    def test_watchful_default(self):
        # No TIR, no streak, no signals → satisfaction=0, concern=0 → watchful
        state = compute_state(_memory(), _deep(), _ctx(tir_pct=None))
        self.assertEqual(state.clinical_mood, "watchful")

    def test_watchful_mid_satisfaction_low_concern(self):
        # tir 50-70 (+0.3) — below 0.6 threshold → watchful
        state = compute_state(_memory(), _deep(), _ctx(tir_pct=60.0))
        self.assertEqual(state.clinical_mood, "watchful")

    def test_all_four_moods_reachable(self):
        moods = set()
        # alarmed
        s = compute_state(_memory(), _deep(), _ctx(tir_pct=30.0, cv_pct=40.0))
        moods.add(s.clinical_mood)
        # concerned
        s = compute_state(_memory(), _deep(), _ctx(tir_pct=48.0, cv_pct=38.0))
        moods.add(s.clinical_mood)
        # optimistic
        s = compute_state(_memory(), _deep(consecutive_log_days=7), _ctx(tir_pct=75.0))
        moods.add(s.clinical_mood)
        # watchful
        s = compute_state(_memory(), _deep(), _ctx(tir_pct=None))
        moods.add(s.clinical_mood)
        self.assertEqual(moods, {"alarmed", "concerned", "optimistic", "watchful"})


# ─── next_intention ───────────────────────────────────────────────────────────

class NextIntentionTest(SimpleTestCase):

    def test_milestone_takes_priority(self):
        mem = _memory(milestones_celebrated=["first_10_logs"])
        state = compute_state(mem, _deep(), _ctx(tir_pct=30.0))
        self.assertIn("first_10_logs", state.next_intention)

    def test_downward_trend_and_high_concern(self):
        ctx = _ctx(tir_pct=30.0, tir_trend={"direction": "down"})
        state = compute_state(_memory(), _deep(), ctx)
        self.assertIn("tendance", state.next_intention)

    def test_long_streak_intention(self):
        deep = _deep(consecutive_log_days=7)
        state = compute_state(_memory(), deep, _ctx(tir_pct=None))
        self.assertIn("régularité", state.next_intention)

    def test_food_sensitivities_do_not_drive_intention(self):
        deep = _deep(food_sensitivities={"couscous": 2.1})
        state = compute_state(_memory(), deep, _ctx(tir_pct=None))
        self.assertEqual(state.next_intention, "écouter et accompagner")

    def test_emotional_signals_intention(self):
        mem = _memory(emotional_signals=["discouragement"])
        state = compute_state(mem, _deep(), _ctx(tir_pct=None))
        self.assertIn("nouvelles", state.next_intention)

    def test_default_intention(self):
        state = compute_state(_memory(), _deep(), _ctx(tir_pct=None))
        self.assertEqual(state.next_intention, "écouter et accompagner")

    def test_next_intention_never_empty(self):
        """next_intention must be non-empty in all edge cases."""
        cases = [
            (_memory(), _deep(), _ctx()),
            (_memory(emotional_signals=["fatigue"]), _deep(), _ctx()),
            (_memory(), _deep(consecutive_log_days=10), _ctx(tir_pct=80.0)),
            (_memory(), _deep(), _ctx(tir_pct=25.0, cv_pct=45.0)),
        ]
        for mem, deep, ctx in cases:
            state = compute_state(mem, deep, ctx)
            self.assertTrue(state.next_intention, f"next_intention should not be empty for {ctx}")


# ─── state_to_prompt ──────────────────────────────────────────────────────────

class StateToPromptTest(SimpleTestCase):

    def _make_state(self, **kwargs) -> IAminaState:
        defaults = dict(
            satisfaction=0.72,
            concern_level=0.18,
            engagement=0.65,
            clinical_mood="optimistic",
            next_intention="souligner la régularité et encourager",
            self_note="Patient en progrès (TIR 68%), streak 5j — rester chaleureux",
        )
        defaults.update(kwargs)
        return IAminaState(**defaults)

    def test_returns_non_empty_string(self):
        state = self._make_state()
        result = state_to_prompt(state)
        self.assertIsInstance(result, str)
        self.assertTrue(result.strip())

    def test_contains_iamina_header(self):
        result = state_to_prompt(self._make_state())
        self.assertIn("[ÉTAT INTERNE IAMINA]", result)

    def test_contains_satisfaction_value(self):
        result = state_to_prompt(self._make_state(satisfaction=0.72))
        self.assertIn("0.72", result)

    def test_contains_concern_value(self):
        result = state_to_prompt(self._make_state(concern_level=0.18))
        self.assertIn("0.18", result)

    def test_contains_engagement_value(self):
        result = state_to_prompt(self._make_state(engagement=0.65))
        self.assertIn("0.65", result)

    def test_contains_clinical_mood(self):
        result = state_to_prompt(self._make_state(clinical_mood="alarmed"))
        self.assertIn("alarmed", result)

    def test_contains_next_intention(self):
        result = state_to_prompt(self._make_state(next_intention="écouter et accompagner"))
        self.assertIn("écouter et accompagner", result)

    def test_contains_self_note(self):
        note = "Patient stable, streak 3j"
        result = state_to_prompt(self._make_state(self_note=note))
        self.assertIn(note, result)

    def test_prompt_from_computed_state(self):
        """End-to-end: compute_state → state_to_prompt returns usable string."""
        mem = _memory(milestones_celebrated=["first_10_logs"])
        deep = _deep(consecutive_log_days=5, relationship_stage="building", total_interactions=15)
        ctx = _ctx(tir_pct=68.0, cv_pct=30.0, tir_trend={"direction": "stable")
        state = compute_state(mem, deep, ctx)
        result = state_to_prompt(state)
        self.assertTrue(result.strip())
        self.assertIn("[ÉTAT INTERNE IAMINA]", result)


# ─── SYSTEM_WITH_STATE ────────────────────────────────────────────────────────

class SystemWithStateTest(SimpleTestCase):

    def test_system_with_state_extends_base(self):
        from companion.prompts import SYSTEM_BASE, SYSTEM_WITH_STATE
        self.assertIn(SYSTEM_BASE, SYSTEM_WITH_STATE)
        self.assertIn("{state}", SYSTEM_WITH_STATE)

    def test_system_with_state_injectable(self):
        from companion.prompts import SYSTEM_WITH_STATE
        state = IAminaState(
            satisfaction=0.5,
            concern_level=0.2,
            engagement=0.4,
            clinical_mood="watchful",
            next_intention="écouter et accompagner",
            self_note="Données insuffisantes pour le moment.",
        )
        filled = SYSTEM_WITH_STATE.format(
            language="français",
            tone="encouraging",
            state=state_to_prompt(state),
        )
        self.assertIn("[ÉTAT INTERNE IAMINA]", filled)
        self.assertIn("watchful", filled)
