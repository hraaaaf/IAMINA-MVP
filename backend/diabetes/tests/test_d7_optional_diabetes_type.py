"""D7 six types, absent/unknown distinction and clinical fail-closed."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.test import TestCase
from pydantic import ValidationError

from core.models import BasePatientProfile
from diabetes.api.v1.profile import ProfilePatchSchema, patch_profile
from diabetes.models import DiabetesProfile


def test_d7_unknown_and_other_are_explicit_nonclinical_types():
    for code in ("other", "unknown"):
        assert ProfilePatchSchema(diabetes_type=code).diabetes_type == code


@pytest.mark.parametrize("code", ["pre", "made-up", "type-3"])
def test_d7_unsupported_diagnosis_codes_remain_rejected(code):
    with pytest.raises(ValidationError):
        ProfilePatchSchema(diabetes_type=code)


class D7TypeApplicabilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="d7-type-synthetic")
        base = BasePatientProfile.objects.create(patient=self.user)
        self.profile = DiabetesProfile.objects.create(
            base_profile=base,
            diabetes_type="type2",
            treatment_type="oral_meds",
            target_range_provenance="clinician_confirmed",
            target_population_context="individualized",
        )

    @patch("diabetes.services.session_cache.invalidate")
    def test_unknown_does_not_keep_clinical_completeness_or_target_authority(
        self, _invalidate
    ):
        patch_profile(
            SimpleNamespace(user=self.user),
            ProfilePatchSchema(diabetes_type="unknown"),
        )
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.clinical_profile_complete)
        self.assertEqual(
            self.profile.target_range_provenance,
            "clinician_confirmation_stale",
        )
        self.assertEqual(self.profile.target_population_context, "unknown")

    @patch("diabetes.services.session_cache.invalidate")
    def test_other_does_not_infer_a_diabetes_type(
        self, _invalidate
    ):
        patch_profile(
            SimpleNamespace(user=self.user),
            ProfilePatchSchema(diabetes_type="other"),
        )
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.clinical_profile_complete)
        self.assertEqual(self.profile.diabetes_type, "other")
        self.assertEqual(self.profile.treatment_type, "oral_meds")

    def test_null_stays_distinct_from_explicit_unknown(self):
        self.profile.diabetes_type = None
        self.profile.save(update_fields=["diabetes_type"])
        self.profile.refresh_from_db()
        self.assertIsNone(self.profile.diabetes_type)
        self.assertFalse(self.profile.clinical_profile_complete)
