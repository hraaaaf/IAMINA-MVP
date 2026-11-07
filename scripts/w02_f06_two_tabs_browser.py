#!/usr/bin/env python3
"""W02-F06: real two-tab Chrome + Flutter AuthService + disposable Django PG16.

No PHI, no hosted deployment, no clinical API, no secret/log token contents.
A and B are separate top-level browser pages/JS isolates at the same origin.
This runs a real Flutter Web probe, NOT a single-isolate flutter_test mock.
"""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as BrowserTimeout

ORIGIN = "http://127.0.0.1:7386"
EVIDENCE = Path("w02-f06-two-tabs-proof.json")


def safe_state(page):
    try:
        return page.locator("#w02-f06-state").evaluate(
            """node => ({
              remote: node.dataset.remote ?? null,
              bound: node.dataset.bound ?? null,
              login: node.dataset.loginResult ?? null,
              logout: node.dataset.logoutResult ?? null,
              token: node.dataset.tokenPresent ?? null,
              scope: node.dataset.scopePresent ?? null
            })"""
        )
    except Exception:
        return {"unavailable": True}


def settled(page, key, value, timeout=30000):
    page.wait_for_function(
        """([key, expected]) =>
          document.querySelector('#w02-f06-state')?.dataset[key] === expected""",
        arg=[key, value], timeout=timeout,
    )


def login(page):
    page.locator("#w02-f06-login").click()
    settled(page, "loginResult", "success")
    settled(page, "remote", "true")


def inspect_locked(page):
    page.locator("#w02-f06-sample").click()
    settled(page, "sampleResult", "success")
    state = safe_state(page)
    if any(state.get(k) != "false" for k in ("remote", "bound", "token", "scope")):
        raise AssertionError("Stale remote authority remained in tab A")


def main():
    proof = {
        "result": "RED_NOT_YET_EXECUTED",
        "scope": "real Chrome pages, distinct JS isolates, real Flutter AuthService, synthetic local Django PG16",
        "steps": [],
        "tabs": 2,
        "hosted_deployment": "NOT_RUN",
        "patient_data": "NONE",
        "server_origin": "localhost",
        "browser_origin": ORIGIN,
    }
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = browser.new_context()
            page_a = context.new_page()
            page_b = context.new_page()
            try:
                for page in (page_a, page_b):
                    page.goto(ORIGIN, wait_until="domcontentloaded", timeout=40000)
                    page.wait_for_function(
                        "() => document.title === 'IAMINA_W02_F06_LOCKED'",
                        timeout=65000,
                    )
                if len(context.pages) != 2 or page_a == page_b:
                    raise AssertionError("Expected distinct live Chrome tabs")
                proof["steps"].append("both_tabs_booted_same_origin")

                login(page_a)
                login(page_b)
                proof["steps"].append("both_tabs_have_live_bearer")
                if safe_state(page_a)["bound"] != "true":
                    raise AssertionError("Tab A never obtained bound Django principal")
                if safe_state(page_b)["bound"] != "true":
                    raise AssertionError("Tab B never obtained bound Django principal")

                page_b.locator("#w02-f06-logout").click()
                settled(page_b, "logoutResult", "success", timeout=25000)
                settled(page_b, "remote", "false")
                proof["steps"].append("tab_b_logged_out_and_server_acknowledged")

                # DO NOT navigate, reload, or touch tab A during this wait.
                # A cross-tab revocation has to arrive automatically while tab
                # A's Flutter AuthService and its old bearer are already live.
                try:
                    page_a.wait_for_function(
                        "() => document.title === 'IAMINA_W02_F06_LOCKED'",
                        timeout=8000,
                    )
                except BrowserTimeout as exc:
                    raise AssertionError(
                        "W02 F06 RED: tab A kept published native authority "
                        "after tab B completed remote logout"
                    ) from exc
                proof["steps"].append("tab_a_revoke_observed_without_reload")
                inspect_locked(page_a)
                proof["steps"].append("tab_a_no_bearer_no_scope")

                # New round with a reachable login then simulated offline B
                # logout. This does NOT change Django's auth_token_version:
                # A still must lose authority from the cross-tab event.
                login(page_a)
                login(page_b)
                proof["steps"].append("relogin_both_tabs")
                page_b.route(
                    "**/api/v1/auth/logout",
                    lambda route: route.abort("failed"),
                )
                page_b.locator("#w02-f06-logout").click()
                settled(page_b, "logoutResult", "success", timeout=25000)
                proof["steps"].append("tab_b_local_logout_when_backend_unavailable")
                try:
                    page_a.wait_for_function(
                        "() => document.title === 'IAMINA_W02_F06_LOCKED'",
                        timeout=8000,
                    )
                except BrowserTimeout as exc:
                    raise AssertionError(
                        "W02 F06 RED: tab A kept authority when B logged out offline"
                    ) from exc
                inspect_locked(page_a)
                proof["steps"].append("tab_a_offline_revoke_no_bearer_no_scope")
                proof["result"] = "PASS_2_LIVE_TABS"
            finally:
                proof["tab_a"] = safe_state(page_a)
                proof["tab_b"] = safe_state(page_b)
                context.close()
                browser.close()
    except Exception as exc:
        proof["result"] = "RED"
        proof["error_type"] = type(exc).__name__
        # Intentionally never disclose credential bytes/response body.
        proof["error"] = str(exc).split("\n")[0][:200]
    finally:
        EVIDENCE.write_text(json.dumps(proof, indent=2), encoding="utf-8")
        print(json.dumps(proof, indent=2))
    if proof["result"] != "PASS_2_LIVE_TABS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
