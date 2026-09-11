#!/usr/bin/env python3
"""Startup-driven P5-4A PWA update safety probe.

Synthetic/non-patient only. This helper keeps the product code unchanged and
models the real pilot cadence: the user closes v1, a candidate is published,
and the next app startup performs the normal background update check.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from p5_4a_pwa_update_recovery_probe import (
    BASE_URL,
    BROKEN_STATE_PATH,
    HEALTHY_STATE_PATH,
    ChromePage,
    load_release_ids,
    read_json,
    require_network_worker,
    seed_and_restore_v1,
    write_json,
    healthy_activate,
)

HTTP_LOG_PATH = Path("/tmp/iamina-pwa-update-http.log")


def wait_http_request(path_fragment: str, timeout: int = 20) -> bool:
    """Return once the local HTTP server has durably observed a request."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if HTTP_LOG_PATH.exists():
            text = HTTP_LOG_PATH.read_text(encoding="utf-8", errors="replace")
            if path_fragment in text:
                return True
        time.sleep(0.1)
    return False


def seed(path, scenario: str) -> None:
    page = ChromePage()
    try:
        state = seed_and_restore_v1(page)
        state.update({"scenario": scenario, "origin_storage_cleared": False})
        write_json(path, state)
        print(json.dumps(state, indent=2, sort_keys=True))
    finally:
        page.close()


def broken_check() -> None:
    v1_cache, _, _ = load_release_ids()
    state = read_json(BROKEN_STATE_PATH)
    require_network_worker("test-v2-broken")
    page = ChromePage()
    try:
        restored = page.wait_title("IAMINA_PWA_RESTORED:")
        if restored.split(":", 1)[1] != state["storage_implementation"]:
            raise RuntimeError("Drift storage changed after failed-candidate startup")

        # A failed service-worker install can be shorter-lived than CDP polling.
        # The intentionally missing precache request is durable server-side proof
        # that Chrome fetched and attempted to install the broken candidate.
        saw_candidate_attempt = wait_http_request("/missing-v2.asset", timeout=20)

        deadline = time.time() + 10
        last_state = page.sw_state()
        caches: list[str] = page.cache_names()
        while last_state.get("installing") and time.time() < deadline:
            time.sleep(0.1)
            last_state = page.sw_state()
            caches = page.cache_names()

        if not saw_candidate_attempt:
            raise RuntimeError(
                "Broken candidate was published but startup produced no install request: "
                f"state={last_state!r}, caches={caches!r}"
            )
        if last_state.get("installing"):
            raise RuntimeError(f"Broken candidate install did not settle: {last_state!r}")
        if last_state.get("waiting"):
            raise RuntimeError(f"Broken candidate unexpectedly reached waiting: {last_state!r}")
        if v1_cache not in caches:
            raise RuntimeError(f"Broken candidate removed last-known-good v1: {caches!r}")

        page.set_network(True)
        page.call("Page.reload", {"ignoreCache": True})
        offline_restore = page.wait_title("IAMINA_PWA_RESTORED:", timeout=30)
        if offline_restore.split(":", 1)[1] != state["storage_implementation"]:
            raise RuntimeError("Drift storage changed during failed-candidate offline reopen")
        if not page.shell_marker("IAMINA_UPDATE_V1"):
            raise RuntimeError("Broken candidate displaced v1 during offline reopen")

        state.update(
            {
                "scenario": "failed-candidate-preservation",
                "server_exposed_broken_v2": True,
                "broken_candidate_install_request_observed": True,
                "broken_candidate_install_request": "/missing-v2.asset",
                "broken_post_install_state": last_state,
                "broken_cache_names": caches,
                "broken_offline_restore_title": offline_restore,
                "broken_update_preserved_v1_shell": True,
                "origin_storage_cleared": False,
                "result": "PASS",
            }
        )
        write_json(BROKEN_STATE_PATH, state)
        print(json.dumps(state, indent=2, sort_keys=True))
    finally:
        page.close()


def healthy_prepare() -> None:
    v1_cache, _, v3_cache = load_release_ids()
    state = read_json(HEALTHY_STATE_PATH)
    require_network_worker("test-v3-fixed")
    page = ChromePage()
    try:
        restored = page.wait_title("IAMINA_PWA_RESTORED:")
        if restored.split(":", 1)[1] != state["storage_implementation"]:
            raise RuntimeError("Drift storage changed during healthy update startup")

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
                "Healthy v3 did not install and wait on normal app startup: "
                f"state={waiting_state!r}, caches={caches!r}"
            )
        if v1_cache not in caches:
            raise RuntimeError("Healthy candidate removed active v1 before activation")
        if not page.shell_marker("IAMINA_UPDATE_V1"):
            raise RuntimeError("Waiting v3 changed the active v1 shell")
        if not page.cache_contains_marker(v3_cache, "IAMINA_UPDATE_V3_FIXED"):
            raise RuntimeError("v3 cache does not contain the expected v3 bundle")

        state.update(
            {
                "scenario": "healthy-update-preactivation",
                "server_exposed_v3": True,
                "waiting_state": waiting_state,
                "pre_activation_cache_names": caches,
                "pre_activation_restore_title": restored,
                "v3_cache_bundle_verified": True,
                "origin_storage_cleared": False,
                "result": "PASS",
            }
        )
        write_json(HEALTHY_STATE_PATH, state)
        print(json.dumps(state, indent=2, sort_keys=True))
    finally:
        page.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "phase",
        choices=(
            "broken-seed",
            "broken-check",
            "healthy-seed",
            "healthy-prepare",
            "healthy-activate",
        ),
    )
    args = parser.parse_args()
    if args.phase == "broken-seed":
        seed(BROKEN_STATE_PATH, "failed-candidate-seed")
    elif args.phase == "broken-check":
        broken_check()
    elif args.phase == "healthy-seed":
        seed(HEALTHY_STATE_PATH, "healthy-update-seed")
    elif args.phase == "healthy-prepare":
        healthy_prepare()
    else:
        healthy_activate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
