"""W02/D11 regression: production patient demo seeding must stay disabled."""
from types import SimpleNamespace
from unittest.mock import patch
from django.test import SimpleTestCase
from ninja.errors import HttpError
from diabetes.api.v1.demo import seed_demo_data

class W02D11DemoSeedDisabledTests(SimpleTestCase):
    def test_owner_a_and_b_cannot_be_seeded(self):
        with (
            patch("diabetes.models.LogEntry.objects.bulk_create") as insert,
            patch("core.models.BasePatientProfile.objects.get_or_create") as profile,
        ):
            for user_id in (734, 812):
                with self.subTest(user_id=user_id):
                    with self.assertRaises(HttpError) as raised:
                        seed_demo_data(SimpleNamespace(user=SimpleNamespace(id=user_id)))
                    self.assertEqual(raised.exception.status_code, 404)
            insert.assert_not_called()
            profile.assert_not_called()

    def test_refusal_precedes_any_identity_access(self):
        class DenyIdentity:
            @property
            def user(self):
                raise AssertionError("D11 handler must not inspect patient")
        with self.assertRaises(HttpError) as raised:
            seed_demo_data(DenyIdentity())
        self.assertEqual(raised.exception.status_code, 404)

    def test_anonymous_or_empty_request_never_seeds(self):
        with self.assertRaises(HttpError) as raised:
            seed_demo_data(SimpleNamespace())
        self.assertEqual(raised.exception.status_code, 404)
