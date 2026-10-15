"""D18: synthetic patient isolation and opt-in historical weight facts."""

import datetime
import decimal
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from core import models
from core.models import patient_weight


class D18PatientWeightHistoryTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.a = User.objects.create_user(
            username="d18_owner_a", password="synthetic-d18-a"
        )
        self.b = User.objects.create_user(
            username="d18_owner_b", password="synthetic-d18-b"
        )
        self.now = datetime.datetime(2026, 10, 15, 8, tzinfo=datetime.timezone.utc)

    def test_no_declarations_are_invented_on_account_creation(self):
        for patient in (self.a, self.b):
            profile = models.BasePatientProfile.objects.create(patient=patient)
            self.assertIsNone(profile.birth_year)
            self.assertIsNone(profile.date_of_birth)
            self.assertIsNone(profile.gender)
            self.assertIsNone(profile.weight)
            self.assertFalse(
                models.PatientWeightObservation.objects.filter(patient=patient).exists()
            )

    def test_two_entries_preserve_both_timestamps_and_original_units(self):
        one, created = patient_weight.append_patient_weight(
            patient=self.a,
            value="71.25",
            unit="kg",
            measured_at=self.now,
            client_uuid=uuid.uuid4(),
        )
        self.assertTrue(created)
        two, created = patient_weight.append_patient_weight(
            patient=self.a,
            value="159.00",
            unit="lb",
            measured_at=self.now + datetime.timedelta(hours=2),
            client_uuid=uuid.uuid4(),
        )
        self.assertTrue(created)
        self.assertEqual(one.value, decimal.Decimal("71.25"))
        self.assertEqual(one.unit, "kg")
        self.assertEqual(one.weight_kg, decimal.Decimal("71.25"))
        self.assertEqual(two.weight_kg, decimal.Decimal("72.12"))
        self.assertEqual(two.provenance, "patient_declared")
        self.assertEqual(
            list(
                models.PatientWeightObservation.objects.filter(patient=self.a)
                .values_list("pk", flat=True)
            ), [two.pk, one.pk],
        )
        self.assertFalse(
            models.PatientWeightObservation.objects.filter(patient=self.b).exists()
        )
        # Do not forge a "current weight" from a historical record.
        # Creating a Django User alone does not manufacture a base profile.
        models.BasePatientProfile.objects.create(patient=self.a)
        self.assertIsNone(models.BasePatientProfile.objects.get(patient=self.a).weight)

    def test_idempotent_same_patient_uuid_and_conflict_fail_closed(self):
        uid = uuid.uuid4()
        one, created = patient_weight.append_patient_weight(
            patient=self.a, value="80", unit="kg",
            measured_at=self.now, client_uuid=uid,
        )
        self.assertTrue(created)
        repeated, created = patient_weight.append_patient_weight(
            patient=self.a, value="80", unit="kg",
            measured_at=self.now, client_uuid=uid,
        )
        self.assertFalse(created)
        self.assertEqual(repeated.pk, one.pk)
        with self.assertRaisesRegex(ValueError, "already belongs"):
            patient_weight.append_patient_weight(
                patient=self.a, value="85", unit="kg",
                measured_at=self.now, client_uuid=uid,
            )
        self.assertEqual(
            models.PatientWeightObservation.objects.get(pk=one.pk).value,
            decimal.Decimal("80"),
        )
        self.assertEqual(models.PatientWeightObservation.objects.count(), 1)

    def test_duplicate_uuid_is_isolated_by_authenticated_patient(self):
        uid = uuid.uuid4()
        for patient in (self.a, self.b):
            patient_weight.append_patient_weight(
                patient=patient, value="66", unit="kg",
                measured_at=self.now, client_uuid=uid,
            )
        self.assertEqual(models.PatientWeightObservation.objects.count(), 2)
        self.assertEqual(
            list(
                models.PatientWeightObservation.objects.filter(
                    patient=self.a
                ).values_list("patient_id", flat=True)
            ), [self.a.pk],
        )

    def test_invalid_weight_and_provenance_are_never_stored(self):
        for val, unit in (
            ("0", "kg"), ("-2", "kg"), ("NaN", "kg"),
            ("Infinity", "kg"), ("60.999", "kg"),
            ("61", "stone"),
        ):
            with self.subTest(val=val, unit=unit), self.assertRaises(ValueError):
                patient_weight.append_patient_weight(
                    patient=self.a, value=val, unit=unit,
                    measured_at=self.now, client_uuid=uuid.uuid4(),
                )
        with self.assertRaises(ValueError):
            patient_weight.append_patient_weight(
                patient=self.a, value="65", unit="kg",
                measured_at=self.now,
                client_uuid=uuid.uuid4(), provenance="device_inferred",
            )
        with self.assertRaises(ValueError):
            patient_weight.append_patient_weight(
                patient=self.a, value="65", unit="kg",
                measured_at=timezone.now() + datetime.timedelta(days=2),
                client_uuid=uuid.uuid4(),
            )
        self.assertFalse(models.PatientWeightObservation.objects.exists())

    def test_birth_year_is_optional_and_never_infers_exact_date(self):
        self.assertIsNone(patient_weight.validated_birth_year(None))
        self.assertEqual(
            patient_weight.validated_birth_year(2001, current_year=2026), 2001
        )
        for value in (True, 1890, 2027, "2001"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                patient_weight.validated_birth_year(value, current_year=2026)

    def test_deleting_one_owner_deletes_only_own_weight_history(self):
        for user in (self.a, self.b):
            patient_weight.append_patient_weight(
                patient=user, value="55", unit="kg",
                measured_at=self.now, client_uuid=uuid.uuid4(),
            )
        self.a.delete()
        self.assertEqual(models.PatientWeightObservation.objects.count(), 1)
        self.assertEqual(
            models.PatientWeightObservation.objects.get().patient_id, self.b.pk
        )

    def test_exact_normalization_is_deterministic_and_unit_aware(self):
        self.assertEqual(
            patient_weight.normalized_weight("1.00", unit="kg"),
            (decimal.Decimal("1.00"), decimal.Decimal("1.00")),
        )
        self.assertEqual(
            patient_weight.normalized_weight("100.00", unit="lb"),
            (decimal.Decimal("100.00"), decimal.Decimal("45.36")),
        )
