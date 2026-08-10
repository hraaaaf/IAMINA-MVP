from datetime import date
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User
from pydantic import ValidationError

from core.models import BasePatientProfile
from diabetes.api.v1.profile import ProfilePatchSchema, patch_profile
from diabetes.models import DiabetesProfile


@pytest.fixture
def patient(db):
    user = User.objects.create_user(username="ramadan-period-patient")
    base = BasePatientProfile.objects.create(patient=user)
    DiabetesProfile.objects.create(base_profile=base)
    return user


def request_for(user):
    return SimpleNamespace(user=user)


def test_ramadan_period_rejects_partial_pair():
    with pytest.raises(ValidationError):
        ProfilePatchSchema(ramadan_start_date=date(2026, 2, 18))


def test_ramadan_period_rejects_inverted_range():
    with pytest.raises(ValidationError):
        ProfilePatchSchema(
            ramadan_start_date=date(2026, 3, 20),
            ramadan_end_date=date(2026, 2, 18),
        )


def test_ramadan_period_persists_as_explicit_patient_context(patient):
    patch_profile(
        request_for(patient),
        ProfilePatchSchema(
            ramadan_start_date=date(2026, 2, 18),
            ramadan_end_date=date(2026, 3, 20),
        ),
    )
    profile = DiabetesProfile.objects.get(base_profile__patient=patient)
    assert profile.ramadan_start_date == date(2026, 2, 18)
    assert profile.ramadan_end_date == date(2026, 3, 20)


def test_ramadan_period_can_be_cleared_atomically(patient):
    profile = DiabetesProfile.objects.get(base_profile__patient=patient)
    profile.ramadan_start_date = date(2026, 2, 18)
    profile.ramadan_end_date = date(2026, 3, 20)
    profile.save(update_fields=["ramadan_start_date", "ramadan_end_date"])

    patch_profile(
        request_for(patient),
        ProfilePatchSchema(ramadan_start_date=None, ramadan_end_date=None),
    )
    profile.refresh_from_db()
    assert profile.ramadan_start_date is None
    assert profile.ramadan_end_date is None


def test_unrelated_profile_patch_never_infers_ramadan(patient):
    patch_profile(request_for(patient), ProfilePatchSchema(preferred_language="fr"))
    profile = DiabetesProfile.objects.get(base_profile__patient=patient)
    assert profile.ramadan_start_date is None
    assert profile.ramadan_end_date is None
