from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from diabetes.models.entry import LogEntry
from diabetes.services.clinical.personal_response import compute_personal_response


class PersonalResponseServiceTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="patient-j8")
        self.other_patient = User.objects.create_user(username="other-j8")
        self.now = timezone.now()

    def _log(
        self,
        *,
        patient=None,
        days_ago=0,
        glucose=120,
        source="manual",
        glycemic_context="",
        meal_type="",
        stressed="",
        exercised="",
        is_sick="",
        sleep_quality="",
        fatigue_level="",
    ):
        return LogEntry.objects.create(
            patient=patient or self.patient,
            logged_at=self.now - timedelta(days=days_ago),
            blood_sugar=glucose,
            source=source,
            glycemic_context=glycemic_context,
            meal_type=meal_type,
            stressed=stressed,
            exercised=exercised,
            is_sick=is_sick,
            sleep_quality=sleep_quality,
            fatigue_level=fatigue_level,
        )

    def test_requires_repetition_across_distinct_days(self):
        self._log(stressed="yes", glucose=150)
        self._log(stressed="yes", glucose=155)
        self._log(stressed="yes", glucose=160)

        result = compute_personal_response(patient_id=self.patient.id)

        self.assertEqual(result.status, "insufficient_data")
        self.assertEqual(result.patterns, ())

    def test_explicit_positive_context_yields_observational_pattern(self):
        self._log(days_ago=0, stressed="yes", glucose=150)
        self._log(days_ago=1, stressed="yes", glucose=160)
        self._log(days_ago=2, stressed="yes", glucose=170)
        self._log(days_ago=3, glucose=110)

        result = compute_personal_response(patient_id=self.patient.id)

        self.assertEqual(result.status, "ready")
        pattern = next(item for item in result.patterns if item.key == "context:stress")
        self.assertEqual(pattern.observations, 3)
        self.assertEqual(pattern.distinct_days, 3)
        self.assertEqual(pattern.median_glucose_mg_dl, 160.0)
        self.assertEqual(pattern.window_median_glucose_mg_dl, 155.0)
        self.assertEqual(pattern.confidence, "limited")

    def test_historical_negative_or_neutral_values_are_never_control_patterns(self):
        for index in range(8):
            self._log(
                days_ago=index,
                glucose=120 + index,
                stressed="no",
                exercised="no",
                is_sick="no",
                sleep_quality="good",
                fatigue_level="ok",
            )

        result = compute_personal_response(patient_id=self.patient.id)

        self.assertEqual(result.status, "insufficient_data")
        self.assertEqual(result.patterns, ())

    def test_demo_entries_never_contribute_to_personal_patterns(self):
        for index in range(4):
            self._log(
                days_ago=index,
                glucose=200,
                stressed="yes",
                source="demo",
            )
        self._log(days_ago=0, glucose=110)
        self._log(days_ago=1, glucose=115)
        self._log(days_ago=2, glucose=120)

        result = compute_personal_response(patient_id=self.patient.id)

        self.assertEqual(result.status, "insufficient_data")
        self.assertEqual(result.patterns, ())
        self.assertEqual(result.total_readings, 3)

    def test_other_patient_data_is_isolated(self):
        for index in range(4):
            self._log(
                patient=self.other_patient,
                days_ago=index,
                glucose=210,
                is_sick="yes",
            )
        self._log(days_ago=0, glucose=100)
        self._log(days_ago=1, glucose=105)
        self._log(days_ago=2, glucose=110)

        result = compute_personal_response(patient_id=self.patient.id)

        self.assertEqual(result.status, "insufficient_data")
        self.assertFalse(any(item.key == "context:illness" for item in result.patterns))

    def test_meal_pattern_requires_explicit_post_meal_measurement_context(self):
        self._log(days_ago=0, glucose=150, meal_type="lunch")
        self._log(days_ago=1, glucose=160, meal_type="lunch")
        self._log(days_ago=2, glucose=170, meal_type="lunch")
        self._log(days_ago=3, glucose=140)

        first = compute_personal_response(patient_id=self.patient.id)
        self.assertFalse(any(item.key == "meal:lunch" for item in first.patterns))

        LogEntry.objects.all().delete()
        self._log(
            days_ago=0,
            glucose=150,
            meal_type="lunch",
            glycemic_context="post_meal",
        )
        self._log(
            days_ago=1,
            glucose=160,
            meal_type="lunch",
            glycemic_context="post_meal",
        )
        self._log(
            days_ago=2,
            glucose=170,
            meal_type="lunch",
            glycemic_context="post_meal",
        )
        self._log(days_ago=3, glucose=140)

        second = compute_personal_response(patient_id=self.patient.id)
        self.assertTrue(any(item.key == "meal:lunch" for item in second.patterns))

    def test_evidence_grade_is_repeatability_not_probability(self):
        for index in range(8):
            self._log(days_ago=index, glucose=130 + index, exercised="yes")

        result = compute_personal_response(patient_id=self.patient.id)
        pattern = next(item for item in result.patterns if item.key == "context:activity")

        self.assertEqual(pattern.confidence, "strong")
        self.assertNotIsInstance(pattern.confidence, float)
