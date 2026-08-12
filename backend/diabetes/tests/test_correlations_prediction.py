"""Fail-closed contracts for retired clinical prototypes."""

from django.contrib.auth.models import User
from django.test import TestCase

from diabetes.services.clinical.correlations import analyze_lifestyle_impact
from diabetes.services.clinical.prediction import predict_glucose


class RetiredPrototypeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="prototype-guard", password="x")

    def test_unvalidated_lifestyle_correlation_returns_no_authority(self):
        self.assertEqual(analyze_lifestyle_impact(self.user), [])

    def test_unvalidated_glucose_prediction_returns_no_authority(self):
        self.assertIsNone(predict_glucose(self.user))

    def test_prediction_hours_ahead_cannot_reenable_prototype(self):
        self.assertIsNone(predict_glucose(self.user, hours_ahead=6))
