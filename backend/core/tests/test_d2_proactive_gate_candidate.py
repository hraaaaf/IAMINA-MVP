"""Synthetic-only D2 proactive gate tests: no patient, database, or delivery."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest import TestCase

from core.d2_proactive_gate_candidate import (
    D2DryRunVerdict,
    D2ProactiveCandidate,
    evaluate_d2_proactive_dry_run,
)


class TestD2ProactiveInAppGate(TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)
        self.candidate = D2ProactiveCandidate(
            patient_id=7,
            record_patient_id=7,
            auth_epoch=2,
            current_auth_epoch=2,
            unlocked=True,
            proactive_opt_in=True,
            server_consent_confirmed=True,
            category_enabled=True,
            global_ai_opt_out=False,
            channel="in_app_notification",
            kind="proactive",
            event_type="weekly_report_ready",
            source_contract_version="d2.inapp.synthetic.v1",
            source_verified=True,
            evidence_id="synthetic-proof-1",
            event_signature="opaque-synthetic-signature",
            evidence_at=self.now - timedelta(minutes=1),
            now=self.now,
        )

    def check(self, expected, **changes):
        self.assertEqual(evaluate_d2_proactive_dry_run(replace(self.candidate, **changes)), expected)

    def test_positive_is_only_a_dry_run_never_delivery(self):
        self.check(D2DryRunVerdict.CANDIDATE_ONLY)
        self.check(D2DryRunVerdict.CANDIDATE_ONLY, event_type="profile_completion_available")

    def test_reminder_and_companion_are_not_d2_notifications(self):
        for channel in ("reminder", "companion_conversation", "browser_push"):
            with self.subTest(channel=channel):
                self.check(D2DryRunVerdict.WRONG_SURFACE, channel=channel)
        self.check(D2DryRunVerdict.WRONG_SURFACE, kind="event")

    def test_unauthenticated_or_cross_patient_is_denied(self):
        self.check(D2DryRunVerdict.NOT_AUTHORIZED, patient_id=None)
        self.check(D2DryRunVerdict.NOT_AUTHORIZED, patient_id=0)
        self.check(D2DryRunVerdict.NOT_AUTHORIZED, record_patient_id=9)
        self.check(D2DryRunVerdict.NOT_AUTHORIZED, unlocked=False)

    def test_stale_or_invalid_epoch_is_denied(self):
        self.check(D2DryRunVerdict.STALE_SESSION, auth_epoch=1)
        self.check(D2DryRunVerdict.STALE_SESSION, current_auth_epoch=-1)

    def test_off_by_default_and_rapid_revocation(self):
        self.check(D2DryRunVerdict.CONSENT_MISSING, proactive_opt_in=False)
        self.check(D2DryRunVerdict.CONSENT_MISSING, server_consent_confirmed=False)
        self.check(D2DryRunVerdict.CONSENT_MISSING, category_enabled=False)
        self.check(D2DryRunVerdict.CONSENT_MISSING, global_ai_opt_out=True)

    def test_untrusted_or_missing_source_never_qualifies(self):
        self.check(D2DryRunVerdict.UNVERIFIED_SOURCE, source_verified=False)
        self.check(D2DryRunVerdict.UNVERIFIED_SOURCE, evidence_id=" ")
        self.check(D2DryRunVerdict.UNVERIFIED_SOURCE, event_signature="")
        self.check(D2DryRunVerdict.UNVERIFIED_SOURCE, source_contract_version="unknown")
        self.check(D2DryRunVerdict.UNVERIFIED_SOURCE, event_type="synthetic_glucose_hypo_alert")
        self.check(D2DryRunVerdict.UNVERIFIED_SOURCE, event_type="unknown")

    def test_no_urgent_clinical_or_sensitive_previews(self):
        self.check(D2DryRunVerdict.CLINICAL_SCOPE, claims_urgent=True)
        self.check(D2DryRunVerdict.CLINICAL_SCOPE, suggests_treatment=True)
        self.check(D2DryRunVerdict.CLINICAL_SCOPE, contains_sensitive_preview=True)

    def test_timezones_future_data_and_stale_evidence(self):
        self.check(D2DryRunVerdict.INVALID_TIMELINE, now=self.now.replace(tzinfo=None))
        self.check(D2DryRunVerdict.INVALID_TIMELINE, evidence_at=self.now.replace(tzinfo=None))
        self.check(D2DryRunVerdict.INVALID_TIMELINE, evidence_at=self.now + timedelta(seconds=1))
        self.check(D2DryRunVerdict.INVALID_TIMELINE, evidence_at=self.now - timedelta(days=7, seconds=1))
        self.check(D2DryRunVerdict.CANDIDATE_ONLY, evidence_at=self.now - timedelta(days=7))

    def test_history_must_be_server_scoped_and_timestamp_valid(self):
        self.check(D2DryRunVerdict.INVALID_TIMELINE, previous_proactive_at=(self.now + timedelta(seconds=1),))
        self.check(D2DryRunVerdict.INVALID_TIMELINE, previous_proactive_at=(self.now.replace(tzinfo=None),))
        self.check(D2DryRunVerdict.INVALID_TIMELINE, last_same_event_at=self.now + timedelta(seconds=1))

    def test_same_event_cannot_repeat_within_seven_days(self):
        self.check(D2DryRunVerdict.DUPLICATE, last_same_event_at=self.now - timedelta(days=6))
        self.check(D2DryRunVerdict.CANDIDATE_ONLY, last_same_event_at=self.now - timedelta(days=7))
        self.check(D2DryRunVerdict.DUPLICATE, last_same_event_at=self.now - timedelta(minutes=1),
                   previous_proactive_at=(self.now - timedelta(minutes=2),))

    def test_daily_cap_is_rolling_24_hours(self):
        self.check(D2DryRunVerdict.DAILY_CAP, previous_proactive_at=(self.now - timedelta(hours=23),))
        self.check(D2DryRunVerdict.CANDIDATE_ONLY, previous_proactive_at=(self.now - timedelta(hours=24),))

    def test_weekly_cap_two_items_per_rolling_seven_days(self):
        self.check(D2DryRunVerdict.WEEKLY_CAP, previous_proactive_at=(
            self.now - timedelta(days=2), self.now - timedelta(days=4),
        ))
        self.check(D2DryRunVerdict.CANDIDATE_ONLY, previous_proactive_at=(
            self.now - timedelta(days=7), self.now - timedelta(days=2),
        ))
        self.check(D2DryRunVerdict.DAILY_CAP, previous_proactive_at=(
            self.now - timedelta(days=2), self.now - timedelta(minutes=2),
        ))

    def test_untyped_flags_are_not_implicit_permission(self):
        # Runtime dataclasses do not enforce type hints: reject forged truthy strings.
        self.check(D2DryRunVerdict.NOT_AUTHORIZED, patient_id=True)
        self.check(D2DryRunVerdict.NOT_AUTHORIZED, unlocked="true")
        self.check(D2DryRunVerdict.STALE_SESSION, auth_epoch="2")
        self.check(D2DryRunVerdict.CONSENT_MISSING, proactive_opt_in="yes")
        self.check(D2DryRunVerdict.CONSENT_MISSING, global_ai_opt_out="false")
        self.check(D2DryRunVerdict.UNVERIFIED_SOURCE, source_verified="true")
        self.check(D2DryRunVerdict.UNVERIFIED_SOURCE, event_type=[])
        self.check(D2DryRunVerdict.UNVERIFIED_SOURCE, evidence_id=None)
        self.check(D2DryRunVerdict.UNVERIFIED_SOURCE, event_signature=None)
        self.check(D2DryRunVerdict.CLINICAL_SCOPE, suggests_treatment="false")
        self.check(D2DryRunVerdict.INVALID_TIMELINE, previous_proactive_at=[])

    def test_pure_and_repeatable_no_bookkeeping_or_side_effects(self):
        original = self.candidate
        self.assertEqual(evaluate_d2_proactive_dry_run(original), D2DryRunVerdict.CANDIDATE_ONLY)
        self.assertEqual(evaluate_d2_proactive_dry_run(original), D2DryRunVerdict.CANDIDATE_ONLY)
        self.assertEqual(original.previous_proactive_at, ())
        self.assertEqual(original.event_signature, "opaque-synthetic-signature")
