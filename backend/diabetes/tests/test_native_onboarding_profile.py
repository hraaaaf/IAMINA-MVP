from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User

from core.models import BasePatientProfile
from diabetes.api.v1.profile import ProfilePatchSchema, patch_profile
from diabetes.models import DiabetesProfile


@pytest.mark.django_db
def test_first_declared_profile_patch_materializes_diabetes_extension():
    user = User.objects.create_user(
        username="native-onboarding@example.test",
        email="native-onboarding@example.test",
        password="A-strong-passphrase-2026!",
    )
    BasePatientProfile.objects.create(patient=user)

    result = patch_profile(
        SimpleNamespace(user=user),
        ProfilePatchSchema(
            diabetes_type="prediabetes",
            treatment_type="oral_meds",
            unit_preference="mmol_l",
        ),
    )

    profile = DiabetesProfile.objects.get(base_profile__patient=user)
    assert result.pk == profile.pk
    assert profile.diabetes_type == "prediabetes"
    assert profile.treatment_type == "oral_meds"
    assert profile.unit_preference == "mmol_l"
