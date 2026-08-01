"""P0 regression tests: authentication must never fabricate patient facts."""

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User

from core.auth_migration import VerifiedFirebaseIdentity, migrate_new_firebase_identity
from core.models import BasePatientProfile
from diabetes.api.v1.profile import ProfilePatchSchema, patch_profile
from diabetes.models import DiabetesProfile


def _migrate(uid: str, email: str):
    return migrate_new_firebase_identity(
        VerifiedFirebaseIdentity(uid=uid, email=email, email_verified=True)
    )


@pytest.mark.django_db
def test_new_auth_identity_has_no_invented_clinical_or_demographic_facts():
    user = _migrate("firebase-p0-new", "p0-new@example.test")

    base = BasePatientProfile.objects.get(patient=user)
    diabetes = DiabetesProfile.objects.get(base_profile=base)

    assert base.firebase_uid == "firebase-p0-new"
    assert base.date_of_birth is None
    assert base.gender is None
    assert diabetes.diabetes_type is None
    assert diabetes.treatment_type is None
    assert diabetes.clinical_profile_complete is False


@pytest.mark.django_db
def test_existing_migrated_identity_is_idempotent_without_fake_defaults():
    first = _migrate("firebase-p0-legacy", "legacy@example.test")
    second = _migrate("firebase-p0-legacy", "legacy@example.test")

    assert second.pk == first.pk
    base = second.base_profile
    diabetes = base.diabetes_profile
    assert base.date_of_birth is None
    assert base.gender is None
    assert diabetes.diabetes_type is None
    assert diabetes.treatment_type is None


@pytest.mark.django_db
def test_patient_declaration_transitions_profile_to_complete():
    user = _migrate("firebase-p0-declared", "declared@example.test")
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


def test_required_profile_fields_cannot_be_explicitly_cleared():
    for field in (
        "preferred_language",
        "unit_preference",
        "target_range_low",
        "target_range_high",
    ):
        with pytest.raises(ValueError):
            ProfilePatchSchema(**{field: None})


def test_nullable_patient_declarations_can_be_explicitly_cleared():
    patch = ProfilePatchSchema(
        diabetes_type=None,
        treatment_type=None,
        gender=None,
        date_of_birth=None,
    )
    assert patch.model_fields_set == {
        "diabetes_type",
        "treatment_type",
        "gender",
        "date_of_birth",
    }
