#!/usr/bin/env python3
"""W01: real Chromium negative SSO/CORS probe for the exact synthetic Vercel Previews.

Uses a NEW empty browser profile. Only GET /api/v1/health and its browser-driven
OPTIONS preflight are intentionally exercised. No auth secrets, production URL,
patient account or clinical mutation. A PASS proves *denial without a Vercel SSO
session*; it does not prove authenticated Web -> API functionality.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

FRONT_URL = "https://iamina-review-goowsfx8j-achraf-benmoussa-s-projects.vercel.app/"
API_HEALTH_URL = (
    "https://iamina-certified-n3g9na2ou-achraf-benmoussa-s-projects.vercel.app"
    "/api/v1/health"
)
CDP_LIST = "http://127.0.0.1:9241/json/list"


def health_is_success(value: dict) -> bool:
    """Only Django's explicit status/db JSON pair qualifies as API access."""
    return (
        value.get("kind") == "http"
        and value.get("http_status") == 200
        and value.get("json") is True
        and value.get("status") == "ok"
        and value.get("db") == "ok"
    )


def deny_is_proven(case_results: list[dict], api_requests: list[dict]) -> bool:
    """A silent script failure, wrong page or zero network calls is not a PASS."""
    names = {item.get("case") for item in case_results}
    if names != {"no_cookies", "with_cookies", "preflight_with_cookies"}:
        return False
    if len(api_requests) < 3:
        return False
    return all(
        item.get("kind") in {"http", "fetch_error"}
        and not health_is_success(item)
        for item in case_results
    )


def _chrome() -> str:
    for name in ("google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    raise RuntimeError("CHROME_NOT_INSTALLED")


def _page() -> dict:
    end = time.monotonic() + 30
    while time.monotonic() < end:
        try:
            with urllib.request.urlopen(CDP_LIST, timeout=3) as response:
                pages = json.load(response)
            return next(item for item in pages if item.get("type") == "page")
        except (OSError, ValueError, StopIteration):
            time.sleep(0.25)
    raise RuntimeError("CHROME_DEVTOOLS_UNAVAILABLE")


def _evaluate(call, expr: str) -> object:
    result = call("Runtime.evaluate", {
        "expression": expr,
        "awaitPromise": True,
        "returnByValue": True,
    })
    if result.get("exceptionDetails"):
        raise RuntimeError("BROWSER_EVALUATION_FAILED")
    return result.get("result", {}).get("value")


def _js_case(case: str) -> str:
    credentials = "omit" if case == "no_cookies" else "include"
    preflight_headers = (
        '{"X-Iamina-W01-Synthetic-Probe": "1"}'
        if case == "preflight_with_cookies" else "{}"
    )
    return (
        "(async () => {"
        "try {"
        f"const r = await fetch({json.dumps(API_HEALTH_URL)}, {{"
        "'method':'GET', 'mode':'cors', 'cache':'no-store', "
        f"'credentials':{json.dumps(credentials)}, "
        f"'headers':{preflight_headers}}});"
        "const isJson = (r.headers.get('content-type') || '').includes('application/json');"
        "let status = null, db = null;"
        "if (isJson) {const body = await r.json();"
        "status = typeof body.status === 'string' ? body.status : null;"
        "db = typeof body.db === 'string' ? body.db : null;}"
        "return {kind:'http',http_status:r.status,json:isJson,status,db};"
        "} catch(e) {return {kind:'fetch_error',error_type:e?.name || 'Error'};}"
        "})()"
    )


def _browser_test() -> dict:
    from websocket import create_connection

    requests: list[dict] = []
    seen_api_request_ids: set[str] = set()
    api_status_codes: list[int] = []
    api_cors_errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="iamina-w01-protected-", ignore_cleanup_errors=True) as tmp:
        log_path = Path(tmp) / "chromium.log"
        with log_path.open("w", encoding="utf-8") as logfile:
            process = subprocess.Popen(
                [
                    _chrome(),
                    "--headless=new",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--remote-allow-origins=*",
                    "--remote-debugging-address=127.0.0.1",
                    "--remote-debugging-port=9241",
                    f"--user-data-dir={tmp}/profile",
                    "about:blank",
                ],
                stdout=logfile,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            try:
                page = _page()
                ws = create_connection(page["webSocketDebuggerUrl"], timeout=25)
                try:
                    counter = 0

                    def call(method: str, params: dict | None = None) -> dict:
                        nonlocal counter
                        counter += 1
                        this_id = counter
                        ws.send(json.dumps({"id": this_id, "method": method, "params": params or {}}))
                        while True:
                            event = json.loads(ws.recv())
                            event_method = event.get("method")
                            event_params = event.get("params", {})
                            if event_method == "Network.requestWillBeSent":
                                request = event_params.get("request", {})
                                if request.get("url", "").startswith(API_HEALTH_URL):
                                    # No headers, cookies, query params or body recorded.
                                    seen_api_request_ids.add(event_params.get("requestId", ""))
                                    requests.append({"method": request.get("method", "unknown")})
                                    redirect = event_params.get("redirectResponse") or {}
                                    if isinstance(redirect.get("status"), (int, float)):
                                        api_status_codes.append(int(redirect["status"]))
                            elif event_method == "Network.responseReceived":
                                if event_params.get("requestId") in seen_api_request_ids:
                                    response = event_params.get("response", {})
                                    if isinstance(response.get("status"), (int, float)):
                                        api_status_codes.append(int(response["status"]))
                            elif event_method == "Network.loadingFailed":
                                if event_params.get("requestId") in seen_api_request_ids:
                                    cors = event_params.get("corsErrorStatus") or {}
                                    if isinstance(cors.get("corsError"), str):
                                        api_cors_errors.append(cors["corsError"])
                            if event.get("id") == this_id:
                                if "error" in event:
                                    raise RuntimeError("CDP_COMMAND_FAILED")
                                return event.get("result", {})

                    call("Page.enable")
                    call("Network.enable")
                    call("Runtime.enable")
                    call("Page.navigate", {"url": FRONT_URL})
                    deadline = time.monotonic() + 40
                    front_origin = FRONT_URL.rstrip("/")
                    while time.monotonic() < deadline:
                        state = _evaluate(
                            call,
                            "({origin:location.origin,ready:document.readyState})",
                        )
                        if (
                            isinstance(state, dict)
                            and state.get("origin") == front_origin
                            and state.get("ready") == "complete"
                        ):
                            break
                        time.sleep(0.4)
                    else:
                        raise RuntimeError("FRONTEND_ORIGIN_NOT_LOADED")

                    cases = []
                    for name in ("no_cookies", "with_cookies", "preflight_with_cookies"):
                        result = _evaluate(call, _js_case(name))
                        if not isinstance(result, dict):
                            raise RuntimeError("NO_BROWSER_RESULT")
                        cases.append({"case": name, **result})

                    # Flush network events queued after final Runtime.evaluate.
                    call("Runtime.evaluate", {"expression": "true"})
                    return {
                        "verdict": "PASS_NEGATIVE_ONLY" if deny_is_proven(cases, requests) else "FAIL_OR_INCONCLUSIVE",
                        "frontend": "EXACT_SYNTHETIC_PREVIEW_LOADED",
                        "cases": cases,
                        "api_request_methods": [entry["method"] for entry in requests],
                        "api_response_statuses": api_status_codes,
                        "api_cors_errors": api_cors_errors,
                        "limit": "Fresh unauthenticated Chrome only; no authenticated browser session, no SSO/CORS repair evidence",
                    }
                finally:
                    ws.close()
            finally:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=5)


def main() -> int:
    proof = _browser_test()
    print(json.dumps(proof, indent=2, sort_keys=True))
    return 0 if proof["verdict"] == "PASS_NEGATIVE_ONLY" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        # A failed browser runner is NOT evidence that SSO denied the request.
        print(f"W01 protected Preview probe INCONCLUSIVE: {type(exc).__name__}", file=sys.stderr)
        raise SystemExit(2) from exc
