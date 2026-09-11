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
    v1_cache, v2_cache, _ = load_release_ids()
    state = read_json(BROKEN_STATE_PATH)
    require_network_worker("test-v2-broken")
    page = ChromePage()
    try:
        restored = page.wait_title("IAMINA_PWA_RESTORED:")
        if restored.split(":", 1)[1] != state["storage_implementation"]:
            raise RuntimeError("Drift storage changed after failed-candidate startup")

        deadline = time.time() + 20
        saw_candidate_attempt = False
        last_state = None
        caches: list[str] = []
        while time.time() < deadline:
            last_state = page.sw_state()
            caches = page.cache_names()
            saw_candidate_attempt = saw_candidate_attempt or v2_cache in caches or bool(
                last_state.get("installing")
            )
            if saw_candidate_attempt and not last_state.get("installing"):
                break
            time.sleep(0.25)

        if not saw_candidate_attempt:
            raise RuntimeError(
                "Broken candidate was published but startup produced no observable update attempt: "
                f"state={last_state!r}, caches={caches!r}"
            )
        if last_state and last_state.get("waiting"):
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
