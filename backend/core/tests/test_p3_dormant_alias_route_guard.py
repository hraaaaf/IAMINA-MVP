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

    def test_current_ninja_mount_inventory_has_canonical_router_only(self):
        """Discriminate absent registration from a registered-but-unresolved URL.

        Django Ninja exposes _routers as (prefix, router) pairs across the
        supported API implementation. This is a diagnostic of current state,
        not authorization to activate the P3 alias.
        """
        registered = ModuleRegistry.get("diabetes")
        self.assertIs(registered.router, logs_router)

        mounted_prefixes = [
            prefix
            for prefix, registered_router in api._routers
            if registered_router is logs_router
        ]
        self.assertEqual(
            mounted_prefixes,
            ["/v1"],
            msg=(
                "The P3 alias was attached to Ninja but remains unresolvable; "
                "investigate operation binding / URL generation instead of "
                "assuming ModuleRegistry was empty at API assembly."
            ),
        )

    def test_dormant_alias_has_no_django_resolver_match(self):
        with self.assertRaises(Resolver404):
            resolve("/api/v1/diabetes/logs/batch")

        # The actively supported canonical path must remain reachable.
        self.assertIsNotNone(resolve("/api/v1/logs/batch"))
