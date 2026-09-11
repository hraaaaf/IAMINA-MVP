from __future__ import annotations

import io
import json
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from diabetes.models.cgm import CGMConnection, CGMReadingRecord
from diabetes.services.cgm_sync import CGMSyncResult


class LiveCGMQualificationCommandTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username="cgm-live-qualification-test",
            password="test-pass",
        )
        self.connection = CGMConnection.objects.create(
            patient=self.patient,
            source=CGMConnection.Source.LINX,
            base_url="https://nightscout.example.com",
            auth_type=CGMConnection.AuthType.BEARER,
            encrypted_credential="opaque-test-credential",
            enabled=True,
        )

    def _reading(self, *, minutes_ago: int, dedupe_key: str) -> None:
        CGMReadingRecord.objects.create(
            patient=self.patient,
            source=CGMConnection.Source.LINX,
            recorded_at=timezone.now() - timedelta(minutes=minutes_ago),
            glucose_mg_dl=120,
            trend="Flat",
            device="physical-bridge-test",
            dedupe_key=dedupe_key,
        )

    @patch("diabetes.services.cgm_live_qualification.sync_patient_cgm")
    def test_live_gate_emits_only_non_clinical_pass_metadata(self, sync_patient_cgm):
        self._reading(minutes_ago=1, dedupe_key="live-1")
        self._reading(minutes_ago=6, dedupe_key="live-2")
        sync_patient_cgm.return_value = CGMSyncResult(
            received=2,
            inserted=1,
            last_recorded_at=timezone.now(),
        )
        output = io.StringIO()

        call_command(
            "audit_cgm_live_bridge",
            patient_id=self.patient.id,
            source="linx",
            max_age_minutes=15,
            minimum_readings=2,
            confirm_authorized_non_patient_test_subject=True,
            confirm_physical_sensor=True,
            stdout=output,
        )

        payload = json.loads(output.getvalue())
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["source"], "linx")
        self.assertEqual(payload["provider_received"], 2)
        self.assertEqual(payload["fresh_persisted_readings"], 2)
        self.assertTrue(payload["physical_sensor_attested"])
        self.assertFalse(payload["contains_glucose_values"])
        self.assertFalse(payload["contains_credentials"])
        self.assertNotIn("glucose", output.getvalue().lower())
        self.assertNotIn("credential", output.getvalue().lower().replace("credentials", ""))
        self.assertNotIn(str(self.patient.id), output.getvalue())
        self.assertNotIn("nightscout.example.com", output.getvalue())
        sync_patient_cgm.assert_called_once_with(patient_id=self.patient.id)

    @patch("diabetes.services.cgm_live_qualification.sync_patient_cgm")
    def test_live_gate_fails_when_persisted_readings_are_stale(self, sync_patient_cgm):
        self._reading(minutes_ago=60, dedupe_key="stale-1")
        self._reading(minutes_ago=90, dedupe_key="stale-2")
        sync_patient_cgm.return_value = CGMSyncResult(
            received=2,
            inserted=0,
            last_recorded_at=timezone.now() - timedelta(hours=1),
        )

        with self.assertRaisesMessage(
            CommandError,
            "fresh_persisted_readings_below_minimum",
        ):
            call_command(
                "audit_cgm_live_bridge",
                patient_id=self.patient.id,
                source="linx",
                confirm_authorized_non_patient_test_subject=True,
                confirm_physical_sensor=True,
            )

    @patch("diabetes.services.cgm_live_qualification.sync_patient_cgm")
    def test_live_gate_requires_both_operator_attestations(self, sync_patient_cgm):
        with self.assertRaisesMessage(
            CommandError,
            "authorized_non_patient_test_subject_confirmation_required",
        ):
            call_command(
                "audit_cgm_live_bridge",
                patient_id=self.patient.id,
                source="linx",
            )
        sync_patient_cgm.assert_not_called()

        with self.assertRaisesMessage(CommandError, "physical_sensor_confirmation_required"):
            call_command(
                "audit_cgm_live_bridge",
                patient_id=self.patient.id,
                source="linx",
                confirm_authorized_non_patient_test_subject=True,
            )
        sync_patient_cgm.assert_not_called()

    @patch("diabetes.services.cgm_live_qualification.sync_patient_cgm")
    def test_live_gate_fails_closed_on_source_mismatch(self, sync_patient_cgm):
        with self.assertRaisesMessage(CommandError, "cgm_source_mismatch"):
            call_command(
                "audit_cgm_live_bridge",
                patient_id=self.patient.id,
                source="dexcom",
                confirm_authorized_non_patient_test_subject=True,
                confirm_physical_sensor=True,
            )
        sync_patient_cgm.assert_not_called()
