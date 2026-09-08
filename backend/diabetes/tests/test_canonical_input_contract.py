from datetime import timedelta

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from pydantic import ValidationError

from diabetes.api.v1.schemas import LogEntryCreateSchema
from diabetes.contracts.log_entry import (
    GLUCOSE_MAX_MG_DL,
    GLUCOSE_MIN_MG_DL,
    LogInputValidationError,
    convert_glucose_to_mg_dl,
    validate_logged_at,
    validate_mg_dl,
)
from diabetes.middleware.unit_guard import UnitGuardMiddleware
from diabetes.models import LogEntry


class CanonicalGlucoseContractTests(SimpleTestCase):
    def test_bounds_are_identical_and_inclusive(self):
        self.assertEqual(validate_mg_dl(GLUCOSE_MIN_MG_DL), 30.0)
        self.assertEqual(validate_mg_dl(GLUCOSE_MAX_MG_DL), 600.0)
        with self.assertRaises(LogInputValidationError):
            validate_mg_dl(29.9)
        with self.assertRaises(LogInputValidationError):
            validate_mg_dl(600.1)

    def test_supported_units_normalize_to_mg_dl(self):
        self.assertEqual(convert_glucose_to_mg_dl(120, "mg/dL"), 120.0)
        self.assertEqual(convert_glucose_to_mg_dl(1.2, "g/L"), 120.0)
        self.assertEqual(convert_glucose_to_mg_dl(5.55, "mmol/L"), 100.0)

    def test_non_finite_or_unknown_units_fail_closed(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.assertRaises(LogInputValidationError):
                validate_mg_dl(value)
        with self.assertRaises(LogInputValidationError):
            convert_glucose_to_mg_dl(5.5, "unknown")

    def test_batch_unit_guard_uses_same_contract(self):
        payload = [
            {"blood_sugar": 1.2, "unit": "g/L"},
            {"blood_sugar": 5.55, "unit": "mmol/L"},
        ]
        self.assertTrue(UnitGuardMiddleware._normalise_payload(payload))
        self.assertEqual(payload[0]["blood_sugar"], 120.0)
        self.assertEqual(payload[0]["unit"], "mg/dL")
        self.assertEqual(payload[1]["blood_sugar"], 100.0)
        self.assertEqual(payload[1]["unit"], "mg/dL")


class CanonicalTimestampAndEnumTests(SimpleTestCase):
    def test_timestamp_allows_small_clock_skew_but_rejects_future_data(self):
        now = timezone.now()
        accepted = now + timedelta(minutes=4, seconds=59)
        self.assertEqual(validate_logged_at(accepted, now=now), accepted)
        with self.assertRaises(LogInputValidationError):
            validate_logged_at(now + timedelta(minutes=5, seconds=1), now=now)

    def test_naive_timestamp_is_rejected(self):
        naive = timezone.now().replace(tzinfo=None)
        with self.assertRaises(LogInputValidationError):
            validate_logged_at(naive)

    def test_schema_rejects_unknown_context_values(self):
        with self.assertRaises(ValidationError):
            LogEntryCreateSchema(blood_sugar=100, stressed="maybe")
        with self.assertRaises(ValidationError):
            LogEntryCreateSchema(blood_sugar=100, source="other_provider")
        with self.assertRaises(ValidationError):
            LogEntryCreateSchema(blood_sugar=100, glycemic_context="after_coffee")

    def test_schema_uses_same_glucose_bounds(self):
        LogEntryCreateSchema(blood_sugar=30)
        LogEntryCreateSchema(blood_sugar=600)
        with self.assertRaises(ValidationError):
            LogEntryCreateSchema(blood_sugar=29.9)
        with self.assertRaises(ValidationError):
            LogEntryCreateSchema(blood_sugar=600.1)

    def test_schema_rejects_future_logged_at(self):
        with self.assertRaises(ValidationError):
            LogEntryCreateSchema(
                blood_sugar=100,
                logged_at=timezone.now() + timedelta(minutes=6),
            )


class CanonicalDatabaseBoundaryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="analysis1-contract")

    def test_database_uses_same_inclusive_glucose_bounds(self):
        low = LogEntry.objects.create(patient=self.user, blood_sugar=30)
        high = LogEntry.objects.create(patient=self.user, blood_sugar=600)
        self.assertEqual(float(low.blood_sugar), 30.0)
        self.assertEqual(float(high.blood_sugar), 600.0)

        for value in (29.9, 600.1):
            with self.assertRaises(IntegrityError), transaction.atomic():
                LogEntry.objects.create(patient=self.user, blood_sugar=value)
