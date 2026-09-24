import json
from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from diabetes.models.entry import LogEntry
from diabetes.models.proactive_insight import ProactiveInsightState


class ProactiveSourceWriteFreshnessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.patient = User.objects.create_user(username="proactive-write-freshness")
        self.client.force_login(self.patient)
        self.now = timezone.now()

    def _post_log(self, *, days_ago: int, glucose: int, stressed: str = "yes"):
        return self.client.post(
            "/api/v1/logs",
            data=json.dumps(
                {
                    "logged_at": (self.now - timedelta(days=days_ago)).isoformat(),
                    "blood_sugar": glucose,
                    "stressed": stressed,
                    "source": "manual",
                    "client_uuid": str(uuid4()),
                }
            ),
            content_type="application/json",
        )

    def test_new_journal_writes_refresh_clinical_twin_before_read_only_preview(self):
        for day, glucose in enumerate((150, 160, 170)):
            response = self._post_log(days_ago=day, glucose=glucose)
            self.assertEqual(response.status_code, 200)

        preview = self.client.get("/api/v1/proactive-insights/preview/")

        self.assertEqual(preview.status_code, 200)
        payload = preview.json()
        self.assertEqual(payload["status"], "available")
        self.assertIsNotNone(payload["item"])
        self.assertEqual(payload["item"]["observation_key"], "context:stress")
        self.assertEqual(payload["item"]["observations"], 3)
        self.assertEqual(ProactiveInsightState.objects.count(), 0)

    def test_batch_insert_refreshes_clinical_twin_once(self):
        payload = [
            {
                "logged_at": (self.now - timedelta(days=day)).isoformat(),
                "blood_sugar": glucose,
                "stressed": "yes",
                "source": "manual",
                "client_uuid": str(uuid4()),
            }
            for day, glucose in enumerate((150, 160, 170))
        ]

        with patch(
            "diabetes.api.v1.logs._refresh_clinical_twin_after_source_write"
        ) as refresh:
            response = self.client.post(
                "/api/v1/logs/batch",
                data=json.dumps(payload),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["synced_ids"]), 3)
        refresh.assert_called_once_with(self.patient.id)

    def test_mixed_batch_reconciliation_includes_new_rows_in_fresh_twin(self):
        existing_uuid = uuid4()
        LogEntry.objects.create(
            patient=self.patient,
            logged_at=self.now,
            blood_sugar=120,
            stressed="",
            source="manual",
            client_uuid=existing_uuid,
        )
        payload = [
            {
                "logged_at": self.now.isoformat(),
                "blood_sugar": 150,
                "stressed": "yes",
                "source": "manual",
                "client_uuid": str(existing_uuid),
            },
            {
                "logged_at": (self.now - timedelta(days=1)).isoformat(),
                "blood_sugar": 160,
                "stressed": "yes",
                "source": "manual",
                "client_uuid": str(uuid4()),
            },
            {
                "logged_at": (self.now - timedelta(days=2)).isoformat(),
                "blood_sugar": 170,
                "stressed": "yes",
                "source": "manual",
                "client_uuid": str(uuid4()),
            },
        ]

        response = self.client.post(
            "/api/v1/logs/batch",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        preview = self.client.get("/api/v1/proactive-insights/preview/")
        self.assertEqual(preview.status_code, 200)
        item = preview.json()["item"]
        self.assertIsNotNone(item)
        self.assertEqual(item["observation_key"], "context:stress")
        self.assertEqual(item["observations"], 3)
        self.assertEqual(ProactiveInsightState.objects.count(), 0)

    def test_derived_refresh_failure_does_not_undo_authoritative_journal_write(self):
        with patch(
            "diabetes.api.v1.logs.refresh_personal_response_memory",
            side_effect=RuntimeError("synthetic refresh failure"),
        ):
            response = self._post_log(days_ago=0, glucose=145)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(LogEntry.objects.filter(patient=self.patient).count(), 1)
        self.assertEqual(ProactiveInsightState.objects.count(), 0)

    def test_demo_source_does_not_trigger_clinical_twin_refresh(self):
        with patch(
            "diabetes.api.v1.logs._refresh_clinical_twin_after_source_write"
        ) as refresh:
            response = self.client.post(
                "/api/v1/logs",
                data=json.dumps(
                    {
                        "logged_at": self.now.isoformat(),
                        "blood_sugar": 140,
                        "source": "demo",
                        "client_uuid": str(uuid4()),
                    }
                ),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        refresh.assert_not_called()
