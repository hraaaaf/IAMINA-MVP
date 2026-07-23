"""
P3 Module Registry — Tests for ModuleRegistry + module activation endpoints.

T1: After Django startup, ModuleRegistry.get("diabetes") returns a RegisteredModule
T2: is_registered() returns True for "diabetes" and False for unknown names
T3: Calling register() twice with same name is idempotent (no duplicate, no error)
T4: POST /api/v1/account/modules/diabetes/activate → 200, PatientModule row created
T5: POST /api/v1/account/modules/diabetes/activate (again) → 200 idempotent, count still 1
T6: POST /api/v1/account/modules/unknown/activate → 404
T7: GET /api/v1/account/modules → 200, returns list with "diabetes"
T8: require_module("diabetes") raises HttpError 404 when module not activated for patient
"""
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from ninja.errors import HttpError

from core.api.v1.dependencies import require_module
from core.models import BasePatientProfile, PatientModule
from core.registry import ModuleRegistry, RegisteredModule
from diabetes.models import DiabetesProfile


def _make_user(username: str):
    """Create User + BasePatientProfile + DiabetesProfile (standard test setup)."""
    user = User.objects.create_user(username=username, email=f"{username}@p3test.com")
    base = BasePatientProfile.objects.create(
        patient=user,
        date_of_birth=date(1988, 6, 15),
    )
    DiabetesProfile.objects.create(
        base_profile=base,
        diabetes_type="type2",
        treatment_type="diet",
    )
    return user, base


# ── T1 ───────────────────────────────────────────────────────────────────────

class RegistryGetTest(TestCase):
    """T1: ModuleRegistry.get("diabetes") returns a RegisteredModule after startup."""

    def test_get_diabetes_returns_registered_module(self):
        mod = ModuleRegistry.get("diabetes")
        self.assertIsInstance(mod, RegisteredModule)
        self.assertEqual(mod.manifest.name, "diabetes")
        self.assertEqual(mod.manifest.url_prefix, "/diabetes")
        self.assertEqual(mod.manifest.version, "1.0.0")


# ── T2 ───────────────────────────────────────────────────────────────────────

class RegistryIsRegisteredTest(TestCase):
    """T2: is_registered() returns correct booleans."""

    def test_diabetes_is_registered(self):
        self.assertTrue(ModuleRegistry.is_registered("diabetes"))

    def test_unknown_module_not_registered(self):
        self.assertFalse(ModuleRegistry.is_registered("hypertension"))
        self.assertFalse(ModuleRegistry.is_registered(""))
        self.assertFalse(ModuleRegistry.is_registered("unknown"))


# ── T3 ───────────────────────────────────────────────────────────────────────

class RegistryIdempotentTest(TestCase):
    """T3: Calling register() twice with same name does not raise and keeps one entry."""

    def test_double_register_is_idempotent(self):
        # Capture the current diabetes entry
        original = ModuleRegistry.get("diabetes")
        count_before = len(ModuleRegistry.all())

        # Re-register with the same manifest (simulates a duplicate call)
        ModuleRegistry.register(original.manifest, original.engine_class, original.router)

        # Still exactly the same number of entries
        self.assertEqual(len(ModuleRegistry.all()), count_before)
        # The entry is still "diabetes"
        self.assertTrue(ModuleRegistry.is_registered("diabetes"))


# ── T4 ───────────────────────────────────────────────────────────────────────

class ActivateModuleTest(TestCase):
    """T4: POST /api/v1/account/modules/diabetes/activate creates a PatientModule row."""

    def setUp(self):
        self.user, self.base = _make_user("p3_activate")
        self.client.force_login(self.user)

    def test_activate_diabetes_returns_200_and_creates_row(self):
        resp = self.client.post(
            "/api/v1/account/modules/diabetes/activate",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["module"], "diabetes")
        self.assertTrue(data["activated"])
        self.assertIn("activated_at", data)

        # Verify DB row created
        self.assertTrue(
            PatientModule.objects.filter(
                patient=self.base, module_name="diabetes", is_active=True
            ).exists()
        )


# ── T5 ───────────────────────────────────────────────────────────────────────

class ActivateModuleIdempotentTest(TestCase):
    """T5: Calling activate twice does not create a duplicate row."""

    def setUp(self):
        self.user, self.base = _make_user("p3_idempotent")
        self.client.force_login(self.user)

    def test_double_activate_is_idempotent(self):
        url = "/api/v1/account/modules/diabetes/activate"
        resp1 = self.client.post(url, content_type="application/json")
        self.assertEqual(resp1.status_code, 200)

        resp2 = self.client.post(url, content_type="application/json")
        self.assertEqual(resp2.status_code, 200)

        count = PatientModule.objects.filter(
            patient=self.base, module_name="diabetes"
        ).count()
        self.assertEqual(count, 1)


# ── T6 ───────────────────────────────────────────────────────────────────────

class ActivateUnknownModuleTest(TestCase):
    """T6: POST /api/v1/account/modules/unknown/activate → 404."""

    def setUp(self):
        self.user, _ = _make_user("p3_unknown")
        self.client.force_login(self.user)

    def test_unknown_module_returns_404(self):
        resp = self.client.post(
            "/api/v1/account/modules/hypertension/activate",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 404)


# ── T7 ───────────────────────────────────────────────────────────────────────

class ListModulesTest(TestCase):
    """T7: GET /api/v1/account/modules returns active modules for patient."""

    def setUp(self):
        self.user, self.base = _make_user("p3_list")
        self.client.force_login(self.user)

    def test_list_modules_returns_active_modules(self):
        # Pre-create the PatientModule row
        PatientModule.objects.create(
            patient=self.base,
            module_name="diabetes",
            is_active=True,
        )

        resp = self.client.get("/api/v1/account/modules")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("modules", data)
        module_names = [m["name"] for m in data["modules"]]
        self.assertIn("diabetes", module_names)

    def test_list_modules_empty_when_none_activated(self):
        resp = self.client.get("/api/v1/account/modules")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["modules"], [])


# ── T8 ───────────────────────────────────────────────────────────────────────

class RequireModuleDependencyTest(TestCase):
    """T8: require_module("diabetes") raises HttpError(404) when module not activated."""

    def setUp(self):
        self.user, self.base = _make_user("p3_require")

    def test_require_module_raises_when_not_activated(self):
        """require_module dependency raises HttpError 404 if no PatientModule row exists."""
        dep = require_module("diabetes")

        # Build a minimal mock request object
        class MockRequest:
            user = self.user

        with self.assertRaises(HttpError) as ctx:
            dep(MockRequest())
        self.assertEqual(ctx.exception.status_code, 404)

    def test_require_module_returns_pm_when_activated(self):
        """require_module dependency returns PatientModule when the module is active."""
        pm = PatientModule.objects.create(
            patient=self.base,
            module_name="diabetes",
            is_active=True,
        )
        dep = require_module("diabetes")

        class MockRequest:
            user = self.user

        result = dep(MockRequest())
        self.assertEqual(result.pk, pm.pk)
        self.assertEqual(result.module_name, "diabetes")
