from datetime import date
from json import loads

from django.contrib.auth.models import User
from django.test import Client, TestCase

from core.models import BasePatientProfile
from diabetes.models import DiabetesProfile, LogEntry


def patient():
    user = User.objects.create_user(username="context_v2", email="context@test.com")
    base = BasePatientProfile.objects.create(patient=user, date_of_birth=date(1990, 1, 1))
    DiabetesProfile.objects.create(base_profile=base, diabetes_type="type2", treatment_type="lifestyle", target_range_low=70, target_range_high=180)
    return user


class JournalContextIntelligenceTests(TestCase):
    def setUp(self):
        self.user = patient()
        self.client = Client()
        self.client.force_login(self.user)

    def test_omitted_context_remains_unknown_instead_of_fabricated_negative(self):
        response = self.client.post('/api/v1/logs', data={"blood_sugar": 121}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        entry = LogEntry.objects.get(patient=self.user)
        self.assertEqual(entry.is_sick, '')
        self.assertEqual(entry.stressed, '')
        self.assertEqual(entry.exercised, '')
        self.assertEqual(entry.sleep_quality, '')
        self.assertEqual(entry.fatigue_level, '')

    def test_explicit_positive_context_is_persisted_without_inference(self):
        payload = {"blood_sugar": 121, "is_sick": "yes", "stressed": "yes", "exercised": "yes", "sleep_quality": "bad"}
        response = self.client.post('/api/v1/logs', data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertEqual(body['is_sick'], 'yes')
        self.assertEqual(body['stressed'], 'yes')
        self.assertEqual(body['exercised'], 'yes')
        self.assertEqual(body['sleep_quality'], 'bad')
