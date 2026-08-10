"""Regressions for the auditable retention evidence contract."""
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

from django.test import TestCase
from django.utils import timezone

from core.observability import RetentionMetrics, compute_retention_metrics
from core.observability.events import (
    EVT_CHAT_MESSAGE,
    EVT_LOG_CREATED,
    EVT_SESSION_START,
    ObservabilityEvent,
)
from core.observability.retention_sql import (
    COHORT_SCOPE_EXPLICIT,
    COHORT_SCOPE_PRODUCT,
    RETENTION_CONTRACT_VERSION,
    RETENTION_SEMANTICS,
)


def _evt_at(event_type: str, patient_id: int, ts: datetime) -> ObservabilityEvent:
    obj = ObservabilityEvent.objects.create(
        event_type=event_type,
        patient_id=patient_id,
        props={},
    )
    ObservabilityEvent.objects.filter(pk=obj.pk).update(timestamp=ts)
    return ObservabilityEvent.objects.get(pk=obj.pk)


class EmptyCohortTest(TestCase):
    def test_empty_cohort(self):
        metrics = compute_retention_metrics()

        self.assertIsInstance(metrics, RetentionMetrics)
        self.assertEqual(metrics.cohort_size, 0)
        self.assertEqual(
            (metrics.eligible_d1, metrics.eligible_d7, metrics.eligible_d30, metrics.eligible_d90),
            (0, 0, 0, 0),
        )
        self.assertEqual(
            (metrics.retention_d1, metrics.retention_d7, metrics.retention_d30, metrics.retention_d90),
            (None, None, None, None),
        )
        self.assertFalse(metrics.cohort_ready_d1)
        self.assertFalse(metrics.cohort_ready_d7)
        self.assertFalse(metrics.cohort_ready_d30)
        self.assertFalse(metrics.cohort_ready_d90)
        self.assertEqual(metrics.funnel_session_start, 0)
        self.assertEqual(metrics.funnel_log_created, 0)
        self.assertEqual(metrics.funnel_chat_message, 0)
        self.assertEqual(metrics.funnel_summary_viewed, 0)
        self.assertIsNone(metrics.chat_per_active_patient)
        self.assertEqual(metrics.retention_contract_version, RETENTION_CONTRACT_VERSION)
        self.assertEqual(metrics.retention_semantics, RETENTION_SEMANTICS)
        self.assertEqual(metrics.cohort_scope, COHORT_SCOPE_PRODUCT)
        self.assertIsNone(metrics.roster_size)
        self.assertIsInstance(metrics.as_of, datetime)
        self.assertIsInstance(metrics.computed_at, datetime)


class RetentionSemanticsTest(TestCase):
    def test_d1_retained(self):
        as_of = datetime(2026, 8, 10, 12, tzinfo=UTC)
        acquired_at = as_of - timedelta(days=3)
        _evt_at(EVT_LOG_CREATED, 1, acquired_at)
        _evt_at(EVT_CHAT_MESSAGE, 1, acquired_at + timedelta(days=1, minutes=5))

        metrics = compute_retention_metrics(as_of=as_of)

        self.assertEqual(metrics.cohort_size, 1)
        self.assertEqual(metrics.eligible_d1, 1)
        self.assertEqual(metrics.retention_d1, 1.0)
        self.assertTrue(metrics.cohort_ready_d1)
        self.assertEqual(metrics.as_of, as_of)

    def test_return_before_d7_does_not_retain_at_d7(self):
        as_of = datetime(2026, 8, 10, 12, tzinfo=UTC)
        acquired_at = as_of - timedelta(days=10)
        _evt_at(EVT_LOG_CREATED, 2, acquired_at)
        _evt_at(EVT_CHAT_MESSAGE, 2, acquired_at + timedelta(days=2))

        metrics = compute_retention_metrics(as_of=as_of)

        self.assertEqual(metrics.eligible_d1, 1)
        self.assertEqual(metrics.eligible_d7, 1)
        self.assertEqual(metrics.retention_d1, 1.0)
        self.assertEqual(metrics.retention_d7, 0.0)

    def test_return_after_d7_counts_as_rolling_retention(self):
        as_of = datetime(2026, 8, 10, 12, tzinfo=UTC)
        acquired_at = as_of - timedelta(days=20)
        _evt_at(EVT_LOG_CREATED, 3, acquired_at)
        _evt_at(EVT_CHAT_MESSAGE, 3, acquired_at + timedelta(days=12))

        metrics = compute_retention_metrics(as_of=as_of)

        self.assertEqual(metrics.eligible_d7, 1)
        self.assertEqual(metrics.retention_d7, 1.0)
        self.assertEqual(metrics.retention_semantics, RETENTION_SEMANTICS)


class HorizonMaturityTest(TestCase):
    def test_young_patient_is_not_a_false_d1_or_d7_failure(self):
        as_of = datetime(2026, 8, 10, 12, tzinfo=UTC)
        _evt_at(EVT_LOG_CREATED, 4, as_of - timedelta(hours=12))

        metrics = compute_retention_metrics(as_of=as_of)

        self.assertEqual(metrics.cohort_size, 1)
        self.assertEqual(metrics.eligible_d1, 0)
        self.assertEqual(metrics.eligible_d7, 0)
        self.assertIsNone(metrics.retention_d1)
        self.assertIsNone(metrics.retention_d7)
        self.assertFalse(metrics.cohort_ready_d1)
        self.assertFalse(metrics.cohort_ready_d7)

    def test_only_mature_patients_enter_each_denominator(self):
        as_of = datetime(2026, 8, 10, 12, tzinfo=UTC)
        mature = as_of - timedelta(days=10)
        young = as_of - timedelta(days=2)
        _evt_at(EVT_LOG_CREATED, 5, mature)
        _evt_at(EVT_LOG_CREATED, 6, young)
        _evt_at(EVT_CHAT_MESSAGE, 5, mature + timedelta(days=8))

        metrics = compute_retention_metrics(as_of=as_of)

        self.assertEqual(metrics.cohort_size, 2)
        self.assertEqual(metrics.eligible_d1, 2)
        self.assertEqual(metrics.eligible_d7, 1)
        self.assertEqual(metrics.eligible_d30, 0)
        self.assertEqual(metrics.eligible_d90, 0)
        self.assertEqual(metrics.retention_d7, 1.0)
        self.assertIsNone(metrics.retention_d30)
        self.assertIsNone(metrics.retention_d90)


class SnapshotCutoffTest(TestCase):
    def test_future_events_cannot_change_historical_snapshot(self):
        as_of = datetime(2026, 8, 10, 12, tzinfo=UTC)
        acquired_at = as_of - timedelta(days=10)
        _evt_at(EVT_LOG_CREATED, 7, acquired_at)
        _evt_at(EVT_CHAT_MESSAGE, 7, as_of + timedelta(days=1))
        _evt_at(EVT_SESSION_START, 8, as_of + timedelta(minutes=1))

        metrics = compute_retention_metrics(as_of=as_of)

        self.assertEqual(metrics.eligible_d7, 1)
        self.assertEqual(metrics.retention_d7, 0.0)
        self.assertEqual(metrics.funnel_chat_message, 0)
        self.assertEqual(metrics.funnel_session_start, 0)
        self.assertIsNone(metrics.chat_per_active_patient)

    def test_future_acquisition_is_not_in_snapshot_cohort(self):
        as_of = datetime(2026, 8, 10, 12, tzinfo=UTC)
        _evt_at(EVT_LOG_CREATED, 9, as_of + timedelta(seconds=1))

        metrics = compute_retention_metrics(as_of=as_of)

        self.assertEqual(metrics.cohort_size, 0)
        self.assertEqual(metrics.funnel_log_created, 0)

    def test_naive_as_of_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            compute_retention_metrics(as_of=datetime(2026, 8, 10, 12))


class ExplicitRosterScopeTest(TestCase):
    def setUp(self):
        self.as_of = datetime(2026, 8, 10, 12, tzinfo=UTC)
        acquired_at = self.as_of - timedelta(days=10)
        for patient_id in (21, 22):
            _evt_at(EVT_LOG_CREATED, patient_id, acquired_at)
            _evt_at(EVT_SESSION_START, patient_id, acquired_at + timedelta(hours=1))
            _evt_at(EVT_CHAT_MESSAGE, patient_id, acquired_at + timedelta(days=8))

    def test_explicit_roster_excludes_unrelated_patient_everywhere(self):
        metrics = compute_retention_metrics(as_of=self.as_of, patient_ids=[21])

        self.assertEqual(metrics.cohort_scope, COHORT_SCOPE_EXPLICIT)
        self.assertEqual(metrics.roster_size, 1)
        self.assertEqual(metrics.cohort_size, 1)
        self.assertEqual(metrics.eligible_d7, 1)
        self.assertEqual(metrics.retention_d7, 1.0)
        self.assertEqual(metrics.funnel_log_created, 1)
        self.assertEqual(metrics.funnel_session_start, 1)
        self.assertEqual(metrics.funnel_chat_message, 1)
        self.assertEqual(metrics.chat_per_active_patient, 1.0)

    def test_duplicate_roster_ids_are_normalized(self):
        metrics = compute_retention_metrics(
            as_of=self.as_of,
            patient_ids=[21, 21],
        )

        self.assertEqual(metrics.roster_size, 1)
        self.assertEqual(metrics.cohort_size, 1)

    def test_empty_explicit_roster_fails_closed_to_empty_evidence(self):
        metrics = compute_retention_metrics(as_of=self.as_of, patient_ids=[])

        self.assertEqual(metrics.cohort_scope, COHORT_SCOPE_EXPLICIT)
        self.assertEqual(metrics.roster_size, 0)
        self.assertEqual(metrics.cohort_size, 0)
        self.assertEqual(metrics.funnel_log_created, 0)
        self.assertEqual(metrics.funnel_chat_message, 0)

    def test_invalid_roster_ids_are_rejected(self):
        invalid_rosters = ([0], [-1], [True], ["21"])
        for roster in invalid_rosters:
            with self.subTest(roster=roster):
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    compute_retention_metrics(
                        as_of=self.as_of,
                        patient_ids=roster,  # type: ignore[arg-type]
                    )


class FunnelCountsTest(TestCase):
    def setUp(self):
        self.as_of = timezone.now()
        base = self.as_of - timedelta(days=5)
        for patient_id in (10, 11, 12):
            _evt_at(EVT_SESSION_START, patient_id, base)
        for patient_id in (10, 11):
            _evt_at(EVT_LOG_CREATED, patient_id, base + timedelta(minutes=5))
        _evt_at(EVT_CHAT_MESSAGE, 10, base + timedelta(hours=1))

    def test_funnel_counts(self):
        metrics = compute_retention_metrics(as_of=self.as_of)

        self.assertEqual(metrics.funnel_session_start, 3)
        self.assertEqual(metrics.funnel_log_created, 2)
        self.assertEqual(metrics.funnel_chat_message, 1)
        self.assertEqual(metrics.funnel_summary_viewed, 0)
        self.assertEqual(metrics.cohort_size, 2)
        self.assertEqual(metrics.chat_per_active_patient, 0.5)


class ContractValidationTest(TestCase):
    def test_dataclass_is_immutable(self):
        metrics = compute_retention_metrics()
        with self.assertRaises(FrozenInstanceError):
            metrics.cohort_size = 99  # type: ignore[misc]

    def test_acquisition_event_rejects_quote_injection(self):
        with self.assertRaises(ValueError):
            compute_retention_metrics("log_created' OR 1=1 --")
