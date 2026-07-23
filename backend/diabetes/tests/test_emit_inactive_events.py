"""
Tests for the emit_inactive_events management command.

Verifies:
  - INACTIVE_7D event emitted for patients with no recent log
  - No event emitted for active patients (log within 7 days)
  - Idempotence: second run on same day emits zero new events
  - stdout output message is correct
"""

from datetime import date, timedelta
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from core.models import BasePatientProfile
from core.observability import EVT_INACTIVE_7D
from core.observability.events import ObservabilityEvent
from diabetes.manifest import DIABETES_MANIFEST
from diabetes.models import DiabetesProfile, LogEntry


def _make_patient(username: str) -> tuple[User, DiabetesProfile]:
    """Create a minimal User + DiabetesProfile pair."""
    user = User.objects.create_user(username=username, password="testpass")
    base = BasePatientProfile.objects.create(
        patient=user,
        firebase_uid=f"firebase-{username}",
        date_of_birth=date(1985, 6, 15),
    )
    profile = DiabetesProfile.objects.create(
        base_profile=base,
        diabetes_type="type2",
        treatment_type="oral_meds",
    )
    return user, profile


class EmitInactiveEventsTest(TestCase):
    """Integration tests for the emit_inactive_events management command."""

    def test_emits_for_inactive_patient(self):
        """A patient with no LogEntry in the last 7 days receives one INACTIVE_7D event."""
        user, _ = _make_patient("inactive_user")

        call_command("emit_inactive_events", stdout=StringIO())

        self.assertEqual(
            ObservabilityEvent.objects.filter(
                event_type=EVT_INACTIVE_7D,
                patient_id=user.id,
            ).count(),
            1,
        )

    def test_does_not_emit_for_active_patient(self):
        """A patient with a recent acquisition ObservabilityEvent does NOT receive an INACTIVE_7D event."""
        user, _ = _make_patient("active_user")
        # Simulate activity via the acquisition event (P5: module-agnostic signal)
        ObservabilityEvent.objects.create(
            event_type=DIABETES_MANIFEST.acquisition_event,
            patient_id=user.id,
            timestamp=timezone.now(),
            props={},
        )

        call_command("emit_inactive_events", stdout=StringIO())

        self.assertEqual(
            ObservabilityEvent.objects.filter(
                event_type=EVT_INACTIVE_7D,
                patient_id=user.id,
            ).count(),
            0,
        )

    def test_idempotent_same_day(self):
        """Running the command twice on the same day emits only one event (idempotent)."""
        user, _ = _make_patient("idempotent_user")

        call_command("emit_inactive_events", stdout=StringIO())
        call_command("emit_inactive_events", stdout=StringIO())

        self.assertEqual(
            ObservabilityEvent.objects.filter(
                event_type=EVT_INACTIVE_7D,
                patient_id=user.id,
            ).count(),
            1,
        )

    def test_output_message(self):
        """The command prints a success message containing 'Emitted INACTIVE_7D'."""
        _make_patient("output_test_user")

        out = StringIO()
        call_command("emit_inactive_events", stdout=out)

        self.assertIn("Emitted INACTIVE_7D", out.getvalue())
