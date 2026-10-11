"""Guard the currently dormant P3 diabetes HTTP alias (#929).

The project must first decide whether this advertised alias is intentional.
Do not make a new patient mutation route reachable without auth/CSRF review.
"""

from django.test import SimpleTestCase
from django.urls import Resolver404, resolve

from core.registry import ModuleRegistry
from diabetes.api.main import api
from diabetes.api.v1.logs import router as logs_router


class P3DormantAliasRouteGuardTest(SimpleTestCase):
    def test_registry_has_module_but_alias_is_not_in_openapi(self):
        entry = ModuleRegistry.get("diabetes")
        self.assertIs(entry.router, logs_router)
        self.assertEqual(entry.manifest.url_prefix, "/diabetes")

        paths = api.get_openapi_schema()["paths"]
        self.assertIn("/api/v1/logs/batch", paths)
        self.assertNotIn("/api/v1/diabetes/logs/batch", paths)

    def test_dormant_alias_has_no_django_resolver_match(self):
        with self.assertRaises(Resolver404):
            resolve("/api/v1/diabetes/logs/batch")

        # The actively supported canonical path must remain reachable.
        self.assertIsNotNone(resolve("/api/v1/logs/batch"))
