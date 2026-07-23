"""
Tests for core.observability.retention_sql — RetentionMetrics + compute_retention_metrics().

Test cases per plan RFC-001:
  T1 — empty cohort → cohort_size=0, all rates None, all cohort_ready False
  T2 — D1 retained → retention_d1=1.0, cohort_ready_d1=True
  T3 — D7 not retained → retention_d7=0.0
  T4 — D90 null for young cohort → retention_d90 is None, cohort_ready_d90=False
  T5 — funnel counts → correct per-event-type counts; missing types default to 0
"""
from datetime import datetime, timedelta
from datetime import timezone as tz

from django.test import TestCase
from django.utils import timezone

from core.observability import RetentionMetrics, compute_retention_metrics
from core.observability.events import (
    EVT_CHAT_MESSAGE,
    EVT_LOG_CREATED,
    EVT_SESSION_START,
    ObservabilityEvent,
)

# ──────────────────────────────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────────────────────────────

def _evt(event_type: str, patient_id: int, days_ago: float = 0) -> ObservabilityEvent:
    """Create an ObservabilityEvent with timestamp offset by days_ago from now."""
    timezone.now() - timedelta(days=days_ago)
    return ObservabilityEvent.objects.create(
        event_type=event_type,
        patient_id=patient_id,
        props={},
        # Override auto_now_add by updating directly after creation
    )


def _evt_at(event_type: str, patient_id: int, ts: datetime) -> ObservabilityEvent:
    """Create an ObservabilityEvent with an explicit timestamp."""
    obj = ObservabilityEvent.objects.create(
        event_type=event_type,
        patient_id=patient_id,
        props={},
    )
    # auto_now_add=True bypasses normal assignment; use queryset update instead
    ObservabilityEvent.objects.filter(pk=obj.pk).update(timestamp=ts)
    return ObservabilityEvent.objects.get(pk=obj.pk)


# ──────────────────────────────────────────────────────────────────────────────
# T1 — empty cohort
# ──────────────────────────────────────────────────────────────────────────────

class T1EmptyCohortTest(TestCase):
    """No events at all → zeroed-out metrics."""

    def test_empty_cohort(self):
        metrics = compute_retention_metrics()

        self.assertIsInstance(metrics, RetentionMetrics)
        self.assertEqual(metrics.cohort_size, 0)

        self.assertIsNone(metrics.retention_d1)
        self.assertIsNone(metrics.retention_d7)
        self.assertIsNone(metrics.retention_d30)
        self.assertIsNone(metrics.retention_d90)

        self.assertFalse(metrics.cohort_ready_d1)
        self.assertFalse(metrics.cohort_ready_d7)
        self.assertFalse(metrics.cohort_ready_d30)
        self.assertFalse(metrics.cohort_ready_d90)

        # funnel defaults to 0
        self.assertEqual(metrics.funnel_session_start, 0)
        self.assertEqual(metrics.funnel_log_created, 0)
        self.assertEqual(metrics.funnel_chat_message, 0)
        self.assertEqual(metrics.funnel_summary_viewed, 0)

        self.assertIsNone(metrics.chat_per_active_patient)
        self.assertIsInstance(metrics.computed_at, datetime)


# ──────────────────────────────────────────────────────────────────────────────
# T2 — D1 retained
# ──────────────────────────────────────────────────────────────────────────────

class T2D1RetainedTest(TestCase):
    """Patient acquired 3 days ago and has an event at T0+1day+1min → D1 retained."""

    def setUp(self):
        now = timezone.now()
        # Patient 1: acquired 3 days ago
        acquired_at = now - timedelta(days=3)
        _evt_at(EVT_LOG_CREATED, patient_id=1, ts=acquired_at)
        # Return event: 1 day + 5 minutes after acquisition
        return_at = acquired_at + timedelta(days=1, minutes=5)
        _evt_at(EVT_CHAT_MESSAGE, patient_id=1, ts=return_at)

    def test_d1_retained(self):
        metrics = compute_retention_metrics()

        self.assertEqual(metrics.cohort_size, 1)
        self.assertIsNotNone(metrics.retention_d1)
        self.assertAlmostEqual(metrics.retention_d1, 1.0, places=2)
        self.assertTrue(metrics.cohort_ready_d1)


# ──────────────────────────────────────────────────────────────────────────────
# T3 — D7 not retained
# ──────────────────────────────────────────────────────────────────────────────

class T3D7NotRetainedTest(TestCase):
    """Patient acquired 10 days ago; last event is at T0+2days (< 7 days) → D7 not retained."""

    def setUp(self):
        now = timezone.now()
        acquired_at = now - timedelta(days=10)
        _evt_at(EVT_LOG_CREATED, patient_id=2, ts=acquired_at)
        # Only event within 2 days of acquisition — NOT within D7 window
        early_return = acquired_at + timedelta(days=2)
        _evt_at(EVT_CHAT_MESSAGE, patient_id=2, ts=early_return)

    def test_d7_not_retained(self):
        metrics = compute_retention_metrics()

        self.assertEqual(metrics.cohort_size, 1)
        self.assertIsNotNone(metrics.retention_d7)
        self.assertAlmostEqual(metrics.retention_d7, 0.0, places=2)
        self.assertTrue(metrics.cohort_ready_d7)

        # D1 should be retained (returned at day 2 > day 1)
        self.assertAlmostEqual(metrics.retention_d1, 1.0, places=2)


# ──────────────────────────────────────────────────────────────────────────────
# T4 — D90 null for young cohort
# ──────────────────────────────────────────────────────────────────────────────

class T4D90NullYoungCohortTest(TestCase):
    """Patient acquired 10 days ago → not yet eligible for D90 → retention_d90 is None."""

    def setUp(self):
        now = timezone.now()
        acquired_at = now - timedelta(days=10)
        _evt_at(EVT_LOG_CREATED, patient_id=3, ts=acquired_at)

    def test_d90_null_young_cohort(self):
        metrics = compute_retention_metrics()

        self.assertEqual(metrics.cohort_size, 1)
        self.assertIsNone(metrics.retention_d90)
        self.assertFalse(metrics.cohort_ready_d90)

        # D30 should also be null (only 10 days old)
        self.assertIsNone(metrics.retention_d30)
        self.assertFalse(metrics.cohort_ready_d30)

        # D1 and D7 readiness — cohort exists so should be True
        self.assertTrue(metrics.cohort_ready_d1)
        self.assertTrue(metrics.cohort_ready_d7)


# ──────────────────────────────────────────────────────────────────────────────
# T5 — funnel counts
# ──────────────────────────────────────────────────────────────────────────────

class T5FunnelCountsTest(TestCase):
    """3 SESSION_START, 2 LOG_CREATED, 1 CHAT_MESSAGE → correct funnel; SUMMARY_VIEWED=0."""

    def setUp(self):
        now = timezone.now()
        base = now - timedelta(days=5)
        # 3 distinct patients: session_start
        for pid in [10, 11, 12]:
            _evt_at(EVT_SESSION_START, patient_id=pid, ts=base)
        # 2 patients: log_created (patients 10 and 11 are also acquired)
        for pid in [10, 11]:
            _evt_at(EVT_LOG_CREATED, patient_id=pid, ts=base + timedelta(minutes=5))
        # 1 patient: chat_message (patient 10)
        _evt_at(EVT_CHAT_MESSAGE, patient_id=10, ts=base + timedelta(hours=1))
        # No summary_viewed events

    def test_funnel_counts(self):
        metrics = compute_retention_metrics()

        self.assertEqual(metrics.funnel_session_start, 3)
        self.assertEqual(metrics.funnel_log_created, 2)
        self.assertEqual(metrics.funnel_chat_message, 1)
        self.assertEqual(metrics.funnel_summary_viewed, 0)

        # cohort_size is based on log_created events (acquisition anchor)
        self.assertEqual(metrics.cohort_size, 2)

    def test_chat_per_active_patient(self):
        """With 1 chat_message event and cohort_size=2: ratio = 1/2 = 0.5."""
        metrics = compute_retention_metrics()

        self.assertIsNotNone(metrics.chat_per_active_patient)
        self.assertAlmostEqual(metrics.chat_per_active_patient, 0.5, places=2)


# ──────────────────────────────────────────────────────────────────────────────
# T6 — dataclass is immutable (frozen)
# ──────────────────────────────────────────────────────────────────────────────

class T6DataclassImmutableTest(TestCase):
    """RetentionMetrics is a frozen dataclass — mutations must raise FrozenInstanceError."""

    def test_frozen_dataclass(self):
        from dataclasses import FrozenInstanceError

        metrics = compute_retention_metrics()  # empty DB → safe to call

        with self.assertRaises(FrozenInstanceError):
            metrics.cohort_size = 99  # type: ignore[misc]
