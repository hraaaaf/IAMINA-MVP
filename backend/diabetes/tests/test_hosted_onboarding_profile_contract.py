from django.contrib.auth.models import User
from django.test import TestCase
from ninja.errors import HttpError

from core.models import BasePatientProfile
from core.models.patient_module import PatientModule
from diabetes.api.v1.profile import ProfilePatchSchema, _get_diabetes_profile
from diabetes.models import DiabetesProfile


class HostedOnboardingProfileContractTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="hosted-onboarding@example.test",
            email="hosted-onboarding@example.test",
            password="safe-test-password",
        )
        self.base = BasePatientProfile.objects.create(patient=self.user)

    def test_active_diabetes_module_can_create_empty_extension_shell(self):
        PatientModule.objects.create(
            patient=self.base,
            module_name="diabetes",
            is_active=True,
        )

        profile = _get_diabetes_profile(self.user, create_if_active=True)

        self.assertEqual(profile.base_profile_id, self.base.id)
        self.assertTrue(
            DiabetesProfile.objects.filter(base_profile=self.base).exists()
        )
        self.assertIsNone(profile.diabetes_type)
        self.assertIsNone(profile.treatment_type)

    def test_inactive_diabetes_module_does_not_create_extension_shell(self):
        with self.assertRaises(HttpError) as exc:
            _get_diabetes_profile(self.user, create_if_active=True)

        self.assertEqual(exc.exception.status_code, 404)
        self.assertFalse(
            DiabetesProfile.objects.filter(base_profile=self.base).exists()
        )

    def test_onboarding_language_contract_accepts_english(self):
        patch = ProfilePatchSchema(preferred_language="en")

        self.assertEqual(patch.preferred_language, "en")
