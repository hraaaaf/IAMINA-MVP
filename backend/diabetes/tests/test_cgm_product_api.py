import hashlib
from types import SimpleNamespace
from unittest.mock import patch

from cryptography.fernet import Fernet
from django.contrib.auth.models import User
from django.test import TestCase

from diabetes.api.v1.cgm import (
    CGMConnectionInput,
    delete_cgm_connection,
    get_cgm_connection,
    put_cgm_connection,
)
from diabetes.models.cgm import CGMConnection, CGMReadingRecord
from diabetes.services.cgm_credentials import decrypt_cgm_credential


class CGMProductApiTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="cgm-api-patient")
        self.request = SimpleNamespace(user=self.patient)
        self.key = Fernet.generate_key().decode("ascii")

    @patch(
        "diabetes.api.v1.cgm.validate_patient_cgm_base_url",
        return_value="https://nightscout.example.com",
    )
    def test_bearer_connection_stores_only_encrypted_secret(self, _network):
        payload = CGMConnectionInput(
            source="dexcom",
            base_url="https://nightscout.example.com/",
            auth_type="bearer",
            credential="private-bearer-token",
        )
        with patch.dict("os.environ", {"CGM_CREDENTIAL_KEY": self.key}, clear=False):
            response = put_cgm_connection(self.request, payload)
            connection = CGMConnection.objects.get(patient=self.patient)
            stored = decrypt_cgm_credential(connection.encrypted_credential)

        self.assertEqual(stored, "private-bearer-token")
        self.assertNotIn("private-bearer-token", connection.encrypted_credential)
        self.assertTrue(response["credential_set"])
        self.assertNotIn("credential", response)
        self.assertEqual(response["base_url"], "https://nightscout.example.com")

    @patch(
        "diabetes.api.v1.cgm.validate_patient_cgm_base_url",
        return_value="https://nightscout.example.com",
    )
    def test_api_secret_is_protocol_hashed_before_encrypted_storage(self, _network):
        payload = CGMConnectionInput(
            source="libre",
            base_url="https://nightscout.example.com",
            auth_type="api_secret",
            credential="raw-nightscout-secret",
        )
        with patch.dict("os.environ", {"CGM_CREDENTIAL_KEY": self.key}, clear=False):
            put_cgm_connection(self.request, payload)
            connection = CGMConnection.objects.get(patient=self.patient)
            stored = decrypt_cgm_credential(connection.encrypted_credential)

        expected = hashlib.sha1(
            b"raw-nightscout-secret", usedforsecurity=False
        ).hexdigest()
        self.assertEqual(stored, expected)
        self.assertNotEqual(stored, "raw-nightscout-secret")

    @patch(
        "diabetes.api.v1.cgm.validate_patient_cgm_base_url",
        return_value="https://nightscout.example.com",
    )
    def test_reconfiguration_replaces_single_active_source(self, _network):
        with patch.dict("os.environ", {"CGM_CREDENTIAL_KEY": self.key}, clear=False):
            put_cgm_connection(
                self.request,
                CGMConnectionInput(
                    source="dexcom",
                    base_url="https://nightscout.example.com",
                    auth_type="bearer",
                    credential="one",
                ),
            )
            put_cgm_connection(
                self.request,
                CGMConnectionInput(
                    source="linx",
                    base_url="https://nightscout.example.com",
                    auth_type="bearer",
                    credential="two",
                ),
            )

        self.assertEqual(CGMConnection.objects.filter(patient=self.patient).count(), 1)
        self.assertEqual(CGMConnection.objects.get(patient=self.patient).source, "linx")

    @patch(
        "diabetes.api.v1.cgm.validate_patient_cgm_base_url",
        return_value="https://nightscout.example.com",
    )
    def test_disconnect_removes_secret_but_preserves_recorded_readings(self, _network):
        with patch.dict("os.environ", {"CGM_CREDENTIAL_KEY": self.key}, clear=False):
            put_cgm_connection(
                self.request,
                CGMConnectionInput(
                    source="dexcom",
                    base_url="https://nightscout.example.com",
                    auth_type="bearer",
                    credential="secret",
                ),
            )
        CGMReadingRecord.objects.create(
            patient=self.patient,
            source="dexcom",
            recorded_at="2026-08-16T12:00:00Z",
            glucose_mg_dl=120,
            dedupe_key="x" * 64,
        )

        status, body = delete_cgm_connection(self.request)
        self.assertEqual(status, 204)
        self.assertIsNone(body)
        self.assertFalse(CGMConnection.objects.filter(patient=self.patient).exists())
        self.assertEqual(CGMReadingRecord.objects.filter(patient=self.patient).count(), 1)
        self.assertFalse(get_cgm_connection(self.request)["connected"])
