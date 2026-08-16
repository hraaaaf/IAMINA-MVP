import json
from datetime import timedelta
from unittest.mock import patch

from cryptography.fernet import Fernet
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from integrations.cgm import CGMReading, CGMSource


class CGMProductE2ETests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="cgm-e2e-patient", password="test-pass")
        self.client = Client()
        self.client.force_login(self.patient)
        self.key = Fernet.generate_key().decode("ascii")

    @patch(
        "diabetes.services.cgm_sync.validate_patient_cgm_base_url",
        return_value="https://nightscout.example.com",
    )
    @patch("diabetes.services.cgm_sync.NightscoutCGMProvider.readings")
    @patch(
        "diabetes.api.v1.cgm.validate_patient_cgm_base_url",
        return_value="https://nightscout.example.com",
    )
    def test_configure_sync_persist_and_read_over_authenticated_http(
        self,
        _configure_network,
        readings,
        _sync_network,
    ):
        now = timezone.now().replace(microsecond=0)
        readings.return_value = [
            CGMReading(
                timestamp=now - timedelta(minutes=3),
                glucose_mg_dl=127,
                source=CGMSource.LINX,
                trend="Flat",
                device="LinX",
            )
        ]

        with patch.dict("os.environ", {"CGM_CREDENTIAL_KEY": self.key}, clear=False):
            configured = self.client.put(
                "/api/v1/cgm/connection",
                data=json.dumps(
                    {
                        "source": "linx",
                        "base_url": "https://nightscout.example.com",
                        "auth_type": "bearer",
                        "credential": "test-transport-token",
                    }
                ),
                content_type="application/json",
            )
            self.assertEqual(configured.status_code, 200)
            configured_payload = configured.json()
            self.assertTrue(configured_payload["connected"])
            self.assertEqual(configured_payload["source"], "linx")
            self.assertTrue(configured_payload["credential_set"])
            self.assertNotIn("credential", configured_payload)

            synced = self.client.post("/api/v1/cgm/sync")
            self.assertEqual(synced.status_code, 200)
            self.assertEqual(synced.json()["inserted"], 1)

            fetched = self.client.get("/api/v1/cgm/readings?hours=24")
            self.assertEqual(fetched.status_code, 200)
            payload = fetched.json()
            self.assertEqual(len(payload), 1)
            self.assertEqual(payload[0]["glucose_mg_dl"], 127)
            self.assertEqual(payload[0]["source"], "linx")
            self.assertEqual(payload[0]["device"], "LinX")

            disconnected = self.client.delete("/api/v1/cgm/connection")
            self.assertEqual(disconnected.status_code, 204)

            connection = self.client.get("/api/v1/cgm/connection")
            self.assertEqual(connection.status_code, 200)
            self.assertFalse(connection.json()["connected"])

            historical = self.client.get("/api/v1/cgm/readings?hours=24")
            self.assertEqual(historical.status_code, 200)
            self.assertEqual(len(historical.json()), 1)
