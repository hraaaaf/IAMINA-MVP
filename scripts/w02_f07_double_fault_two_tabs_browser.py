#!/usr/bin/env python3
"""W02-F07 real Chrome tabs, Django PG16, doubly failing browser storage.

Isolation: synthetic account, random CI-only masked password, localhost only.
Proof contains booleans and event labels, NEVER bearer bytes, password or PHI.
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as BrowserTimeout

ORIGIN = "http://127.0.0.1:7387"
EVIDENCE = Path("w02-f07-double-fault-tabs-proof.json")


def state(page):
    try:
        return page.locator("#w02-f07-state").evaluate(
            """node => ({
              remote: node.dataset.remote ?? null,
              bound: node.dataset.bound ?? null,
              login: node.dataset.loginResult ?? null,
              logout: node.dataset.logoutResult ?? null,
              logoutSettled: node.dataset.logoutSettled ?? null,
              faultArmed: node.dataset.faultArmed ?? null,
              serverConfirmed: node.dataset.serverConfirmed ?? null,
              persisted: node.dataset.persistentBearer ?? null,
              token: node.dataset.tokenPresent ?? null,
              scope: node.dataset.scopePresent ?? null
            })"""
        )
    except Exception:
        return {"unavailable": True}


def until(page, key, value, timeout=30000):
    page.wait_for_function(
        """([key, expected]) =>
          document.querySelector('#w02-f07-state')?.dataset[key] === expected""",
        arg=[key, value], timeout=timeout,
    )


def click(page, action):
    page.evaluate(
        """id => document.getElementById(id).click()""",
        f"w02-f07-{action}",
    )


def sign_in(page):
    click(page, "login")
    until(page, "loginResult", "success")
    until(page, "remote", "true")
    until(page, "bound", "true")


def inspect_no_authority(page):
    click(page, "sample")
    until(page, "sampleResult", "success")
    values = state(page)
    for key in ("remote", "bound", "token", "scope"):
        if values.get(key) != "false":
            raise AssertionError(f"W02-F07 FAIL: stale {key} authority in live Chrome tab")


def run():
    proof = {
        "result": "NOT_VERIFIED",
        "scope": "real two-tab Flutter Web AuthService + actual browser secure storage + local Django PG16",
        "fault": "logout fence write AND native bearer delete fail; HTTP logout aborted",
        "steps": [],
        "tabs": 2,
        "patient_data": "NONE",
        "hosted_deployment": "NOT_RUN",
        "remote_revocation_confirmation": "NOT_CONFIRMED_OFFLINE",
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
                page_a.goto(ORIGIN, wait_until="domcontentloaded", timeout=40000)
                page_b.goto(
                    f"{ORIGIN}/?fault_storage=1",
                    wait_until="domcontentloaded",
                    timeout=40000,
                )
                for page in (page_a, page_b):
                    page.wait_for_function(
                        "() => document.title === 'IAMINA_W02_F07_LOCKED'",
                        timeout=65000,
                    )
                if len(context.pages) != 2 or page_a == page_b:
                    raise AssertionError("Two distinct live Chrome tabs not created")
                proof["steps"].append("distinct_tabs_loaded")

                sign_in(page_a)
                sign_in(page_b)
                proof["steps"].append("both_tabs_have_verified_native_bearer")
                until(page_b, "persistedBearer", "true")
                proof["steps"].append("tab_b_bearer_persisted_before_fault")

                # Fault only AFTER both normal logins have persisted their
                # credentials. Block only the logout POST, NOT user login.
                page_b.route(
                    "**/api/v1/auth/logout",
                    lambda route: route.abort("failed"),
                )
                click(page_b, "arm")
                until(page_b, "faultArmed", "true")
                proof["steps"].append("tab_b_double_storage_fault_armed")

                click(page_b, "logout")
                until(page_b, "logoutSettled", "true", timeout=30000)
                b = state(page_b)
                if b.get("logout") != "StateError":
                    raise AssertionError(
                        "W02-F07 FAIL: double persistent-storage refusal not observable"
                    )
                if b.get("persisted") != "true":
                    raise AssertionError(
                        "W02-F07 FAIL: synthetic bearer deletion unexpectedly succeeded"
                    )
                if b.get("serverConfirmed") != "false":
                    raise AssertionError(
                        "W02-F07 FAIL: blocked HTTP falsely confirmed remote revocation"
                    )
                if b.get("remote") != "false" or b.get("bound") != "false":
                    raise AssertionError(
                        "W02-F07 FAIL: tab B retained local remote authority"
                    )
                proof["steps"].append("tab_b_logout_throws_with_persisted_bearer_and_no_server_confirmation")

                # A is left open and untouched. The BroadcastChannel event
                # must invalidate A before faulted storage/network operations.
                try:
                    page_a.wait_for_function(
                        "() => document.title === 'IAMINA_W02_F07_LOCKED'",
                        timeout=8000,
                    )
                except BrowserTimeout as exc:
                    raise AssertionError(
                        "W02-F07 RED: tab A retained remote authority during "
                        "B's simultaneous storage and backend failures"
                    ) from exc
                inspect_no_authority(page_a)
                inspect_no_authority(page_b)
                proof["steps"].append("tab_a_and_b_have_no_bearer_or_vault_scope")

                # Browser reload with the genuinely persisted stale bearer
                # still present must never re-hydrate a remote session.
                page_b.reload(wait_until="domcontentloaded", timeout=40000)
                page_b.wait_for_function(
                    "() => document.title === 'IAMINA_W02_F07_LOCKED'",
                    timeout=65000,
                )
                until(page_b, "persistentBearer", "true")
                inspect_no_authority(page_b)
                proof["steps"].append("tab_b_cold_reload_stale_bytes_denied")
                proof["result"] = "PASS_DOUBLE_STORAGE_AND_NETWORK_FAULT"
            finally:
                proof["tab_a"] = state(page_a)
                proof["tab_b"] = state(page_b)
                context.close()
                browser.close()
    except Exception as error:
        proof["result"] = "FAIL"
        proof["error_type"] = type(error).__name__
        proof["error"] = str(error).split("\n")[0][:180]
    finally:
        EVIDENCE.write_text(json.dumps(proof, indent=2), encoding="utf-8")
        print(json.dumps(proof, indent=2))

    if proof["result"] != "PASS_DOUBLE_STORAGE_AND_NETWORK_FAULT":
        raise SystemExit(1)


if __name__ == "__main__":
    run()
