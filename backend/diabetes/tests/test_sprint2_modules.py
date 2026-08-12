"""
Sprint 2 module tests: session_cache, IAminaMemory DB fallback,
conversation._trim_history, compute_trend, evidence-qualified pre/post-meal
observation, LLM rate guard, AGP percentile helper, and AuditLog.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone


class IAminaMemoryDBFallbackTest(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()

    def _make_user(self):
        return User.objects.create_user(
            username=f"testmem_{self._testMethodName}", password="x"
        )

    def test_load_returns_default_when_cache_and_db_empty(self):
        from companion.memory import IAminaMemory

        user = self._make_user()
        mem = IAminaMemory.load(user)
        self.assertEqual(mem.patient_id, user.id)
        self.assertEqual(mem.patterns, [])

    def test_save_creates_db_snapshot(self):
        from companion.memory import IAminaMemory
        from companion.memory_truth import SNAPSHOT_SCHEMA, SNAPSHOT_VERSION
        from diabetes.models import IAminaMemorySnapshot

        user = self._make_user()
        mem = IAminaMemory(
            patient_id=user.id,
            patterns=["HIGH_VARIABILITY"],
            current_tone="gentle",
        )
        mem.save()
        snap = IAminaMemorySnapshot.objects.get(patient=user)
        self.assertEqual(snap.data_json["schema"], SNAPSHOT_SCHEMA)
        self.assertEqual(snap.data_json["schema_version"], SNAPSHOT_VERSION)
        self.assertEqual(snap.data_json["kind"], "memory")
        self.assertEqual(snap.data_json["values"]["patterns"], ["HIGH_VARIABILITY"])
        self.assertEqual(snap.data_json["values"]["current_tone"], "gentle")
        self.assertIn("patterns", snap.data_json["provenance"])

    def test_load_recovers_from_db_when_cache_cold(self):
        from companion.memory import IAminaMemory
        from diabetes.models import IAminaMemorySnapshot

        user = self._make_user()
        IAminaMemorySnapshot.objects.create(
            patient=user,
            data_json={
                "patient_id": user.id,
                "patterns": ["DAWN_PHENOMENON"],
                "last_concern": None,
                "current_tone": "challenge",
                "emotional_signals": [],
                "milestones_celebrated": [],
                "cached_stats": {},
            },
        )
        from django.core.cache import cache

        cache.delete(f"iamina:memory:{user.id}")
        mem = IAminaMemory.load(user)
        self.assertEqual(mem.patterns, ["DAWN_PHENOMENON"])
        self.assertEqual(mem.current_tone, "encouraging")

    def test_save_updates_existing_snapshot(self):
        from companion.memory import IAminaMemory
        from companion.memory_truth import SNAPSHOT_SCHEMA
        from diabetes.models import IAminaMemorySnapshot

        user = self._make_user()
        mem = IAminaMemory(patient_id=user.id, patterns=["FIRST"])
        mem.save()
        mem.patterns = ["SECOND"]
        mem.save()
        self.assertEqual(
            IAminaMemorySnapshot.objects.filter(patient=user).count(), 1
        )
        snap = IAminaMemorySnapshot.objects.get(patient=user)
        self.assertEqual(snap.data_json["schema"], SNAPSHOT_SCHEMA)
        self.assertEqual(snap.data_json["values"]["patterns"], ["SECOND"])


class TrimHistoryTest(TestCase):
    def _make_user(self):
        return User.objects.create_user(username="trimuser", password="x")

    def _create_messages(self, user, count: int):
        from diabetes.models import AIChatMessage

        for i in range(count):
            AIChatMessage.objects.create(patient=user, role="user", message=f"msg {i}")
            AIChatMessage.objects.create(
                patient=user, role="assistant", message=f"reply {i}"
            )

    def test_no_preamble_under_20_messages(self):
        from companion.conversation import _trim_history
        from diabetes.models import AIChatMessage

        user = self._make_user()
        self._create_messages(user, 5)
        qs = AIChatMessage.objects.filter(patient=user).order_by("-created_at")[:10]
        result = _trim_history(qs, 5000, patient=user)
        self.assertNotIn("[", result[:5])

    def test_preamble_appears_over_20_messages(self):
        from companion.conversation import _trim_history
        from diabetes.models import AIChatMessage

        user = self._make_user()
        self._create_messages(user, 15)
        qs = AIChatMessage.objects.filter(patient=user).order_by("-created_at")[:10]
        result = _trim_history(qs, 5000, patient=user)
        self.assertIn("messages au total", result)

    def test_char_budget_respected(self):
        from companion.conversation import _trim_history
        from diabetes.models import AIChatMessage

        user = self._make_user()
        self._create_messages(user, 5)
        qs = AIChatMessage.objects.filter(patient=user).order_by("-created_at")[:10]
        result = _trim_history(qs, 20, patient=user)
        self.assertLessEqual(len(result.replace("[", "").replace("]", "")), 200)

    def test_empty_history_returns_fallback(self):
        from companion.conversation import _trim_history
        from diabetes.models import AIChatMessage

        user = self._make_user()
        qs = AIChatMessage.objects.filter(patient=user).order_by("-created_at")[:10]
        result = _trim_history(qs, 5000, patient=user)
        self.assertEqual(result, "Pas d'historique.")


class ComputeTrendTest(TestCase):
    def _make_user(self):
        return User.objects.create_user(username="trenduser", password="x")

    def test_returns_unknown_direction_with_no_data(self):
        from diabetes.services.clinical.sql_analytics import compute_trend

        user = self._make_user()
        result = compute_trend(patient_id=user.id)
        self.assertEqual(result["direction"], "unknown")
        self.assertIsNone(result["current_week_tir"])

    def test_returns_dict_with_required_keys(self):
        from diabetes.services.clinical.sql_analytics import compute_trend

        user = self._make_user()
        result = compute_trend(patient_id=user.id)
        for key in (
            "current_week_tir",
            "prev_week_tir",
            "tir_delta",
            "direction",
        ):
            self.assertIn(key, result)

    def test_with_current_week_data(self):
        from diabetes.models import LogEntry
        from diabetes.services.clinical.sql_analytics import compute_trend

        user = self._make_user()
        now = timezone.now()
        for val in [120, 140, 110, 160, 130]:
            LogEntry.objects.create(
                patient=user,
                blood_sugar=val,
                logged_at=now - timedelta(days=2),
            )
        result = compute_trend(patient_id=user.id)
        self.assertIsNotNone(result["current_week_tir"])
        self.assertIn(result["direction"], ("up", "down", "stable", "unknown"))


class PostmealSpikeDetectorTest(TestCase):
    """Compatibility helper must require explicit measurement context."""

    def _make_entry(
        self,
        blood_sugar,
        meal_type=None,
        glycemic_context="",
        hours_offset=0,
    ):
        e = MagicMock()
        e.blood_sugar = blood_sugar
        e.meal_type = meal_type
        e.glycemic_context = glycemic_context
        e.effective_time = timezone.now() + timedelta(hours=hours_offset)
        return e

    def test_no_entries_returns_none(self):
        from diabetes.services.clinical.engine import detect_postmeal_spike

        self.assertIsNone(detect_postmeal_spike([]))

    def test_single_explicit_pair_not_enough(self):
        from diabetes.services.clinical.engine import detect_postmeal_spike

        entries = [
            self._make_entry(
                100,
                meal_type="lunch",
                glycemic_context="pre_meal",
                hours_offset=0,
            ),
            self._make_entry(
                175,
                meal_type="lunch",
                glycemic_context="post_meal",
                hours_offset=1,
            ),
        ]
        self.assertIsNone(detect_postmeal_spike(entries))

    def test_two_explicit_pairs_trigger_neutral_observation(self):
        from diabetes.services.clinical.engine import detect_postmeal_spike

        base = datetime(2024, 1, 10, 12, 0, 0, tzinfo=UTC)

        def _e(val, context, delta_h, day_offset=0):
            e = MagicMock()
            e.blood_sugar = val
            e.meal_type = "lunch"
            e.glycemic_context = context
            e.effective_time = base + timedelta(days=day_offset, hours=delta_h)
            return e

        entries = [
            _e(100, "pre_meal", 0, day_offset=0),
            _e(175, "post_meal", 1, day_offset=0),
            _e(110, "pre_meal", 0, day_offset=1),
            _e(190, "post_meal", 1, day_offset=1),
        ]
        result = detect_postmeal_spike(entries)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.code, "REPEATED_PRE_POST_MEAL_RISE")
        self.assertEqual(result.priority, 2)
        self.assertIn("ne détermine ni la cause", result.fallback_content)
        self.assertNotIn("insuline", result.fallback_action.lower())

    def test_missing_pre_post_context_fails_closed(self):
        from diabetes.services.clinical.engine import detect_postmeal_spike

        base = datetime(2024, 1, 10, 12, 0, 0, tzinfo=UTC)

        def _e(val, meal, delta_h, day_offset=0):
            e = MagicMock()
            e.blood_sugar = val
            e.meal_type = meal
            e.glycemic_context = ""
            e.effective_time = base + timedelta(days=day_offset, hours=delta_h)
            return e

        entries = [
            _e(100, "lunch", 0, day_offset=0),
            _e(175, None, 1, day_offset=0),
            _e(110, "lunch", 0, day_offset=1),
            _e(190, None, 1, day_offset=1),
        ]
        self.assertIsNone(detect_postmeal_spike(entries))

    def test_no_pattern_when_rise_below_threshold(self):
        from diabetes.services.clinical.engine import detect_postmeal_spike

        base = datetime(2024, 1, 10, 12, 0, 0, tzinfo=UTC)

        def _e(val, context, delta_h, day_offset=0):
            e = MagicMock()
            e.blood_sugar = val
            e.meal_type = "lunch"
            e.glycemic_context = context
            e.effective_time = base + timedelta(days=day_offset, hours=delta_h)
            return e

        entries = [
            _e(120, "pre_meal", 0, day_offset=0),
            _e(150, "post_meal", 1, day_offset=0),
            _e(115, "pre_meal", 0, day_offset=1),
            _e(140, "post_meal", 1, day_offset=1),
        ]
        self.assertIsNone(detect_postmeal_spike(entries))


class RateGuardTest(TestCase):
    def setUp(self):
        from django.core.cache import cache

        from llm.rate_guard import _clear_local_count, _counter_key

        cache.delete(_counter_key())
        _clear_local_count()

    def test_should_use_gemini_when_count_zero(self):
        from llm.rate_guard import should_use_gemini

        self.assertTrue(should_use_gemini())

    def test_should_not_use_gemini_at_cap(self):
        from llm.rate_guard import _mark_cap_reached, should_use_gemini

        _mark_cap_reached()
        self.assertFalse(should_use_gemini())

    def test_record_increments_counter(self):
        from llm.rate_guard import _get_count, record_gemini_call

        record_gemini_call()
        record_gemini_call()
        self.assertEqual(_get_count(), 2)

    def test_guarded_provider_returns_quota_response_at_cap(self):
        from llm.base import LLMResponse
        from llm.rate_guard import GuardedGeminiProvider, _mark_cap_reached

        _mark_cap_reached()
        inner = MagicMock()
        inner.complete.return_value = LLMResponse(content="ok", provider="gemini")
        guarded = GuardedGeminiProvider(inner)
        result = guarded.complete("sys", "user")
        inner.complete.assert_not_called()
        self.assertIsInstance(result, LLMResponse)
        self.assertIn("quota", result.provider.lower())

    def test_guarded_provider_calls_inner_when_quota_ok(self):
        from llm.base import LLMResponse
        from llm.rate_guard import GuardedGeminiProvider, _get_count

        inner = MagicMock()
        inner.complete.return_value = LLMResponse(content="reply", provider="gemini")
        guarded = GuardedGeminiProvider(inner)
        result = guarded.complete("sys", "user")
        self.assertEqual(result.content, "reply")
        inner.complete.assert_called_once()
        self.assertEqual(_get_count(), 1)


class AGPPercentileHelperTest(TestCase):
    def test_p50_of_sorted_list(self):
        from diabetes.services.clinical.sql_analytics import _percentile

        self.assertEqual(_percentile([1.0, 2.0, 3.0, 4.0, 5.0], 0.5), 3.0)

    def test_p0_returns_min(self):
        from diabetes.services.clinical.sql_analytics import _percentile

        self.assertEqual(_percentile([10.0, 20.0, 30.0], 0.0), 10.0)

    def test_p100_returns_max(self):
        from diabetes.services.clinical.sql_analytics import _percentile

        self.assertEqual(_percentile([10.0, 20.0, 30.0], 1.0), 30.0)

    def test_empty_list_returns_none(self):
        from diabetes.services.clinical.sql_analytics import _percentile

        self.assertIsNone(_percentile([], 0.5))

    def test_single_element(self):
        from diabetes.services.clinical.sql_analytics import _percentile

        self.assertEqual(_percentile([42.0], 0.25), 42.0)


class AuditLogTest(TestCase):
    def _make_user(self):
        return User.objects.create_user(username="audituser", password="x")

    def test_record_creates_row(self):
        from diabetes.models import AuditLog

        user = self._make_user()
        AuditLog.record(user, "consent_given")
        self.assertEqual(
            AuditLog.objects.filter(patient=user, action="consent_given").count(),
            1,
        )

    def test_record_with_request_hashes_ip(self):
        from diabetes.models import AuditLog

        user = self._make_user()
        request = MagicMock()
        request.META = {"REMOTE_ADDR": "127.0.0.1"}
        AuditLog.record(user, "login", request)
        log = AuditLog.objects.get(patient=user, action="login")
        self.assertEqual(len(log.ip_hash), 64)

    def test_row_survives_user_deletion(self):
        from diabetes.models import AuditLog

        user = self._make_user()
        AuditLog.record(user, "account_deleted")
        user.delete()
        log = AuditLog.objects.get(action="account_deleted", patient__isnull=True)
        self.assertIsNone(log.patient)

    def test_no_delete_permission_on_model(self):
        from diabetes.models import AuditLog

        perms = [p[0] for p in AuditLog._meta.default_permissions]
        self.assertNotIn("delete", perms)
