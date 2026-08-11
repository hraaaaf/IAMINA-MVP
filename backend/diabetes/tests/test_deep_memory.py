from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase

from companion.deep_memory import IAminaDeepMemory


def _make_patient(pk=42):
    user = MagicMock(spec=User)
    user.id = pk
    return user


class LoadSaveTest(TestCase):

    def test_load_returns_default_when_no_data(self):
        with patch("django.core.cache.cache.get", return_value=None), \
             patch("diabetes.models.IAminaDeepMemorySnapshot.objects") as mock_qs:
            mock_qs.filter.return_value.first.return_value = None
            mem = IAminaDeepMemory.load(_make_patient(1))
        self.assertEqual(mem.patient_id, 1)
        self.assertEqual(mem.relationship_stage, "new")
        self.assertEqual(mem.total_interactions, 0)

    def test_load_from_cache(self):
        import json
        data = {
            "patient_id": 7,
            "significant_events": [],
            "food_sensitivities": {"pizza": 1.8},
            "peak_hours": [14, 18],
            "relationship_stage": "building",
            "communication_style": "data_driven",
            "total_interactions": 12,
            "last_log_date": None,
            "consecutive_log_days": 3,
            "longest_streak": 5,
        }
        with patch("django.core.cache.cache.get", return_value=json.dumps(data)):
            mem = IAminaDeepMemory.load(_make_patient(7))
        self.assertEqual(mem.patient_id, 7)
        self.assertEqual(mem.food_sensitivities, {})
        self.assertEqual(mem.quarantined_heuristics["food_sensitivities"]["pizza"], 1.8)
        self.assertEqual(mem.relationship_stage, "building")

    def test_load_from_db_when_cache_miss(self):
        import json
        data = {
            "patient_id": 8,
            "significant_events": [],
            "food_sensitivities": {},
            "peak_hours": [],
            "relationship_stage": "trusted",
            "communication_style": "unknown",
            "total_interactions": 30,
            "last_log_date": None,
            "consecutive_log_days": 0,
            "longest_streak": 10,
        }
        snap = MagicMock()
        snap.data_json = data
        with patch("django.core.cache.cache.get", return_value=None), \
             patch("django.core.cache.cache.set"), \
             patch("diabetes.models.IAminaDeepMemorySnapshot.objects") as mock_qs:
            mock_qs.filter.return_value.first.return_value = snap
            mem = IAminaDeepMemory.load(_make_patient(8))
        self.assertEqual(mem.relationship_stage, "trusted")
        self.assertEqual(mem.total_interactions, 30)

    def test_save_writes_to_cache_and_db(self):
        mem = IAminaDeepMemory(patient_id=5)
        with patch("django.core.cache.cache.set") as mock_cache, \
             patch("diabetes.models.IAminaDeepMemorySnapshot.objects") as mock_qs:
            mock_qs.update_or_create.return_value = (MagicMock(), True)
            mem.save()
        mock_cache.assert_called_once()
        mock_qs.update_or_create.assert_called_once()

    def test_save_graceful_on_db_error(self):
        mem = IAminaDeepMemory(patient_id=9)
        with patch("django.core.cache.cache.set"), \
             patch("diabetes.models.IAminaDeepMemorySnapshot.objects") as mock_qs:
            mock_qs.update_or_create.side_effect = Exception("DB down")
            # Should not raise
            mem.save()


class RecordEventTest(TestCase):

    def test_event_appended(self):
        mem = IAminaDeepMemory(patient_id=1)
        mem.record_event("hypo", "Glycémie à 0.55", glucose=55.0)
        self.assertEqual(len(mem.significant_events), 1)
        ev = mem.significant_events[0]
        self.assertEqual(ev["type"], "hypo")
        self.assertEqual(ev["glucose"], 55.0)
        self.assertIn("timestamp", ev)

    def test_event_without_glucose(self):
        mem = IAminaDeepMemory(patient_id=1)
        mem.record_event("milestone", "10 jours de suite")
        ev = mem.significant_events[0]
        self.assertNotIn("glucose", ev)

    def test_events_truncated_at_20(self):
        mem = IAminaDeepMemory(patient_id=1)
        for i in range(25):
            mem.record_event("test", f"event {i}")
        self.assertEqual(len(mem.significant_events), 20)
        # Must keep the most recent ones
        self.assertEqual(mem.significant_events[-1]["description"], "event 24")
        self.assertEqual(mem.significant_events[0]["description"], "event 5")


class LearnFoodSensitivityQuarantineTest(TestCase):

    def test_new_food_is_quarantined_not_activated(self):
        mem = IAminaDeepMemory(patient_id=1)
        mem.learn_food_sensitivity("couscous", 2.1)
        self.assertEqual(mem.food_sensitivities, {})
        self.assertAlmostEqual(
            mem.quarantined_heuristics["food_sensitivities"]["couscous"],
            2.1,
            places=3,
        )

    def test_existing_quarantined_food_ema_update(self):
        mem = IAminaDeepMemory(
            patient_id=1,
            quarantined_heuristics={"food_sensitivities": {"pizza": 2.0}},
        )
        mem.learn_food_sensitivity("pizza", 3.0)
        # alpha=0.3: 0.3*3.0 + 0.7*2.0 = 0.9 + 1.4 = 2.3
        self.assertAlmostEqual(
            mem.quarantined_heuristics["food_sensitivities"]["pizza"],
            2.3,
            places=3,
        )
        self.assertEqual(mem.food_sensitivities, {})

    def test_food_name_normalized_lowercase_in_quarantine(self):
        mem = IAminaDeepMemory(patient_id=1)
        mem.learn_food_sensitivity("Couscous", 1.5)
        self.assertIn("couscous", mem.quarantined_heuristics["food_sensitivities"])
        self.assertEqual(mem.food_sensitivities, {})

    def test_multiple_quarantined_updates_converge(self):
        mem = IAminaDeepMemory(patient_id=1)
        mem.learn_food_sensitivity("pain", 1.0)
        for _ in range(20):
            mem.learn_food_sensitivity("pain", 3.0)
        # Backward-compatible EMA may be retained in quarantine, never active state.
        self.assertGreater(mem.quarantined_heuristics["food_sensitivities"]["pain"], 2.5)
        self.assertEqual(mem.food_sensitivities, {})


class UpdateStreakTest(TestCase):

    def test_first_log_starts_streak(self):
        mem = IAminaDeepMemory(patient_id=1)
        mem.update_streak(today_has_log=True)
        self.assertEqual(mem.consecutive_log_days, 1)
        self.assertEqual(mem.last_log_date, date.today().isoformat())

    def test_no_log_resets_streak(self):
        mem = IAminaDeepMemory(patient_id=1)
        mem.consecutive_log_days = 5
        mem.update_streak(today_has_log=False)
        self.assertEqual(mem.consecutive_log_days, 0)

    def test_consecutive_days_increments(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        mem = IAminaDeepMemory(patient_id=1, last_log_date=yesterday, consecutive_log_days=3)
        mem.update_streak(today_has_log=True)
        self.assertEqual(mem.consecutive_log_days, 4)

    def test_gap_resets_to_one(self):
        two_days_ago = (date.today() - timedelta(days=2)).isoformat()
        mem = IAminaDeepMemory(patient_id=1, last_log_date=two_days_ago, consecutive_log_days=5)
        mem.update_streak(today_has_log=True)
        self.assertEqual(mem.consecutive_log_days, 1)

    def test_duplicate_call_same_day_idempotent(self):
        today = date.today().isoformat()
        mem = IAminaDeepMemory(patient_id=1, last_log_date=today, consecutive_log_days=3)
        mem.update_streak(today_has_log=True)
        self.assertEqual(mem.consecutive_log_days, 3)

    def test_longest_streak_updated(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        mem = IAminaDeepMemory(patient_id=1, last_log_date=yesterday, consecutive_log_days=7, longest_streak=7)
        mem.update_streak(today_has_log=True)
        self.assertEqual(mem.longest_streak, 8)

    def test_longest_streak_not_reduced(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        mem = IAminaDeepMemory(patient_id=1, last_log_date=yesterday, consecutive_log_days=2, longest_streak=10)
        mem.update_streak(today_has_log=True)
        self.assertEqual(mem.longest_streak, 10)


class EvolveRelationshipTest(TestCase):

    def test_new_to_building_at_threshold(self):
        mem = IAminaDeepMemory(patient_id=1, relationship_stage="new", total_interactions=5)
        mem.evolve_relationship()
        self.assertEqual(mem.relationship_stage, "building")

    def test_no_progression_below_threshold(self):
        mem = IAminaDeepMemory(patient_id=1, relationship_stage="new", total_interactions=3)
        mem.evolve_relationship()
        self.assertEqual(mem.relationship_stage, "new")

    def test_building_to_trusted(self):
        mem = IAminaDeepMemory(patient_id=1, relationship_stage="building", total_interactions=20)
        mem.evolve_relationship()
        self.assertEqual(mem.relationship_stage, "trusted")

    def test_trusted_to_companion(self):
        mem = IAminaDeepMemory(patient_id=1, relationship_stage="trusted", total_interactions=50)
        mem.evolve_relationship()
        self.assertEqual(mem.relationship_stage, "companion")

    def test_companion_stays_companion(self):
        mem = IAminaDeepMemory(patient_id=1, relationship_stage="companion", total_interactions=200)
        mem.evolve_relationship()
        self.assertEqual(mem.relationship_stage, "companion")

    def test_emotional_signals_boost_progression(self):
        # 4 interactions + 1 signal = 5, should trigger new→building
        mem = IAminaDeepMemory(patient_id=1, relationship_stage="new", total_interactions=4)
        mem.evolve_relationship(emotional_signals=["discouragement"])
        self.assertEqual(mem.relationship_stage, "building")

    def test_no_emotional_signals_no_boost(self):
        mem = IAminaDeepMemory(patient_id=1, relationship_stage="new", total_interactions=4)
        mem.evolve_relationship()
        self.assertEqual(mem.relationship_stage, "new")
