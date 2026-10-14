"""D7 true loopback TCP HTTP proof with independent synthetic client sessions.

Not a Flutter UI or two physical devices. No Vercel, remote DB, or real patients.
"""

import json
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import LiveServerTestCase
from ninja.security import HttpBearer

from core.models import BasePatientProfile
from core.native_auth import issue_native_token
from diabetes.api.v1.security import HybridBearerAuth
from diabetes.models import DiabetesProfile


class D7LiveHttpTwoClientCAS(LiveServerTestCase):
    def setUp(self):
        self.a = User.objects.create_user(username="e2e-d7-synthetic-a")
        self.b = User.objects.create_user(username="e2e-d7-synthetic-b")
        for user in (self.a, self.b):
            base = BasePatientProfile.objects.create(patient=user)
            DiabetesProfile.objects.create(base_profile=base)
        self.token_a = issue_native_token(self.a)
        self.token_b = issue_native_token(self.b)
        # Different cookie stores and HTTP clients; same ephemeral TCP backend.
        self.device_1 = build_opener(ProxyHandler({}))
        self.device_2 = build_opener(ProxyHandler({}))

    def _http(self, client, method, bearer=None, *, declaration=None, revision=None):
        headers = {"Accept": "application/json"}
        if bearer is not None:
            headers["Authorization"] = f"Bearer {bearer}"
        if revision is not None:
            headers["X-Iamina-Treatment-Expected-Updated-At"] = revision
        body = None
        if declaration is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps({"treatment_declaration": declaration}).encode("utf-8")
        request = Request(
            self.live_server_url + "/api/v1/profile",
            data=body,
            headers=headers,
            method=method,
        )
        # A global pytest test shim accepts Django sessions and rejects
        # native tokens; restore production Django-Ninja bearer parsing only
        # around this real TCP transaction. Never bypass token validation.
        with patch.object(HybridBearerAuth, "__call__", HttpBearer.__call__):
            try:
                with client.open(request, timeout=12) as response:
                    return response.status, json.loads(response.read())
            except HTTPError as exc:
                return exc.code, json.loads(exc.read())

    @staticmethod
    def _declaration(codes, state="declared"):
        return {"version": 1, "state": state, "codes": codes}

    def test_live_a_b_a_two_http_clients_409_and_no_silent_clobber(self):
        # Device 1 authenticates A, Device 2 authenticates B; neither shares
        # a cookie, on-disk state, bearer, or account binding.
        code, a_initial = self._http(self.device_1, "GET", self.token_a)
        self.assertEqual(code, 200)
        self.assertEqual(a_initial["treatment_declarations"], [])
        code, b_initial = self._http(self.device_2, "GET", self.token_b)
        self.assertEqual(code, 200)
        self.assertEqual(b_initial["treatment_declarations"], [])

        code, a_saved = self._http(
            self.device_1,
            "PATCH", self.token_a,
            declaration=self._declaration(["lifestyle"]),
            revision="none",
        )
        self.assertEqual(code, 200)
        expected = a_saved["treatment_declaration_updated_at"]
        self.assertIsNotNone(expected)

        # Two separate TCP clients authenticated as A see the same server
        # snapshot, unlike purely local browser-context isolation.
        code, a_second_device = self._http(self.device_2, "GET", self.token_a)
        self.assertEqual(code, 200)
        self.assertEqual(a_second_device["treatment_declarations"], ["lifestyle"])
        self.assertEqual(a_second_device["treatment_declaration_updated_at"], expected)

        # Device 1 caches an offline intent; while it is disconnected, device
        # 2 writes a newer version. The queued dictionary is synthetic; this
        # is NOT a Flutter Drift outbox persistence/restart proof.
        queued_offline_intent = self._declaration(["insulin"])
        code, new_a = self._http(
            self.device_2, "PATCH", self.token_a,
            declaration=self._declaration(["lifestyle", "oral_meds"]),
            revision=expected,
        )
        self.assertEqual(code, 200)
        updated = new_a["treatment_declaration_updated_at"]
        self.assertNotEqual(expected, updated)

        code, _ = self._http(
            self.device_1, "PATCH", self.token_a,
            declaration=queued_offline_intent, revision=expected,
        )
        self.assertEqual(code, 409)
        code, _ = self._http(
            self.device_1, "PATCH", self.token_a,
            declaration=queued_offline_intent,
        )
        self.assertEqual(code, 428)

        code, current = self._http(self.device_1, "GET", self.token_a)
        self.assertEqual(code, 200)
        self.assertEqual(current["treatment_declarations"], ["lifestyle", "oral_meds"])
        self.assertEqual(current["treatment_declaration_updated_at"], updated)

        # The same browser HTTP client changes user A -> B -> A. Every GET
        # uses the explicitly supplied bearer and can never borrow A's data.
        code, b_again = self._http(self.device_1, "GET", self.token_b)
        self.assertEqual(code, 200)
        self.assertEqual(b_again["treatment_declarations"], [])
        code, a_again = self._http(self.device_1, "GET", self.token_a)
        self.assertEqual(code, 200)
        self.assertEqual(a_again["treatment_declarations"], ["lifestyle", "oral_meds"])

        # Cross-device stale 409 requires explicit user resolution. A
        # version-correct chosen value can be written after the latest GET.
        code, resolved = self._http(
            self.device_1, "PATCH", self.token_a,
            declaration=self._declaration(["lifestyle", "oral_meds", "insulin"]),
            revision=updated,
        )
        self.assertEqual(code, 200)
        self.assertEqual(
            resolved["treatment_declarations"],
            ["lifestyle", "oral_meds", "insulin"],
        )
        code, last_b = self._http(self.device_2, "GET", self.token_b)
        self.assertEqual(code, 200)
        self.assertEqual(last_b["treatment_declarations"], [])

    def test_live_missing_and_tampered_bearer_denied_before_profile_read(self):
        for bearer in (None, self.token_a + "-forged"):
            code, body = self._http(self.device_2, "GET", bearer)
            self.assertIn(code, (401, 403))
            self.assertNotIn("treatment_declarations", str(body))
        code, existing = self._http(self.device_1, "GET", self.token_a)
        self.assertEqual(code, 200)
        self.assertEqual(existing["treatment_declarations"], [])
