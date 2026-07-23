from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from diabetes.models import LogEntry
from diabetes.services.clinical.correlations import analyze_lifestyle_impact
from diabetes.services.clinical.prediction import predict_glucose


class CorrelationsPredictionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="predictor", password="x")

    def _log(
        self,
        hours_ago: int,
        blood_sugar: float,
        *,
        stressed: str = "no",
        sleep_quality: str = "good",
        exercised: str = "no",
        fatigue_level: str = "ok",
    ) -> None:
        ts = timezone.now() - timedelta(hours=hours_ago)
        entry = LogEntry.objects.create(
            patient=self.user,
            blood_sugar=blood_sugar,
            stressed=stressed,
            sleep_quality=sleep_quality,
            exercised=exercised,
            fatigue_level=fatigue_level,
            meal_type="other",
            logged_at=ts,
        )
        LogEntry.objects.filter(pk=entry.pk).update(created_at=ts)

    def test_analyze_lifestyle_impact_returns_correlations(self):
        self._log(100, 210, stressed="yes", sleep_quality="bad")
        self._log(90, 205, stressed="yes", sleep_quality="bad")
        self._log(80, 200, stressed="yes")
        self._log(70, 130, stressed="no", sleep_quality="good", exercised="yes")
        self._log(60, 125, stressed="no", sleep_quality="good", exercised="yes")
        self._log(50, 128, stressed="no", sleep_quality="good")

        correlations = analyze_lifestyle_impact(self.user)
        factors = {item.factor for item in correlations}

        self.assertIn("stress", factors)
        self.assertIn("sleep", factors)
        self.assertTrue(all(item.sample_size >= 4 for item in correlations))

    def test_predict_glucose_returns_short_horizon_prediction(self):
        self._log(10, 140)
        self._log(8, 150, stressed="yes")
        self._log(6, 160, sleep_quality="bad")
        self._log(4, 170, exercised="yes")
        self._log(2, 180, stressed="yes", fatigue_level="tired")

        prediction = predict_glucose(self.user, hours_ahead=2)

        self.assertIsNotNone(prediction)
        assert prediction is not None
        self.assertEqual(prediction.hours_ahead, 2)
        self.assertGreaterEqual(prediction.predicted_value, 30.0)
        self.assertLessEqual(prediction.predicted_value, 600.0)
        self.assertGreater(prediction.confidence, 0.0)
        self.assertTrue(prediction.contributing_factors)

    def test_predict_glucose_returns_none_when_not_enough_data(self):
        self._log(2, 145)
        self._log(1, 150)

        self.assertIsNone(predict_glucose(self.user))
