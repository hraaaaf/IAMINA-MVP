"""W01 config guard regression: negative mutations must fail closed."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from sys import path as sys_path

ROOT = Path(__file__).resolve().parents[2]
sys_path.insert(0, str(ROOT / "scripts"))
from check_web_topology_contract import check_web_topology  # noqa: E402


class W01WebTopologyContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for rel in [
            "frontend/vercel.json",
            "backend/vercel.json",
            "vercel.json",
            "backend/api/index.py",
            "frontend/vercel_build.sh",
            "frontend/api/preview-proxy.js",
        ]:
            destination = self.root / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, destination)

    def _edit_json(self, rel: str, change) -> None:
        path = self.root / rel
        config = json.loads(path.read_text(encoding="utf-8"))
        change(config)
        path.write_text(json.dumps(config), encoding="utf-8")

    def test_all_manifests_pass_with_no_deploy(self) -> None:
        self.assertEqual(check_web_topology(self.root), [])

    def test_accidental_frontend_git_deployment_is_blocked(self) -> None:
        self._edit_json("frontend/vercel.json", lambda cfg: cfg["git"].update(deploymentEnabled=True))
        self.assertTrue(any("frontend/vercel.json" in e for e in check_web_topology(self.root)))

    def test_missing_backend_function_fails_closed(self) -> None:
        self._edit_json("backend/vercel.json", lambda cfg: cfg.pop("functions"))
        self.assertTrue(any("Django WSGI" in e for e in check_web_topology(self.root)))

    def test_frontend_build_must_not_embed_db_secret(self) -> None:
        with (self.root / "frontend/vercel_build.sh").open("a", encoding="utf-8") as f:
            f.write("\nDATABASE_URL=should_never_be_here\n")
        self.assertTrue(any("SQL credentials" in e for e in check_web_topology(self.root)))

    def test_preview_api_must_not_fall_through_to_flutter_html(self) -> None:
        self._edit_json("frontend/vercel.json", lambda cfg: cfg.pop("rewrites"))
        self.assertTrue(any("BFF API rewrite" in e for e in check_web_topology(self.root)))

    def test_proxy_preview_gate_must_remain(self) -> None:
        path = self.root / "frontend/api/preview-proxy.js"
        path.write_text(path.read_text(encoding="utf-8").replace("VERCEL_ENV !== 'preview'", "false"))
        self.assertTrue(any("proxy fail-closed" in e for e in check_web_topology(self.root)))

    def test_backend_region_needs_explicit_review(self) -> None:
        self._edit_json("backend/vercel.json", lambda cfg: cfg.update(regions=["fra1"]))
        self.assertTrue(any("region baseline" in e for e in check_web_topology(self.root)))


if __name__ == "__main__":
    unittest.main()
