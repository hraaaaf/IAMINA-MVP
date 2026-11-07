#!/usr/bin/env python3
"""W02 C9: real Flutter Web compiled, TWO isolated tabs in Chromium+WebKit.

Synthetic local HTTP server; no Django/Ninja integration on this browser
probe, no real credentials/patient data. C7/C6 PG16 integration is tested
separately. Evidence contains only booleans and coarse step names.
"""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as BrowserTimeout

ORIGIN = os.environ.get("W02_C9_BROWSER_ORIGIN", "http://127.0.0.1:7399").rstrip("/")
PROOF = Path("w02-f09-c7c8c9-local-browser-proof.json")


def state(page):
    return page.locator("#w02-c9-state").evaluate(
        """node => ({
            access:node.dataset.access ?? null,
            tokenPresent:node.dataset.tokenPresent ?? null,
            activate:node.dataset.activateResult ?? null,
            refresh:node.dataset.refreshResult ?? null,
            logout:node.dataset.logoutResult ?? null,
            outage:node.dataset.outage ?? null,
            direction:node.dataset.direction ?? null,
            lang:node.dataset.lang ?? null
        })"""
    )


def until(page, key, value, timeout=25000):
    page.wait_for_function(
        """([name, expected]) => document
            .querySelector('#w02-c9-state')?.dataset[name] === expected""",
        arg=[key, value], timeout=timeout,
    )


def click(page, name):
    page.evaluate(
        "(id) => document.getElementById(id).click()", f"w02-c9-{name}"
    )


def ensure_locked(page):
    until(page, "access", "false")
    until(page, "tokenPresent", "false")
    if page.title() != "IAMINA_W02_C9_LOCKED":
        raise AssertionError("Candidate Flutter tab still exposed remote authority")


def memory_only(page):
    return page.evaluate(
        """() => ![...Object.keys(window.localStorage),
                     ...Object.keys(window.sessionStorage),
                     document.cookie].some(
            x => /iamina-web\.|iamina-wr1\./.test(x)
        ) && ![...Object.values(window.localStorage),
                ...Object.values(window.sessionStorage),
                document.cookie].some(
            x => /iamina-web\.|iamina-wr1\./.test(x)
        )"""
    )


def do_browser(name, browser_type, results):
    browser = browser_type.launch(
        headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage"]
        if name == "chromium" else [],
    )
    context = browser.new_context(viewport={"width": 390, "height": 844})
    a = context.new_page()
    b = context.new_page()
    try:
        a.set_viewport_size({"width": 390, "height": 844})
        b.set_viewport_size({"width": 1280, "height": 900})
        a.goto(ORIGIN + "/?lang=fr", wait_until="domcontentloaded", timeout=50000)
        b.goto(ORIGIN + "/?lang=ar", wait_until="domcontentloaded", timeout=50000)
        for page in (a, b):
            page.wait_for_function(
                "() => document.title === 'IAMINA_W02_C9_LOCKED'",
                timeout=70000,
            )
        if len(context.pages) != 2:
            raise AssertionError("Not two independent browser tabs")
        if state(a)["direction"] != "ltr" or state(b)["direction"] != "rtl":
            raise AssertionError("FR/AR probe document direction incorrect")
        results.append(name + ":2_tabs_fr_ar_booted_locked")

        click(a, "activate")
        click(b, "activate")
        until(a, "access", "true")
        until(b, "access", "true")
        results.append(name + ":both_synthetic_bearers_in_memory")

        # Race: A refresh request is pending while B logs out.
        click(a, "refresh")
        until(a, "refreshResult", "pending")
        click(b, "logout")
        until(b, "logoutResult", "confirmed")
        ensure_locked(b)
        try:
            ensure_locked(a)
        except BrowserTimeout as exc:
            raise AssertionError("Cross-tab logout failed without reload") from exc
        until(a, "refreshResult", "denied", timeout=15000)
        ensure_locked(a)
        results.append(name + ":stale_async_refresh_cannot_resurrect_a")

        click(a, "activate")
        click(b, "activate")
        until(a, "access", "true")
        until(b, "access", "true")
        click(b, "offline")
        until(b, "outage", "true")
        click(b, "logout")
        until(b, "logoutResult", "not_confirmed")
        ensure_locked(b)
        ensure_locked(a)
        results.append(name + ":offline_logout_clears_both_tabs_without_server_ack")

        a.reload(wait_until="domcontentloaded", timeout=50000)
        a.wait_for_function(
            "() => document.title === 'IAMINA_W02_C9_LOCKED'",
            timeout=70000,
        )
        ensure_locked(a)
        if not memory_only(a) or not memory_only(b):
            raise AssertionError("Candidate bearer/refresh reached browser storage")
        results.append(name + ":cold_reload_locked_and_no_persistent_token")
    finally:
        context.close()
        browser.close()


def main():
    report = {
        "result": "NOT_RUN",
        "scope": "actual compiled Flutter Web candidate C8 in 2 same-origin tabs",
        "backend": "SYNTHETIC_BROWSER_ONLY",
        "hosted_vercel": "NOT_RUN",
        "real_patient_data": "NONE",
        "browsers": [],
        "steps": [],
        "limitations": "No hosted OIDC, no actual Django refresh endpoint, no clinical UI."
    }
    try:
        with sync_playwright() as playwright:
            for name in ("chromium", "webkit"):
                do_browser(name, getattr(playwright, name), report["steps"])
                report["browsers"].append(name)
        report["result"] = "PASS_LOCAL_CHROME_WEBKIT_TWO_TABS"
    except Exception as exc:
        report["result"] = "FAIL"
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc).split("\n")[0][:180]
    finally:
        PROOF.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
    if report["result"] != "PASS_LOCAL_CHROME_WEBKIT_TWO_TABS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
