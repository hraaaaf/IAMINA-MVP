"""D7: synthetic patient-owned declarative multi-treatment contract."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.test import TestCase
from pydantic import ValidationError

from core.models import BasePatientProfile
from diabetes.api.v1.profile import (
    PatientTreatmentDeclarationPatch,
    ProfilePatchSchema,
    get_profile,
    patch_profile,
)
from diabetes.api.v1.schemas import PatientProfileSchema
from diabetes.models import DiabetesProfile


def declaration(state="declared", codes=None):
    return PatientTreatmentDeclarationPatch(
        version=1,
        state=state,
        codes=codes if codes is not None else ["insulin", "lifestyle"],
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"version": 2, "state": "declared", "codes": ["insulin"]},
        {"version": 1, "state": "declared", "codes": []},
        {"version": 1, "state": "unsure", "codes": ["insulin"]},
        {"version": 1, "state": "none_declared", "codes": ["lifestyle"]},
        {"version": 1, "state": "declared", "codes": ["insulin", "insulin"]},
        {"version": 1, "state": "declared", "codes": ["unknown_code"]},
        {"version": 1, "state": "declared", "codes": ["insulin"], "patient_id": 999},
    ],
)
def test_d7_invalid_declarations_are_not_accepted(payload):
    with pytest.raises(ValidationError):
        PatientTreatmentDeclarationPatch.model_validate(payload)


def test_d7_nullable_patch_is_not_silent_deletion():
    with pytest.raises(ValidationError):
        ProfilePatchSchema.model_validate({"treatment_declaration": None})


class DeclarativeTreatmentPersistenceTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user(username="synthetic-d7-a")
        self.b = User.objects.create_user(username="synthetic-d7-b")
        for user in (self.a, self.b):
            base = BasePatientProfile.objects.create(patient=user)
            DiabetesProfile.objects.create(
                base_profile=base,
                diabetes_type="type2",
                treatment_type="oral_meds",
            )

    @staticmethod
    def _declaration_request(user, revision="none"):
        return SimpleNamespace(
            user=user,
            headers={"X-Iamina-Treatment-Expected-Updated-At": revision},
        )

    @patch("diabetes.services.session_cache.invalidate")
    def test_multiselect_round_trip_does_not_overwrite_legacy_or_other_patient(
        self, _invalidate
    ):
        a = self._declaration_request(self.a)
        b = SimpleNamespace(user=self.b)
        patch_profile(
            a,
            ProfilePatchSchema(
                treatment_declaration=declaration(
                    codes=["insulin", "oral_meds", "lifestyle"]
                )
            ),
        )
        a_record = DiabetesProfile.objects.get(base_profile__patient=self.a)
        b_record = DiabetesProfile.objects.get(base_profile__patient=self.b)
        self.assertEqual(a_record.treatment_declarations, [
            "insulin", "oral_meds", "lifestyle"
        ])
        self.assertEqual(a_record.treatment_declaration_state, "declared")
        self.assertEqual(a_record.treatment_declaration_source, "patient_declared")
        self.assertEqual(a_record.treatment_declaration_version, 1)
        self.assertIsNotNone(a_record.treatment_declaration_updated_at)
        self.assertEqual(a_record.treatment_type, "oral_meds")
        self.assertEqual(b_record.treatment_declarations, [])
        self.assertEqual(b_record.treatment_declaration_state, "not_answered")
        self.assertIsNone(b_record.treatment_declaration_source)
        response = PatientProfileSchema.model_validate(
            get_profile(a), from_attributes=True
        )
        self.assertEqual(response.treatment_declarations, [
            "insulin", "oral_meds", "lifestyle"
        ])
        self.assertEqual(get_profile(b).treatment_declarations, [])

    @patch("diabetes.services.session_cache.invalidate")
    def test_explicit_unsure_and_none_remain_distinct_from_not_answered(
        self, _invalidate
    ):
        a = self._declaration_request(self.a)
        patch_profile(
            a,
            ProfilePatchSchema(
                treatment_declaration=declaration(state="unsure", codes=[])
            ),
        )
        record = DiabetesProfile.objects.get(base_profile__patient=self.a)
        self.assertEqual(record.treatment_declarations, [])
        self.assertEqual(record.treatment_declaration_state, "unsure")
        a.headers["X-Iamina-Treatment-Expected-Updated-At"] = (
            record.treatment_declaration_updated_at.isoformat()
        )
        patch_profile(
            a,
            ProfilePatchSchema(
                treatment_declaration=declaration(state="none_declared", codes=[])
            ),
        )
        record.refresh_from_db()
        self.assertEqual(record.treatment_declaration_state, "none_declared")
        a.headers["X-Iamina-Treatment-Expected-Updated-At"] = (
            record.treatment_declaration_updated_at.isoformat()
        )
        patch_profile(
            a,
            ProfilePatchSchema(
                treatment_declaration=declaration(state="not_answered", codes=[])
            ),
        )
        record.refresh_from_db()
        self.assertEqual(record.treatment_declaration_state, "not_answered")

    @patch("diabetes.services.session_cache.invalidate")
    def test_declaration_change_keeps_clinician_target_authority_unmodified(
        self, _invalidate
    ):
        patient = DiabetesProfile.objects.get(base_profile__patient=self.a)
        patient.target_range_provenance = "clinician_confirmed"
        patient.target_population_context = "individualized"
        patient.target_time_in_range_goal_pct = 75.0
        patient.save(
            update_fields=[
                "target_range_provenance",
                "target_population_context",
                "target_time_in_range_goal_pct",
            ]
        )
        patch_profile(
            self._declaration_request(self.a),
            ProfilePatchSchema(
                treatment_declaration=declaration(codes=["oral_meds"])
            ),
        )
        patient.refresh_from_db()
        self.assertEqual(patient.target_range_provenance, "clinician_confirmed")
        self.assertEqual(patient.target_population_context, "individualized")
        self.assertEqual(patient.target_time_in_range_goal_pct, 75.0)

    def test_unrelated_patch_does_not_create_patient_declaration(self):
        patch_profile(
            SimpleNamespace(user=self.a),
            ProfilePatchSchema(preferred_language="fr"),
        )
        patient = DiabetesProfile.objects.get(base_profile__patient=self.a)
        self.assertEqual(patient.treatment_declaration_state, "not_answered")
        self.assertEqual(patient.treatment_declarations, [])
        self.assertIsNone(patient.treatment_declaration_source)
