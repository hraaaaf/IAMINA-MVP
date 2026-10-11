"""Guard the currently dormant P3 diabetes HTTP alias (#929).

The project must first decide whether this advertised alias is intentional.
Do not make a new patient mutation route reachable without auth/CSRF review.
"""

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

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

    def test_fresh_django_bootstrap_keeps_p3_alias_dormant(self):
        """A clean Django boot may register diabetes but MUST NOT mount an alias.

        The historical diagnostic confirmed an import-order problem; V1 option
        A makes alias non-exposure intentional regardless of import timing.
        """
        script = textwrap.dedent(
            r"""
            import json
            import os
            import sys
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "amina.settings")
            events = []

            def trace(frame, event, _arg):
                if event != "call":
                    return
                code = frame.f_code
                if not code.co_filename.replace("\\", "/").endswith("/core/registry.py"):
                    return
                if code.co_name not in ("all", "register"):
                    return
                caller = frame.f_back.f_code.co_filename.replace("\\", "/")
                if code.co_name == "all" and not caller.endswith("/diabetes/api/main.py"):
                    return
                cls = frame.f_locals.get("cls")
                if cls is None:
                    return
                events.append({
                    "step": code.co_name,
                    "registered_before": sorted(cls._modules.keys()),
                    "api_in_modules": "diabetes.api.main" in sys.modules,
                    "caller": caller.rsplit("/", 2)[-2:],
                })

            sys.setprofile(trace)
            import django
            django.setup()
            from diabetes.api.main import api
            from diabetes.api.v1.logs import router as logs_router
            from core.registry import ModuleRegistry
            import ninja
            sys.setprofile(None)
            mounts = [
                prefix for prefix, router in api._routers if router is logs_router
            ]
            print("P3_TRACE=" + json.dumps({
                "events": events,
                "registered_final": sorted(ModuleRegistry._modules.keys()),
                "mounts": mounts,
                "django": django.get_version(),
                "ninja": getattr(ninja, "__version__", "unknown"),
            }))
            """
        )
        env = os.environ.copy()
        env.setdefault("DJANGO_SETTINGS_MODULE", "amina.settings")
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[2],
            env=env,
            capture_output=True,
            text=True,
            timeout=40,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            msg=f"Fresh Django bootstrap probe failed: {completed.stderr[-1000:]}",
        )
        traces = [
            line.removeprefix("P3_TRACE=")
            for line in completed.stdout.splitlines()
            if line.startswith("P3_TRACE=")
        ]
        self.assertEqual(len(traces), 1, msg=completed.stdout[-700:])
        observed = json.loads(traces[0])
        self.assertIn("diabetes", observed["registered_final"])
        self.assertEqual(observed["mounts"], ["/v1"])

        # V1 policy A (#929): unlike the historical startup-timing diagnosis,
        # the API assembly no longer attempts ANY registry-driven alias mount.
        assembly = [event for event in observed["events"] if event["step"] == "all"]
        registration = [
            event for event in observed["events"] if event["step"] == "register"
        ]
        self.assertEqual(assembly, [], msg=str(observed))
        self.assertTrue(registration, msg=str(observed))

    def test_manifest_and_triage_declare_only_reachable_chat(self):
        """No dormant namespace is advertised as an emergency-enabled API."""
        from core.safety_registry import TRIAGE_REGISTRY

        manifest = ModuleRegistry.get("diabetes").manifest
        self.assertEqual(manifest.interactive_endpoints, ["/api/v1/ai/chat"])
        self.assertIn("/api/v1/ai/chat", TRIAGE_REGISTRY._paths)
        self.assertNotIn("/api/v1/diabetes/ai/chat", TRIAGE_REGISTRY._paths)
        self.assertEqual(manifest.url_prefix, "/diabetes")  # Reserved only.

    def test_all_p3_aliases_remain_absent_from_schema_and_resolver(self):
        from diabetes.api.main import api

        paths = api.get_openapi_schema()["paths"]
        for alias in (
            "/api/v1/diabetes/logs",
            "/api/v1/diabetes/logs/batch",
            "/api/v1/diabetes/ai/chat",
            "/api/v1/diabetes/ai/chat/stream",
        ):
            with self.subTest(alias=alias):
                self.assertNotIn(alias, paths)
                with self.assertRaises(Resolver404):
                    resolve(alias)
        self.assertIn("/api/v1/ai/chat", paths)
        self.assertIn("/api/v1/ai/chat/stream", paths)

    def test_urgent_text_cannot_revive_dormant_patient_chat_route(self):
        """Even emergency text must not turn a nonexistent P3 URL into HTTP 200."""
        import json
        from unittest.mock import patch

        from django.test import Client, RequestFactory
        from django.contrib.auth.models import AnonymousUser
        from core.middleware.triage_vital import TriageVitalMiddleware

        urgent = json.dumps({"message": "Je suis inconscient"}).encode()
        with patch("companion.core.IAmina") as provider:
            reply = Client().post(
                "/api/v1/diabetes/ai/chat",
                data=urgent,
                content_type="application/json",
            )
            self.assertEqual(reply.status_code, 404)
            stream = Client().post(
                "/api/v1/diabetes/ai/chat/stream",
                data=urgent,
                content_type="application/json",
            )
            self.assertEqual(stream.status_code, 404)
            provider.assert_not_called()

        # Preserve the deterministic emergency guard on the real canonical
        # patient chat endpoint despite dropping the misleading P3 alias.
        req = RequestFactory().post(
            "/api/v1/ai/chat", data=urgent, content_type="application/json"
        )
        req.user = AnonymousUser()
        response = TriageVitalMiddleware(lambda _: None)(req)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content)["is_emergency"])
