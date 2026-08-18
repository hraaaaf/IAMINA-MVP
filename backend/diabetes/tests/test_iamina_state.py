"""P3 tests for IAmina relationship-only internal state.

Clinical semantics must not be recreated in the chassis state layer. DomainContext
is accepted only for API compatibility and changing TIR/CV/trend must not affect
relationship state.
"""
from datetime import date, timedelta

from django.test import SimpleTestCase

from companion.deep_memory import IAminaDeepMemory
from companion.memory import IAminaMemory
from companion.state import IAminaState, compute_state, state_to_prompt
from core.contracts.domain_context import DomainContext


def _memory(**kwargs) -> IAminaMemory:
    defaults = dict(patient_id=1, patterns=[], last_concern=None, current_tone="encouraging", emotional_signals=[], milestones_celebrated=[], cached_stats={})
    defaults.update(kwargs)
    return IAminaMemory(**defaults)


def _deep(**kwargs) -> IAminaDeepMemory:
    defaults = dict(patient_id=1, significant_events=[], food_sensitivities={}, peak_hours=[], relationship_stage="new", communication_style="unknown", total_interactions=0, last_log_date=None, consecutive_log_days=0, longest_streak=0)
    defaults.update(kwargs)
    return IAminaDeepMemory(**defaults)


def _ctx(*, tir=None, cv=None, direction=None) -> DomainContext:
    return DomainContext(kpi_summary={}, detected_patterns=[], insights=[], pivot_text="", language="fr", has_sufficient_data=tir is not None, tone_signals={"primary": tir, "stability": cv}, trend={"direction": direction} if direction else {}, primary_label="TIR")


class RelationshipStateTest(SimpleTestCase):
    def test_clinical_metrics_do_not_change_relationship_state(self):
        mem = _memory()
        deep = _deep(total_interactions=5, relationship_stage="building")
        low = compute_state(mem, deep, _ctx(tir=20, cv=50, direction="down"))
        high = compute_state(mem, deep, _ctx(tir=95, cv=10, direction="up"))
        self.assertEqual(low, high)

    def test_streak_and_milestone_drive_satisfaction(self):
        state = compute_state(_memory(milestones_celebrated=["first_10_logs"]), _deep(consecutive_log_days=7, total_interactions=10), _ctx(tir=20))
        self.assertAlmostEqual(state.satisfaction, 0.8)

    def test_emotional_signal_drives_relationship_concern(self):
        state = compute_state(_memory(emotional_signals=["discouragement"]), _deep(), _ctx(tir=95))
        self.assertAlmostEqual(state.concern_level, 0.4)
        self.assertEqual(state.clinical_mood, "concerned")

    def test_stale_logging_adds_small_relationship_attention(self):
        old = (date.today() - timedelta(days=5)).isoformat()
        state = compute_state(_memory(), _deep(last_log_date=old), _ctx())
        self.assertAlmostEqual(state.concern_level, 0.1)

    def test_engagement_uses_relationship_signals(self):
        state = compute_state(_memory(), _deep(total_interactions=50, relationship_stage="companion", consecutive_log_days=5), _ctx(tir=30))
        self.assertAlmostEqual(state.engagement, 1.0)

    def test_milestone_intention_has_priority(self):
        state = compute_state(_memory(milestones_celebrated=["first_10_logs"]), _deep(consecutive_log_days=9), _ctx(tir=20, direction="down"))
        self.assertIn("first_10_logs", state.next_intention)

    def test_emotional_intention_is_relationship_only(self):
        state = compute_state(_memory(emotional_signals=["fatigue"]), _deep(), _ctx(tir=20, direction="down"))
        self.assertIn("émotionnel", state.next_intention)
        self.assertNotIn("tendance", state.next_intention)

    def test_default_intention(self):
        state = compute_state(_memory(), _deep(), _ctx(tir=20, direction="down"))
        self.assertEqual(state.next_intention, "écouter et accompagner")


class StatePromptTest(SimpleTestCase):
    def test_prompt_is_explicitly_relationship_only(self):
        state = IAminaState(satisfaction=0.5, concern_level=0.2, engagement=0.4, clinical_mood="watchful", next_intention="écouter et accompagner", self_note="Relation: pas de streak actif, style encore inconnu.")
        prompt = state_to_prompt(state)
        self.assertIn("[ÉTAT RELATIONNEL IAMINA]", prompt)
        self.assertIn("Prochaine intention conversationnelle", prompt)
        self.assertNotIn("TIR", prompt)
        self.assertNotIn("CV", prompt)

    def test_computed_prompt_contains_no_clinical_metric_even_if_context_has_one(self):
        state = compute_state(_memory(), _deep(), _ctx(tir=99, cv=1, direction="up"))
        prompt = state_to_prompt(state)
        self.assertNotIn("99", prompt)
        self.assertNotIn("TIR", prompt)
        self.assertNotIn("CV", prompt)
