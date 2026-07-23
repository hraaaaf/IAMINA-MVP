"""
P2 Patient Split — Integration tests for BasePatientProfile + DiabetesProfile + PatientModule.

Verifies the P2 acceptance criteria:
  1. BasePatientProfile has identity fields
  2. DiabetesProfile extends BasePatientProfile via base_profile FK
  3. Creating User → BasePatientProfile → DiabetesProfile round-trip works
  4. PatientModule unique constraint enforced
  5. Deleting BasePatientProfile cascades to DiabetesProfile
  6. firebase_uid lookup via BasePatientProfile returns correct user
"""
from datetime import date

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from core.models import BasePatientProfile, PatientModule
from diabetes.models import DiabetesProfile


class BasePatientProfileTests(TestCase):
    """BasePatientProfile model — identity fields and constraints."""

    def setUp(self):
        self.user = User.objects.create_user(username="p2_alice", email="p2alice@test.com")
        self.base = BasePatientProfile.objects.create(
            patient=self.user,
            firebase_uid="p2-uid-alice",
            date_of_birth=date(1990, 5, 15),
        )

    def test_base_profile_has_identity_fields(self):
        """BasePatientProfile has all chassis identity fields without fabricated facts."""
        self.assertEqual(self.base.patient, self.user)
        self.assertEqual(self.base.firebase_uid, "p2-uid-alice")
        self.assertEqual(self.base.preferred_language, "ar-MA")
        self.assertIsNone(self.base.ai_consent_given_at)
        self.assertIsNone(self.base.premium_valid_until)
        self.assertIsNone(self.base.gender)
        self.assertEqual(self.base.date_of_birth, date(1990, 5, 15))
        self.assertIsNone(self.base.weight)
        self.assertIsNone(self.base.height)
        self.assertIsNotNone(self.base.created_at)
        self.assertIsNotNone(self.base.updated_at)

    def test_firebase_uid_lookup_returns_correct_user(self):
        """Acceptance criteria 6: firebase_uid lookup returns correct user."""
        found = BasePatientProfile.objects.get(firebase_uid="p2-uid-alice")
        self.assertEqual(found.patient, self.user)

    def test_firebase_uid_unique_constraint(self):
        """firebase_uid must be unique across all BasePatientProfile rows."""
        other_user = User.objects.create_user(username="p2_bob")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                BasePatientProfile.objects.create(
                    patient=other_user,
                    firebase_uid="p2-uid-alice",
                    date_of_birth=date(1988, 1, 1),
                )

    def test_user_base_profile_reverse_accessor(self):
        """User.base_profile reverse accessor works."""
        self.assertEqual(self.user.base_profile, self.base)


class DiabetesProfileTests(TestCase):
    """DiabetesProfile model — diabetes-specific fields + base_profile FK."""

    def setUp(self):
        self.user = User.objects.create_user(username="p2_carol")
        self.base = BasePatientProfile.objects.create(
            patient=self.user,
            date_of_birth=date(1985, 3, 20),
        )
        self.profile = DiabetesProfile.objects.create(
            base_profile=self.base,
            diabetes_type="type2",
            treatment_type="oral_meds",
        )

    def test_diabetes_profile_has_diabetes_fields(self):
        """DiabetesProfile has all diabetes-specific fields."""
        self.assertEqual(self.profile.diabetes_type, "type2")
        self.assertEqual(self.profile.treatment_type, "oral_meds")
        self.assertEqual(self.profile.target_range_low, 70)
        self.assertEqual(self.profile.target_range_high, 180)
        self.assertEqual(self.profile.unit_preference, "mg_dl")

    def test_diabetes_profile_base_profile_fk(self):
        """DiabetesProfile.base_profile links to BasePatientProfile."""
        self.assertEqual(self.profile.base_profile, self.base)

    def test_user_to_diabetes_profile_traversal(self):
        """User → base_profile → diabetes_profile traversal works."""
        dp = self.user.base_profile.diabetes_profile
        self.assertEqual(dp, self.profile)

    def test_diabetes_profile_proxy_properties(self):
        """DiabetesProfile proxy properties delegate to base_profile."""
        self.assertEqual(self.profile.patient, self.user)
        self.assertEqual(self.profile.patient_id, self.user.id)
        self.assertEqual(self.profile.preferred_language, "ar-MA")
        self.assertIsNone(self.profile.firebase_uid)
        self.assertEqual(self.profile.date_of_birth, date(1985, 3, 20))


class P2RoundTripTests(TestCase):
    """End-to-end round-trip: User → BasePatientProfile → DiabetesProfile."""

    def test_full_creation_round_trip(self):
        """Acceptance criteria 3: creating User → BasePatientProfile → DiabetesProfile."""
        user = User.objects.create_user(username="p2_roundtrip", email="rt@test.com")
        base = BasePatientProfile.objects.create(
            patient=user,
            firebase_uid="rt-uid-001",
            date_of_birth=date(1992, 7, 10),
            preferred_language="fr",
        )
        DiabetesProfile.objects.create(
            base_profile=base,
            diabetes_type="type1",
            treatment_type="insulin_pump",
        )
        fetched_base = BasePatientProfile.objects.get(firebase_uid="rt-uid-001")
        self.assertEqual(fetched_base.patient, user)
        self.assertEqual(fetched_base.preferred_language, "fr")
        fetched_profile = fetched_base.diabetes_profile
        self.assertEqual(fetched_profile.diabetes_type, "type1")
        self.assertEqual(fetched_profile.base_profile, fetched_base)

    def test_cascade_delete_base_removes_diabetes_profile(self):
        """Acceptance criteria 5: deleting BasePatientProfile cascades to DiabetesProfile."""
        user = User.objects.create_user(username="p2_cascade")
        base = BasePatientProfile.objects.create(
            patient=user,
            date_of_birth=date(1988, 2, 14),
        )
        DiabetesProfile.objects.create(
            base_profile=base,
            diabetes_type="type2",
            treatment_type="oral_meds",
        )
        base_id = base.pk
        profile_count_before = DiabetesProfile.objects.filter(base_profile_id=base_id).count()
        self.assertEqual(profile_count_before, 1)

        base.delete()

        profile_count_after = DiabetesProfile.objects.filter(base_profile_id=base_id).count()
        self.assertEqual(profile_count_after, 0)


class PatientModuleTests(TestCase):
    """PatientModule junction table — unique constraint and activation tracking."""

    def setUp(self):
        self.user = User.objects.create_user(username="p2_module_user")
        self.base = BasePatientProfile.objects.create(
            patient=self.user,
            date_of_birth=date(1980, 1, 1),
        )

    def test_module_creation(self):
        """PatientModule can be created with patient + module_name."""
        mod = PatientModule.objects.create(
            patient=self.base,
            module_name="diabetes",
        )
        self.assertTrue(mod.is_active)
        self.assertIsNotNone(mod.activated_at)
        self.assertEqual(mod.module_name, "diabetes")

    def test_unique_constraint_enforced(self):
        """Acceptance criteria 4: duplicate (patient, module_name) is rejected."""
        PatientModule.objects.create(patient=self.base, module_name="diabetes")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PatientModule.objects.create(patient=self.base, module_name="diabetes")

    def test_multiple_modules_per_patient(self):
        """One patient can have multiple distinct module activations."""
        PatientModule.objects.create(patient=self.base, module_name="diabetes")
        PatientModule.objects.create(patient=self.base, module_name="hypertension")
        self.assertEqual(PatientModule.objects.filter(patient=self.base).count(), 2)

    def test_table_in_fresh_migration(self):
        """core_patientmodule table is accessible (migration applied)."""
        count = PatientModule.objects.count()
        self.assertGreaterEqual(count, 0)


class DiabetesTablePreservationTest(TestCase):
    """Critical safety check: diabetes_patientprofile table was NOT dropped."""

    def test_diabetes_patientprofile_table_exists(self):
        """The preserved table must exist on every supported database backend."""
        from django.db import connection

        table_names = connection.introspection.table_names()
        self.assertIn(
            "diabetes_patientprofile",
            table_names,
            "diabetes_patientprofile table was dropped — CRITICAL ERROR",
        )
