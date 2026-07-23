"""P0 regression tests: authentication must never fabricate patient facts."""

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User

from core.api.v1.auth import _ensure_profile, _resolve_user
from core.models import BasePatientProfile
from diabetes.api.v1.profile import ProfilePatchSchema, patch_profile
from diabetes.models import DiabetesProfile


@pytest.mark.django_db
def test_new_auth_identity_has_no_invented_clinical_or_demographic_facts():
    user = _resolve_user("firebase-p0-new", "p0-new@example.test")

    base = BasePatientProfile.objects.get(patient=user)
    diabetes = DiabetesProfile.objects.get(base_profile=base)

    assert base.firebase_uid == "firebase-p0-new"
    assert base.date_of_birth is None
    assert base.gender is None
    assert diabetes.diabetes_type is None
    assert diabetes.treatment_type is None
    assert diabetes.clinical_profile_complete is False


@pytest.mark.django_db
def test_legacy_identity_profile_shell_is_created_without_fake_defaults():
    user = User.objects.create_user(username="firebase-p0-legacy")

    _ensure_profile(user, "firebase-p0-legacy")

    base = user.base_profile
    diabetes = base.diabetes_profile
    assert base.date_of_birth is None
    assert base.gender is None
    assert diabetes.diabetes_type is None
    assert diabetes.treatment_type is None


@pytest.mark.django_db
def test_patient_declaration_transitions_profile_to_complete():
    user = _resolve_user("firebase-p0-declared", "declared@example.test")
    request = SimpleNamespace(user=user)

    patch_profile(
        request,
        ProfilePatchSchema(
            diabetes_type="type1",
            treatment_type="insulin_injections",
            gender="male",
        ),
    )

    base = BasePatientProfile.objects.get(patient=user)
    diabetes = DiabetesProfile.objects.get(base_profile=base)
    assert base.gender == "male"
    assert diabetes.diabetes_type == "type1"
    assert diabetes.treatment_type == "insulin_injections"
    assert diabetes.clinical_profile_complete is True


def test_invalid_clinical_declaration_is_rejected():
    with pytest.raises(ValueError):
        ProfilePatchSchema(diabetes_type="guessed-type")

    with pytest.raises(ValueError):
        ProfilePatchSchema(treatment_type="guessed-treatment")
