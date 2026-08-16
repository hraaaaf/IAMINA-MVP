from datetime import timedelta
from unittest.mock import patch

from cryptography.fernet import Fernet
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from diabetes.models.cgm import CGMConnection, CGMReadingRecord
from diabetes.services.cgm_credentials import (
    CGMCredentialError,
    decrypt_cgm_credential,
    encrypt_cgm_credential,
)
from diabetes.services.cgm_network import CGMNetworkPolicyError, validate_patient_cgm_base_url
from diabetes.services.cgm_sync import CGMSyncError, sync_patient_cgm
from integrations.cgm import CGMReading, CGMSource


class CGMCredentialTests(TestCase):
    @patch.dict("os.environ", {}, clear=True)
    def test_missing_key_fails_closed(self):
        with self.assertRaisesRegex(CGMCredentialError, "cgm_credential_key_unavailable"):
            encrypt_cgm_credential("secret")

    def test_round_trip_does_not_store_plaintext(self):
        key = Fernet.generate_key().decode("ascii")
        with patch.dict("os.environ", {"CGM_CREDENTIAL_KEY": key}, clear=False):
            ciphertext = encrypt_cgm_credential("private-token")
            self.assertNotIn("private-token", ciphertext)
            self.assertEqual(decrypt_cgm_credential(ciphertext), "private-token")


class CGMNetworkPolicyTests(TestCase):
    def test_plain_http_is_rejected(self):
        with self.assertRaisesRegex(CGMNetworkPolicyError, "cgm_bridge_https_required"):
            validate_patient_cgm_base_url("http://nightscout.example.com")

    def test_private_literal_is_rejected(self):
        with self.assertRaisesRegex(CGMNetworkPolicyError, "cgm_bridge_host_not_public"):
            validate_patient_cgm_base_url("https://127.0.0.1")

    @patch("diabetes.services.cgm_network.socket.getaddrinfo")
    def test_private_dns_resolution_is_rejected(self, getaddrinfo):
        getaddrinfo.return_value = [
            (2, 1, 6, "", ("10.0.0.5", 443)),
        ]
        with self.assertRaisesRegex(CGMNetworkPolicyError, "cgm_bridge_host_not_public"):
            validate_patient_cgm_base_url("https://nightscout.example.com")

    @patch("diabetes.services.cgm_network.socket.getaddrinfo")
    def test_public_https_target_is_accepted(self, getaddrinfo):
        getaddrinfo.return_value = [
            (2, 1, 6, "", ("93.184.216.34", 443)),
        ]
        self.assertEqual(
            validate_patient_cgm_base_url("https://nightscout.example.com/"),
            "https://nightscout.example.com",
        )


class CGMSyncTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="cgm-patient")
        self.other = User.objects.create_user(username="cgm-other")
        self.key = Fernet.generate_key().decode("ascii")
        with patch.dict("os.environ", {"CGM_CREDENTIAL_KEY": self.key}, clear=False):
            encrypted = encrypt_cgm_credential("transport-token")
        self.connection = CGMConnection.objects.create(
            patient=self.patient,
            source=CGMConnection.Source.DEXCOM,
            base_url="https://nightscout.example.test",
            auth_type=CGMConnection.AuthType.BEARER,
            encrypted_credential=encrypted,
        )

    @patch(
        "diabetes.services.cgm_sync.validate_patient_cgm_base_url",
        return_value="https://nightscout.example.test",
    )
    @patch("diabetes.services.cgm_sync.NightscoutCGMProvider.readings")
    def test_sync_is_patient_scoped_and_idempotent(self, readings, _network):
        now = timezone.now().replace(microsecond=0)
        readings.return_value = [
            CGMReading(
                timestamp=now - timedelta(minutes=5),
                glucose_mg_dl=123,
                source=CGMSource.DEXCOM,
                trend="Flat",
                device="Dexcom G7",
            )
        ]
        with patch.dict("os.environ", {"CGM_CREDENTIAL_KEY": self.key}, clear=False):
            first = sync_patient_cgm(patient_id=self.patient.id)
            second = sync_patient_cgm(patient_id=self.patient.id)

        self.assertEqual(first.received, 1)
        self.assertEqual(first.inserted, 1)
        self.assertEqual(second.inserted, 0)
        self.assertEqual(CGMReadingRecord.objects.filter(patient=self.patient).count(), 1)
        self.assertEqual(CGMReadingRecord.objects.filter(patient=self.other).count(), 0)
        row = CGMReadingRecord.objects.get(patient=self.patient)
        self.assertEqual(row.glucose_mg_dl, 123)
        self.assertEqual(row.source, "dexcom")

    def test_disabled_or_missing_connection_fails_closed(self):
        self.connection.enabled = False
        self.connection.save(update_fields=["enabled"])
        with self.assertRaisesRegex(CGMSyncError, "cgm_connection_unavailable"):
            sync_patient_cgm(patient_id=self.patient.id)

    @patch(
        "diabetes.services.cgm_sync.validate_patient_cgm_base_url",
        return_value="https://nightscout.example.test",
    )
    @patch("diabetes.services.cgm_sync.NightscoutCGMProvider.readings")
    def test_provider_failure_does_not_create_readings(self, readings, _network):
        from integrations.cgm.nightscout import CGMProviderError

        readings.side_effect = CGMProviderError("upstream detail must not escape")
        with patch.dict("os.environ", {"CGM_CREDENTIAL_KEY": self.key}, clear=False):
            with self.assertRaisesRegex(CGMSyncError, "provider_unavailable"):
                sync_patient_cgm(patient_id=self.patient.id)
        self.assertFalse(CGMReadingRecord.objects.filter(patient=self.patient).exists())
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.last_error_code, "provider_unavailable")

    @patch(
        "diabetes.services.cgm_sync.validate_patient_cgm_base_url",
        side_effect=CGMNetworkPolicyError("cgm_bridge_host_not_public"),
    )
    def test_sync_revalidates_network_target(self, _network):
        with patch.dict("os.environ", {"CGM_CREDENTIAL_KEY": self.key}, clear=False):
            with self.assertRaisesRegex(CGMSyncError, "cgm_bridge_host_not_public"):
                sync_patient_cgm(patient_id=self.patient.id)
        self.assertFalse(CGMReadingRecord.objects.filter(patient=self.patient).exists())
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.last_error_code, "cgm_bridge_host_not_public")
