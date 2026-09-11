#!/usr/bin/env python3
"""Real-Chrome P5-4A PWA update/recovery probe.

Synthetic/non-patient only. The three phases are separated by full browser
restarts so the rehearsal matches the pilot update contract: a candidate
installs in the background, waits while the old release has a client, and
activates only after that client closes.
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
import urllib.request
from pathlib import Path

from websocket import create_connection

BASE_URL = "http://127.0.0.1:7362/"
DEVTOOLS = "http://127.0.0.1:9225"
ROOT = Path("p5-4a-pwa-update").resolve()
STATE_PATH = Path("p5-4a-pwa-update-proof/phase-state.json")
PROOF_PATH = Path("p5-4a-pwa-update-proof/pwa-update-recovery-proof.json")


class ChromePage:
    def __init__(self) -> None:
        deadline = time.time() + 20
        page = None
        while time.time() < deadline:
            pages = json.load(urllib.request.urlopen(f"{DEVTOOLS}/json/list"))
            page = next(
                (
                    item
                    for item in pages
                    if item.get("type") == "page"
                    and str(item.get("url", "")).startswith(BASE_URL)
                ),
                None,
            )
            if page is not None:
                break
            time.sleep(0.2)
        if page is None:
            raise RuntimeError("IAMINA page target not found in Chrome")

        self.ws = create_connection(page["webSocketDebuggerUrl"], timeout=20)
        self.counter = 0
        self.call("Page.enable")
        self.call("Runtime.enable")
        self.call("Network.enable")

    def close(self) -> None:
        self.ws.close()

    def call(self, method: str, params: dict | None = None) -> dict:
        self.counter += 1
        self.ws.send(
            json.dumps({"id": self.counter, "method": method, "params": params or {}})
        )
        while True:
            response = json.loads(self.ws.recv())
            if response.get("id") == self.counter:
                if "error" in response:
                    raise RuntimeError(f"{method}: {response['error']}")
                return response.get("result", {})

    def evaluate(self, expression: str, await_promise: bool = False):
        result = self.call(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": await_promise,
            },
        )
        return result["result"].get("value")

    def title(self) -> str:
        return self.evaluate("document.title") or ""

    def wait_title(self, prefix: str, timeout: int = 30) -> str:
        deadline = time.time() + timeout
        last = ""
        while time.time() < deadline:
            last = self.title()
            if last.startswith(prefix):
                return last
            if last.startswith("IAMINA_PWA_ERROR:"):
                raise RuntimeError(last)
            time.sleep(0.25)
        raise RuntimeError(f"Expected title {prefix!r}, got {last!r}")

    def sw_state(self) -> dict:
        return self.evaluate(
            "navigator.serviceWorker.getRegistrations().then(r => ({"
            "count:r.length, controller:!!navigator.serviceWorker.controller, "
            "active:r.some(x=>!!x.active), installing:r.some(x=>!!x.installing), "
            "waiting:r.some(x=>!!x.waiting)}))",
            True,
        )

    def cache_names(self) -> list[str]:
        return self.evaluate("caches.keys()", True) or []

    def wait_cache(
        self,
        expected: str,
        *,
        forbidden: tuple[str, ...] = (),
        timeout: int = 20,
    ) -> list[str]:
        deadline = time.time() + timeout
        last: list[str] = []
        while time.time() < deadline:
            last = self.cache_names()
            state = self.sw_state()
            if (
                expected in last
                and all(name not in last for name in forbidden)
                and state.get("active")
                and state.get("controller")
            ):
                return last
            time.sleep(0.25)
        raise RuntimeError(
            f"Expected cache {expected!r} without {forbidden!r}; "
            f"got {last!r}, state={self.sw_state()!r}"
        )

    def shell_marker(self, marker: str) -> bool:
        return bool(
            self.evaluate(
                "fetch('main.dart.js').then(r => r.text()).then(t => t.includes("
                + json.dumps(marker)
                + "))",
                True,
            )
        )

    def set_network(self, offline: bool) -> None:
        self.call("Network.setCacheDisabled", {"cacheDisabled": True})
        self.call(
            "Network.emulateNetworkConditions",
            {
                "offline": offline,
                "latency": 0,
                "downloadThroughput": 0 if offline else 100000000,
                "uploadThroughput": 0 if offline else 100000000,
            },
        )


def publish_release(name: str) -> None:
    """Atomically replace files under the stable HTTP server directory."""
    source = ROOT / "releases" / name
    served = ROOT / "served"
    staging = ROOT / "served.next"
    previous = ROOT / "served.previous"

    for path in (staging, previous):
        if path.exists():
            shutil.rmtree(path)
    shutil.copytree(source, staging)
    if served.exists():
        served.rename(previous)
    staging.rename(served)
    if previous.exists():
        shutil.rmtree(previous)


def network_worker_text() -> str:
    request = urllib.request.Request(
        f"{BASE_URL}iamina_service_worker.js?probe={time.time_ns()}",
        headers={"Cache-Control": "no-cache"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.read().decode("utf-8")


def require_network_worker(marker: str) -> None:
    text = network_worker_text()
    if marker not in text:
        raise RuntimeError(
            f"HTTP server did not expose expected service worker marker {marker!r}"
        )


def load_release_ids() -> tuple[str, str, str]:
    base_release = ROOT.joinpath("base-release.txt").read_text(encoding="utf-8").strip()
    return (
        f"iamina-app-shell-{base_release}",
        "iamina-app-shell-test-v2-broken",
        "iamina-app-shell-test-v3-fixed",
    )


def load_state() -> dict:
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def phase1() -> None:
    v1_cache, _, _ = load_release_ids()
    page = ChromePage()
    try:
        seeded = page.wait_title("IAMINA_PWA_SEEDED:")
        storage = seeded.split(":", 1)[1]
        if storage in ("", "unknown", "inMemory"):
            raise RuntimeError(f"Non-persistent Drift storage: {storage!r}")

        initial_caches = page.wait_cache(v1_cache)
        if not page.shell_marker("IAMINA_UPDATE_V1"):
            raise RuntimeError("Initial v1 shell marker is not served")

        page.call("Page.navigate", {"url": f"{BASE_URL}?phase=verify"})
        initial_restore = page.wait_title("IAMINA_PWA_RESTORED:")

        publish_release("v2-broken")
        require_network_worker("test-v2-broken")
        broken_update_result = page.evaluate(
            "(async()=>{const r=await navigator.serviceWorker.getRegistration(); "
            "try {await r.update(); return 'update-called';} "
            "catch(e) {return 'update-rejected:' + e.name;}})()",
            True,
        )

        deadline = time.time() + 15
        while time.time() < deadline:
            state = page.sw_state()
            if not state.get("installing"):
                break
            time.sleep(0.25)
        post_broken_state = page.sw_state()
        if post_broken_state.get("waiting"):
            raise RuntimeError(
                f"Broken v2 unexpectedly reached waiting state: {post_broken_state!r}"
            )

        broken_caches = page.cache_names()
        if v1_cache not in broken_caches:
            raise RuntimeError(
                f"Broken v2 removed last-known-good cache: {broken_caches!r}"
            )

        page.set_network(True)
        page.call("Page.reload", {"ignoreCache": True})
        broken_offline_restore = page.wait_title("IAMINA_PWA_RESTORED:", timeout=30)
        if not page.shell_marker("IAMINA_UPDATE_V1"):
            raise RuntimeError("Broken v2 displaced last-known-good v1 shell offline")
        page.set_network(False)

        save_state(
            {
                "storage_implementation": storage,
                "initial_cache_names": initial_caches,
                "initial_restore_title": initial_restore,
                "broken_update_result": broken_update_result,
                "broken_post_install_state": post_broken_state,
                "broken_cache_names": broken_caches,
                "broken_offline_restore_title": broken_offline_restore,
                "broken_update_preserved_v1_shell": True,
                "server_exposed_broken_v2": True,
            }
        )
    finally:
        page.close()


def phase2() -> None:
    v1_cache, _, v3_cache = load_release_ids()
    state = load_state()
    require_network_worker("test-v3-fixed")
    page = ChromePage()
    try:
        restored = page.wait_title("IAMINA_PWA_RESTORED:")
        if restored.split(":", 1)[1] != state["storage_implementation"]:
            raise RuntimeError("Drift storage changed after browser restart")
        if not page.shell_marker("IAMINA_UPDATE_V1"):
            raise RuntimeError("v1 shell was not retained while v3 downloaded")

        page.evaluate(
            "(async()=>{const r=await navigator.serviceWorker.getRegistration(); "
            "await r.update(); return true;})()",
            True,
        )

        deadline = time.time() + 30
        waiting_state = None
        caches: list[str] = []
        while time.time() < deadline:
            waiting_state = page.sw_state()
            caches = page.cache_names()
            if waiting_state.get("waiting") and v3_cache in caches:
                break
            time.sleep(0.25)
        if not waiting_state or not waiting_state.get("waiting") or v3_cache not in caches:
            raise RuntimeError(
                "Forward-fix v3 did not install and wait safely: "
                f"state={waiting_state!r}, caches={caches!r}"
            )
        if v1_cache not in caches:
            raise RuntimeError("v3 install removed v1 before activation")
        if not page.shell_marker("IAMINA_UPDATE_V1"):
            raise RuntimeError("waiting v3 altered the active v1 shell")

        state.update(
            {
                "forward_fix_waiting_state": waiting_state,
                "pre_activation_cache_names": caches,
                "pre_activation_restore_title": restored,
                "server_exposed_forward_fix_v3": True,
            }
        )
        save_state(state)
    finally:
        page.close()


def phase3() -> None:
    v1_cache, v2_cache, v3_cache = load_release_ids()
    state = load_state()
    page = ChromePage()
    try:
        forward_caches = page.wait_cache(
            v3_cache,
            forbidden=(v1_cache, v2_cache),
            timeout=30,
        )
        page.call("Page.reload", {"ignoreCache": True})
        forward_restore = page.wait_title("IAMINA_PWA_RESTORED:")
        if forward_restore.split(":", 1)[1] != state["storage_implementation"]:
            raise RuntimeError("Drift storage changed after forward-fix activation")
        if not page.shell_marker("IAMINA_UPDATE_V3_FIXED"):
            raise RuntimeError("Forward-fix v3 shell is not served online")

        page.set_network(True)
        page.call("Page.reload", {"ignoreCache": True})
        forward_offline_restore = page.wait_title("IAMINA_PWA_RESTORED:", timeout=30)
        if not page.shell_marker("IAMINA_UPDATE_V3_FIXED"):
            raise RuntimeError("Forward-fix v3 shell is not served offline")

        result = {
            "evidence_class": "synthetic-non-patient-browser",
            **state,
            "forward_fix_cache_names": forward_caches,
            "forward_fix_restore_title": forward_restore,
            "forward_fix_offline_restore_title": forward_offline_restore,
            "forward_fix_v3_shell_verified": True,
            "http_cache_disabled_for_offline_checks": True,
            "origin_storage_cleared": False,
            "activation_model": "natural-after-controlled-client-close",
            "result": "PASS",
        }
        PROOF_PATH.write_text(
            json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
        )
        print(json.dumps(result, indent=2, sort_keys=True))
    finally:
        page.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("phase1", "phase2", "phase3"))
    args = parser.parse_args()
    {"phase1": phase1, "phase2": phase2, "phase3": phase3}[args.phase]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
