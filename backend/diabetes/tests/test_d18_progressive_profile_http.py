"""D18 — real bearer HTTP tests for minimal demographics and dated weights.

All people, tokens and clinical values in this file are synthetic.
No live patient data, treatment adaptation or inferred date of birth.
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch as mock_patch
from uuid import uuid4

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone
from ninja.security import HttpBearer

from core.models import BasePatientProfile
from core.models.patient_weight import PatientWeightObservation
from core.native_auth import issue_native_token
from diabetes.api.v1.security import HybridBearerAuth
from diabetes.models import DiabetesProfile


class D18PatientDemographicsAndWeightHttpTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user(username="d18-owner-a", password="synthetic")
        self.b = User.objects.create_user(username="d18-owner-b", password="synthetic")
        for user in (self.a, self.b):
            base = BasePatientProfile.objects.create(patient=user)
            DiabetesProfile.objects.create(base_profile=base)
        self.token_a = issue_native_token(self.a)
        self.token_b = issue_native_token(self.b)
        self.client = Client()

    def _call(self, method, path, token=None, payload=None):
        # Restore the real Ninja bearer path, not conftest's session shortcut.
        with mock_patch.object(HybridBearerAuth, "__call__", HttpBearer.__call__):
            kw = {"headers": {"Authorization": f"Bearer {token}"}} if token else {}
            if payload is not None:
                kw["data"] = json.dumps(payload)
                kw["content_type"] = "application/json"
            return getattr(self.client, method)(path, **kw)

    def _weight(self, token, *, value="70.50", unit="kg", at=None, uid=None):
        date = at or timezone.now().replace(microsecond=0)
        payload = {
            "client_uuid": str(uid or uuid4()),
            "value": value,
            "unit": unit,
            "measured_at": date.isoformat(),
            "provenance": "patient_declared",
        }
        return self._call(
            "post", "/api/v1/profile/weight-observations", token, payload
        ), payload

    def test_new_patient_all_demographics_unanswered_and_weight_history_empty(self):
        response = self._call("get", "/api/v1/profile", self.token_a)
        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        for field in ("birth_year", "gender_identity", "date_of_birth", "weight"):
            self.assertIsNone(body[field])
        history = self._call(
            "get", "/api/v1/profile/weight-observations", self.token_a
        )
        self.assertEqual(history.status_code, 200, history.content)
        self.assertEqual(history.json(), [])

    def test_optional_birth_year_and_gender_are_declarative_and_clearable(self):
        response = self._call("patch", "/api/v1/profile", self.token_a, {
            "birth_year": 1994,
            "gender_identity": "non_binary",
        })
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["birth_year"], 1994)
        self.assertEqual(response.json()["gender_identity"], "non_binary")
        self.assertIsNone(response.json()["date_of_birth"])
        self.assertIsNone(self._call("get", "/api/v1/profile", self.token_b).json()["birth_year"])

        cleared = self._call("patch", "/api/v1/profile", self.token_a, {
            "birth_year": None, "gender_identity": None,
        })
        self.assertEqual(cleared.status_code, 200, cleared.content)
        self.assertIsNone(cleared.json()["birth_year"])
        self.assertIsNone(cleared.json()["gender_identity"])
        self.assertFalse(PatientWeightObservation.objects.exists())

    def test_birth_year_and_gender_validation_is_non_mutating(self):
        original = self._call("get", "/api/v1/profile", self.token_a).json()
        bad_values = (
            {"birth_year": 1899},
            {"birth_year": timezone.now().year + 1},
            {"birth_year": "not-a-year"},
            {"gender_identity": "biology_inferred_from_weight"},
        )
        for payload in bad_values:
            response = self._call("patch", "/api/v1/profile", self.token_a, payload)
            self.assertEqual(response.status_code, 422, (payload, response.content))
        self.assertEqual(
            self._call("get", "/api/v1/profile", self.token_a).json(),
            original,
        )

    def test_multiple_measurements_append_and_other_patient_sees_none(self):
        first_date = timezone.now().replace(microsecond=0) - timedelta(days=3)
        second_date = first_date + timedelta(days=1)
        first, _ = self._weight(self.token_a, value="71.20", at=first_date)
        second, _ = self._weight(
            self.token_a, value="155.00", unit="lb", at=second_date
        )
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(second.status_code, 201, second.content)
        self.assertEqual(Decimal(str(second.json()["weight_kg"])), Decimal("70.31"))
        history = self._call(
            "get", "/api/v1/profile/weight-observations", self.token_a
        )
        self.assertEqual(history.status_code, 200, history.content)
        self.assertEqual(len(history.json()), 2)
        self.assertEqual(history.json()[0]["id"], second.json()["id"])
        self.assertEqual(history.json()[1]["id"], first.json()["id"])
        self.assertEqual(
            self._call(
                "get", "/api/v1/profile/weight-observations", self.token_b
            ).json(),
            [],
        )
        self.assertEqual(
            list(PatientWeightObservation.objects.values_list("patient_id", flat=True)),
            [self.a.pk, self.a.pk],
        )
        # No speculative automatic mirroring to legacy undated profile weight.
        self.assertIsNone(BasePatientProfile.objects.get(patient=self.a).weight)

    def test_idempotent_retry_replays_and_changed_uuid_payload_conflicts(self):
        uid = uuid4()
        stamp = timezone.now().replace(microsecond=0)
        first, payload = self._weight(self.token_a, at=stamp, uid=uid)
        self.assertEqual(first.status_code, 201, first.content)
        again = self._call(
            "post", "/api/v1/profile/weight-observations", self.token_a, payload
        )
        self.assertEqual(again.status_code, 200, again.content)
        self.assertEqual(first.json()["id"], again.json()["id"])
        changed = {**payload, "value": "74.00"}
        conflict = self._call(
            "post", "/api/v1/profile/weight-observations", self.token_a, changed
        )
        self.assertEqual(conflict.status_code, 409, conflict.content)
        self.assertEqual(PatientWeightObservation.objects.count(), 1)
        self.assertEqual(
            PatientWeightObservation.objects.get(patient=self.a).value,
            Decimal("70.50"),
        )
        # Same UUID in another patient's vault is a distinct owner-scoped record.
        other = self._call(
            "post", "/api/v1/profile/weight-observations", self.token_b, changed
        )
        self.assertEqual(other.status_code, 201, other.content)
        self.assertEqual(PatientWeightObservation.objects.count(), 2)

    def test_invalid_weight_and_undated_legacy_patch_do_not_mutate_history(self):
        future = timezone.now() + timedelta(days=1)
        invalid = (
            {"value": "NaN"},
            {"value": "-10"},
            {"value": "0"},
            {"value": "70.123"},
            {"unit": "stones"},
            {"measured_at": future.isoformat()},
            {"provenance": "inferred_by_ai"},
        )
        valid_stamp = timezone.now().replace(microsecond=0).isoformat()
        for partial in invalid:
            payload = {
                "client_uuid": str(uuid4()),
                "value": "70",
                "unit": "kg",
                "measured_at": valid_stamp,
                "provenance": "patient_declared",
                **partial,
            }
            response = self._call(
                "post", "/api/v1/profile/weight-observations", self.token_a, payload
            )
            self.assertEqual(response.status_code, 422, (partial, response.content))

        # Legacy singleton writes cannot overwrite unversioned history.
        old_patch = self._call(
            "patch", "/api/v1/profile", self.token_a, {"weight": 75}
        )
        self.assertEqual(old_patch.status_code, 422, old_patch.content)
        self.assertFalse(PatientWeightObservation.objects.exists())
        self.assertIsNone(BasePatientProfile.objects.get(patient=self.a).weight)

    def test_unauthenticated_weight_endpoints_and_bad_limits_fail_closed(self):
        for method in ("get", "post"):
            response = self._call(
                method, "/api/v1/profile/weight-observations",
                payload={"value": "60"} if method == "post" else None,
            )
            self.assertIn(response.status_code, (401, 403))
        for query in ("?limit=0", "?limit=201"):
            bad = self._call(
                "get", "/api/v1/profile/weight-observations" + query, self.token_a
            )
            self.assertEqual(bad.status_code, 422, bad.content)
