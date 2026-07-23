"""
Amina schema runway — new fields on BasePatientProfile/DiabetesProfile and LogEntry are in
place as nullable/defaulted columns. No behaviour change yet; these
tests lock defaults and uniqueness so future phases can rely on them.

AuditLog moved to the `core` app — see `core/tests/test_audit.py`.

P2 update: identity fields (firebase_uid, preferred_language, premium_valid_until)
now live on core.BasePatientProfile accessed via proxy properties on DiabetesProfile.
"""
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from core.models import BasePatientProfile
from diabetes.models import DiabetesProfile, LogEntry


class PatientProfileAminaFieldsTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='pw')
        self.base = BasePatientProfile.objects.create(
            patient=self.alice,
            date_of_birth=date(1985, 1, 1),
        )
        self.profile = DiabetesProfile.objects.create(
            base_profile=self.base,
            diabetes_type='type2',
            treatment_type='oral_meds',
        )

    def test_preferred_language_defaults_to_darija(self):
        self.assertEqual(self.profile.preferred_language, 'ar-MA')

    def test_preferred_language_accepts_darija(self):
        self.base.preferred_language = 'ar-MA'
        self.base.save()
        self.base.refresh_from_db()
        self.assertEqual(self.profile.preferred_language, 'ar-MA')

    def test_firebase_uid_is_nullable(self):
        self.assertIsNone(self.profile.firebase_uid)

    def test_firebase_uid_unique_across_profiles(self):
        self.base.firebase_uid = 'fb-alice-123'
        self.base.save()
        bob = User.objects.create_user(username='bob', password='pw')
        bob_base = BasePatientProfile(
            patient=bob,
            date_of_birth=date(1990, 1, 1),
            firebase_uid='fb-alice-123',
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                bob_base.save()

    def test_premium_valid_until_nullable(self):
        self.assertIsNone(self.profile.premium_valid_until)
        self.base.premium_valid_until = timezone.now() + timedelta(days=30)
        self.base.save()
        self.base.refresh_from_db()
        self.assertIsNotNone(self.profile.premium_valid_until)


class LogEntryAminaFieldsTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='pw')

    def test_source_defaults_to_manual(self):
        entry = LogEntry.objects.create(patient=self.alice, blood_sugar=Decimal('100'))
        self.assertEqual(entry.source, 'manual')

    def test_blood_sugar_constraint_enforced(self):
        """DB-level CheckConstraint rejects values outside [30, 600] mg/dL."""
        from django.db import IntegrityError, transaction
        with self.assertRaises((IntegrityError, Exception)):
            with transaction.atomic():
                LogEntry.objects.create(patient=self.alice, blood_sugar=Decimal('25'))

    def test_client_uuid_is_nullable_and_unique(self):
        # Two unset client_uuids are allowed.
        LogEntry.objects.create(patient=self.alice, blood_sugar=Decimal('100'))
        LogEntry.objects.create(patient=self.alice, blood_sugar=Decimal('110'))

        shared = uuid.uuid4()
        LogEntry.objects.create(patient=self.alice, blood_sugar=Decimal('120'), client_uuid=shared)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                LogEntry.objects.create(patient=self.alice, blood_sugar=Decimal('130'), client_uuid=shared)
