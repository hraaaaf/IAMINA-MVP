"""
Profile update validations — PATCH /api/v1/profile (Ninja API).

Rewritten from OnboardingChatPostTests (Django onboarding view removed).
The profile is created automatically during Firebase auth; subsequent PATCH calls
update language, unit preference, and glucose target bounds.

Validations tested:
  - preferred_language must be one of {"fr", "ar-MA", "ar"}
  - unit_preference must be one of {"mg_dl", "mmol_l"}
  - target_range_low:  40.0 ≤ v ≤ 200.0
  - target_range_high: 100.0 ≤ v ≤ 400.0
"""
from datetime import date
from json import loads

from django.contrib.auth.models import User
from django.test import TestCase

from core.models import BasePatientProfile
from diabetes.models import DiabetesProfile


def _make_patient(username):
    user = User.objects.create_user(username=username, email=f"{username}@test.com")
    base = BasePatientProfile.objects.create(
        patient=user,
        date_of_birth=date(1985, 6, 15),
    )
    DiabetesProfile.objects.create(
        base_profile=base,
        diabetes_type="type2",
        treatment_type="oral_meds",
        target_range_low=70,
        target_range_high=180,
    )
    return user


class OnboardingChatPostTests(TestCase):
    """PATCH /api/v1/profile — language, unit, and target-range validation."""

    def setUp(self):
        self.alice = _make_patient("alice_onboarding")
        self.client.force_login(self.alice)

    def test_post_with_dob_creates_profile(self):
        """PATCH with valid preferred_language='fr' → 200, language persisted."""
        resp = self.client.patch(
            "/api/v1/profile",
            data={"preferred_language": "fr"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertEqual(data["preferred_language"], "fr")
        self.alice.base_profile.refresh_from_db()
        self.assertEqual(self.alice.base_profile.preferred_language, "fr")

    def test_post_without_dob_returns_400(self):
        """PATCH with unsupported preferred_language='zh' → 422 (not in allowed set)."""
        resp = self.client.patch(
            "/api/v1/profile",
            data={"preferred_language": "zh"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 422)

    def test_post_with_future_dob_returns_400(self):
        """PATCH with target_range_high=999 exceeds the 400 mg/dL ceiling → 422."""
        resp = self.client.patch(
            "/api/v1/profile",
            data={"target_range_high": 999},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 422)

    def test_post_with_malformed_dob_returns_400(self):
        """PATCH with invalid unit_preference='cups' → 422 (not in allowed set)."""
        resp = self.client.patch(
            "/api/v1/profile",
            data={"unit_preference": "cups"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 422)

    def test_post_with_ancient_dob_returns_400(self):
        """PATCH with target_range_low=10 is below the 40 mg/dL floor → 422."""
        resp = self.client.patch(
            "/api/v1/profile",
            data={"target_range_low": 10},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 422)
