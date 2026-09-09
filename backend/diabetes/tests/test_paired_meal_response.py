from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from ninja.errors import HttpError
from pydantic import ValidationError

from diabetes.api.v1.logs import batch_create_logs, create_log, update_log
from diabetes.api.v1.schemas import LogEntryCreateSchema, LogEntryUpdateSchema
from diabetes.models.entry import LogEntry
from diabetes.services.clinical.paired_meal_response import compute_paired_meal_response


class PairedMealResponseTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="a7-paired")
        self.other_patient = User.objects.create_user(username="a7-other")
        self.now = timezone.now()

    def _log(
        self,
        *,
        patient=None,
        episode_id=None,
        context="pre_meal",
        meal_type="lunch",
        glucose=120,
        days_ago=0,
        minutes_offset=0,
        source="manual",
    ):
        return LogEntry.objects.create(
            patient=patient or self.patient,
            meal_episode_id=episode_id,
            glycemic_context=context,
            meal_type=meal_type,
            blood_sugar=glucose,
            logged_at=(
                self.now
                - timedelta(days=days_ago)
                + timedelta(minutes=minutes_offset)
            ),
            source=source,
        )

    def _pair(
        self,
        *,
        patient=None,
        episode_id=None,
        meal_type="lunch",
        pre=110,
        post=150,
        days_ago=0,
        elapsed_minutes=90,
        source="manual",
    ):
        episode_id = episode_id or uuid4()
        self._log(
            patient=patient,
            episode_id=episode_id,
            context="pre_meal",
            meal_type=meal_type,
            glucose=pre,
            days_ago=days_ago,
            minutes_offset=-elapsed_minutes,
            source=source,
        )
        self._log(
            patient=patient,
            episode_id=episode_id,
            context="post_meal",
            meal_type=meal_type,
            glucose=post,
            days_ago=days_ago,
            source=source,
        )
        return episode_id

    def test_exact_episode_pair_computes_descriptive_delta(self):
        episode_id = self._pair(pre=105, post=160, elapsed_minutes=75)

        result = compute_paired_meal_response(patient_id=self.patient.id)

        self.assertEqual(result.status, "ready")
        self.assertEqual(result.explicit_episode_count, 1)
        self.assertEqual(result.complete_pair_count, 1)
        pair = result.pairs[0]
        self.assertEqual(pair.episode_id, episode_id)
        self.assertEqual(pair.pre_glucose_mg_dl, 105.0)
        self.assertEqual(pair.post_glucose_mg_dl, 160.0)
        self.assertEqual(pair.delta_mg_dl, 55.0)
        self.assertEqual(pair.elapsed_minutes, 75.0)

    def test_temporal_proximity_without_episode_id_is_never_paired(self):
        self._log(context="pre_meal", glucose=100, minutes_offset=-60)
        self._log(context="post_meal", glucose=180)

        result = compute_paired_meal_response(patient_id=self.patient.id)

        self.assertEqual(result.status, "insufficient_data")
        self.assertEqual(result.explicit_episode_count, 0)
        self.assertEqual(result.pairs, ())

    def test_incomplete_explicit_episode_is_reported_not_inferred(self):
        episode_id = uuid4()
        self._log(episode_id=episode_id, context="post_meal", glucose=170)

        result = compute_paired_meal_response(patient_id=self.patient.id)

        self.assertEqual(result.explicit_episode_count, 1)
        self.assertEqual(result.complete_pair_count, 0)
        self.assertEqual(result.incomplete_or_invalid_episode_count, 1)

    def test_mismatched_meal_types_make_episode_invalid(self):
        episode_id = uuid4()
        self._log(
            episode_id=episode_id,
            context="pre_meal",
            meal_type="lunch",
            glucose=100,
            minutes_offset=-60,
        )
        self._log(
            episode_id=episode_id,
            context="post_meal",
            meal_type="dinner",
            glucose=150,
        )

        result = compute_paired_meal_response(patient_id=self.patient.id)

        self.assertEqual(result.complete_pair_count, 0)
        self.assertEqual(result.incomplete_or_invalid_episode_count, 1)

    def test_post_must_follow_pre_but_no_clinical_timing_window_is_inferred(self):
        episode_id = uuid4()
        self._log(
            episode_id=episode_id,
            context="pre_meal",
            glucose=110,
            minutes_offset=20,
        )
        self._log(
            episode_id=episode_id,
            context="post_meal",
            glucose=150,
        )

        result = compute_paired_meal_response(patient_id=self.patient.id)

        self.assertEqual(result.complete_pair_count, 0)

    def test_same_episode_uuid_is_isolated_by_patient(self):
        shared = uuid4()
        self._pair(episode_id=shared, pre=100, post=130)
        self._pair(
            patient=self.other_patient,
            episode_id=shared,
            pre=200,
            post=250,
        )

        result = compute_paired_meal_response(patient_id=self.patient.id)

        self.assertEqual(result.complete_pair_count, 1)
        self.assertEqual(result.pairs[0].delta_mg_dl, 30.0)

    def test_database_rejects_duplicate_role_for_same_patient_episode(self):
        episode_id = uuid4()
        self._log(episode_id=episode_id, context="pre_meal", glucose=100)

        with self.assertRaises(IntegrityError), transaction.atomic():
            self._log(episode_id=episode_id, context="pre_meal", glucose=120)

    @patch("diabetes.api.v1.logs.track")
    @patch("diabetes.api.v1.logs._invalidate_ctx")
    @patch("diabetes.api.v1.logs._invalidate_kpis")
    def test_create_duplicate_role_returns_conflict_not_server_error(
        self,
        _invalidate_kpis_mock,
        _invalidate_ctx_mock,
        _track_mock,
    ):
        episode_id = uuid4()
        self._log(episode_id=episode_id, context="pre_meal", meal_type="lunch")
        request = SimpleNamespace(user=self.patient)

        with self.assertRaises(HttpError) as caught:
            create_log(
                request,
                LogEntryCreateSchema(
                    blood_sugar=130,
                    meal_episode_id=episode_id,
                    glycemic_context="pre_meal",
                    meal_type="lunch",
                ),
            )

        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(
            LogEntry.objects.filter(
                patient=self.patient,
                meal_episode_id=episode_id,
                glycemic_context="pre_meal",
            ).count(),
            1,
        )

    @patch("diabetes.api.v1.logs._invalidate_ctx")
    @patch("diabetes.api.v1.logs._invalidate_kpis")
    def test_patch_duplicate_role_returns_conflict_and_rolls_back(
        self,
        _invalidate_kpis_mock,
        _invalidate_ctx_mock,
    ):
        occupied_episode = uuid4()
        original_episode = uuid4()
        self._log(
            episode_id=occupied_episode,
            context="pre_meal",
            meal_type="lunch",
        )
        candidate = self._log(
            episode_id=original_episode,
            context="pre_meal",
            meal_type="lunch",
        )
        request = SimpleNamespace(user=self.patient)

        with self.assertRaises(HttpError) as caught:
            update_log(
                request,
                candidate.id,
                LogEntryUpdateSchema(meal_episode_id=occupied_episode),
            )

        self.assertEqual(caught.exception.status_code, 409)
        candidate.refresh_from_db()
        self.assertEqual(candidate.meal_episode_id, original_episode)

    def test_demo_episode_never_enters_paired_analytics(self):
        self._pair(source="demo", pre=100, post=220)

        result = compute_paired_meal_response(patient_id=self.patient.id)

        self.assertEqual(result.explicit_episode_count, 0)
        self.assertEqual(result.complete_pair_count, 0)

    def test_repeated_exact_pairs_build_descriptive_meal_pattern(self):
        self._pair(days_ago=0, pre=100, post=140)
        self._pair(days_ago=1, pre=110, post=160)
        self._pair(days_ago=2, pre=120, post=180)

        result = compute_paired_meal_response(patient_id=self.patient.id)

        self.assertEqual(result.complete_pair_count, 3)
        self.assertEqual(len(result.patterns), 1)
        pattern = result.patterns[0]
        self.assertEqual(pattern.meal_type, "lunch")
        self.assertEqual(pattern.pairs, 3)
        self.assertEqual(pattern.distinct_days, 3)
        self.assertEqual(pattern.median_pre_glucose_mg_dl, 110.0)
        self.assertEqual(pattern.median_post_glucose_mg_dl, 160.0)
        self.assertEqual(pattern.median_delta_mg_dl, 50.0)
        self.assertEqual(pattern.evidence_density, "limited")
        self.assertEqual(pattern.evidence_id, "rule.personal-response.repetition.v1")

    def test_negative_delta_is_preserved_as_observed_fact(self):
        self._pair(pre=180, post=130)

        result = compute_paired_meal_response(patient_id=self.patient.id)

        self.assertEqual(result.pairs[0].delta_mg_dl, -50.0)

    def test_create_schema_requires_explicit_pairing_context_and_meal_type(self):
        with self.assertRaises(ValidationError):
            LogEntryCreateSchema(
                blood_sugar=120,
                meal_episode_id=uuid4(),
                glycemic_context="other",
                meal_type="lunch",
            )
        with self.assertRaises(ValidationError):
            LogEntryCreateSchema(
                blood_sugar=120,
                meal_episode_id=uuid4(),
                glycemic_context="pre_meal",
                meal_type="other",
            )

    @patch("diabetes.api.v1.logs._invalidate_ctx")
    @patch("diabetes.api.v1.logs._invalidate_kpis")
    def test_patch_cannot_leave_episode_on_non_meal_context_and_can_clear_link(
        self,
        _invalidate_kpis_mock,
        _invalidate_ctx_mock,
    ):
        episode_id = uuid4()
        log = self._log(
            episode_id=episode_id,
            context="pre_meal",
            meal_type="lunch",
        )
        request = SimpleNamespace(user=self.patient)

        with self.assertRaises(HttpError) as caught:
            update_log(
                request,
                log.id,
                LogEntryUpdateSchema(glycemic_context="other"),
            )
        self.assertEqual(caught.exception.status_code, 422)

        update_log(
            request,
            log.id,
            LogEntryUpdateSchema(meal_episode_id=None),
        )
        log.refresh_from_db()
        self.assertIsNone(log.meal_episode_id)

    @patch("diabetes.api.v1.logs.track")
    @patch("diabetes.api.v1.logs._invalidate_ctx")
    @patch("diabetes.api.v1.logs._invalidate_kpis")
    def test_batch_integrity_conflict_does_not_poison_later_valid_row(
        self,
        _invalidate_kpis_mock,
        _invalidate_ctx_mock,
        _track_mock,
    ):
        occupied_episode = uuid4()
        self._log(
            episode_id=occupied_episode,
            context="pre_meal",
            meal_type="lunch",
        )
        conflicting_uuid = uuid4()
        valid_uuid = uuid4()
        valid_episode = uuid4()
        request = SimpleNamespace(user=self.patient)

        result = batch_create_logs(
            request,
            [
                LogEntryCreateSchema(
                    blood_sugar=130,
                    client_uuid=conflicting_uuid,
                    meal_episode_id=occupied_episode,
                    glycemic_context="pre_meal",
                    meal_type="lunch",
                ),
                LogEntryCreateSchema(
                    blood_sugar=140,
                    client_uuid=valid_uuid,
                    meal_episode_id=valid_episode,
                    glycemic_context="pre_meal",
                    meal_type="lunch",
                ),
            ],
        )

        self.assertEqual(result["synced_ids"], [valid_uuid])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("data conflict", result["errors"][0])
        self.assertNotIn("uniq_patient_meal_episode_role", result["errors"][0])
        self.assertTrue(LogEntry.objects.filter(client_uuid=valid_uuid).exists())
        self.assertFalse(LogEntry.objects.filter(client_uuid=conflicting_uuid).exists())

    def test_limitations_are_explicitly_non_causal(self):
        self._pair()
        result = compute_paired_meal_response(patient_id=self.patient.id)
        joined = " ".join(result.limitations)

        self.assertIn("descriptive_not_causal", joined)
        self.assertIn("no_temporal_pairing_inference", joined)
        self.assertNotIn("probability", joined)
