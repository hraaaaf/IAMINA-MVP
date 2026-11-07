#!/usr/bin/env python3
"""W01: no-deployment static guard for IAMINA's two-project web topology.

Only asserts checked-in configuration. It neither contacts services nor proves
that project Root Directory, auth, API connectivity or Neon are configured.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_web_topology(root: Path = ROOT) -> list[str]:
    problems: list[str] = []
    def read_config(rel: str) -> dict:
        try:
            return json.loads((root / rel).read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            problems.append(f"{rel}: missing/invalid JSON ({type(exc).__name__})")
            return {}

    front = read_config("frontend/vercel.json")
    back = read_config("backend/vercel.json")
    monorepo = read_config("vercel.json")
    for name, config in [
        ("frontend/vercel.json", front),
        ("backend/vercel.json", back),
        ("vercel.json", monorepo),
    ]:
        if config.get("git", {}).get("deploymentEnabled") is not False:
            problems.append(f"{name}: automatic Git deployment must be disabled")

    if front.get("buildCommand") != "bash vercel_build.sh":
        problems.append("frontend: Flutter web build command is unexpected")
    if front.get("outputDirectory") != "build/web":
        problems.append("frontend: static SPA outputDirectory must be build/web")
    if front.get("functions"):
        problems.append("frontend: static SPA manifest must not define function overrides")
    rewrites = front.get("rewrites", [])
    expected_refresh = {
        "source": "/api/v1/auth/refresh",
        "destination": "/api/session-refresh.js",
    }
    expected_api = {"source": "/api/v1/:path*", "destination": "/api/index.js?forward=:path*"}
    expected_spa = {"source": "/(.*)", "destination": "/index.html"}
    # F09-C1: preserve a STRICT three-rule order. A broader rewrite ahead of
    # the dedicated refresh handler could leak refresh credentials through the
    # generic OIDC bridge, which has no cookie/rotation/CSRF authority.
    if rewrites != [expected_refresh, expected_api, expected_spa]:
        problems.append(
            "frontend: dedicated deny-only refresh handler must precede "
            "generic Preview API relay and SPA fallback"
        )
    if "api/index.py" not in back.get("functions", {}):
        problems.append("backend: expected Django WSGI api/index.py function absent")
    if back.get("outputDirectory") == "build/web":
        problems.append("backend: must not publish Flutter SPA as its output")
    if back.get("regions") != ["cdg1"]:
        problems.append("backend: cdg1 region baseline unexpectedly changed; review residency/latency before altering")
    if "cd frontend && bash vercel_build.sh" != monorepo.get("buildCommand"):
        problems.append("monorepo: root fallback build contract drift")
    try:
        entry = (root / "backend/api/index.py").read_text(encoding="utf-8")
        if "from amina.wsgi import application" not in entry or "app = application" not in entry:
            problems.append("backend: Django WSGI entrypoint contract drift")
        proxy = (root / "frontend/api/index.js").read_text(encoding="utf-8")
        for must in ("VERCEL_ENV !== 'preview'", "VERCEL_PROJECT_ID !== EXPECTED_PROJECT",
                     "x-vercel-oidc-token", "x-vercel-trusted-oidc-idp-token",
                     "IAMINA_REVIEW_PREVIEW_API_BASE_URL", "redirect: 'manual'"):
            if must not in proxy:
                problems.append("frontend: synthetic OIDC API bridge security contract missing " + must)
        build = (root / "frontend/vercel_build.sh").read_text(encoding="utf-8")
        if 'VERCEL_PROJECT_ID' not in build or 'API_BASE_URL' not in build:
            problems.append("frontend: project gate or API origin define missing")
        # W01's old stable alias is still accepted on legacy branches. W02
        # replaces it ONLY with a stricter immutable same-deployment host
        # resolver. Never accept a raw arbitrary URL or a fallback.
        w01_legacy = (
            'API_BASE_URL="https://iamina-review-git-preview-w0-'
            'f972e4-achraf-benmoussa-s-projects.vercel.app"'
        ) in build
        w02_immutable = (
            'source "$(dirname "$0")/scripts/w02_preview_origin.sh"' in build
            and 'API_BASE_URL="$(iamina_w02_preview_origin '
            in build
            and '"${VERCEL_URL:-}" "$VERCEL_PROJECT_ID" "$VERCEL_ENV")"' in build
        )
        if w02_immutable:
            helper = (root / "frontend/scripts/w02_preview_origin.sh").read_text(
                encoding="utf-8"
            )
            required = (
                'iamina_w02_preview_origin()',
                'prj_AYaUi32KTDHak8I7dmdQpDrqd8SI',
                '"preview"',
                'iamina-review-[a-z0-9]{9,12}',
                '-achraf-benmoussa-s-projects',
                'return 64',
            )
            if any(field not in helper for field in required):
                w02_immutable = False
        if not (w01_legacy or w02_immutable):
            problems.append(
                "frontend: Preview browser API must use the exact W01 "
                "alias or verified immutable W02 same-origin resolver"
            )
        if "DATABASE_URL" in build or "NEON_DATABASE_URL" in build:
            problems.append("frontend: SQL credentials must never appear in web build")
    except FileNotFoundError as exc:
        problems.append(f"required source missing: {exc.filename}")
    return problems


if __name__ == "__main__":
    errors = check_web_topology()
    if errors:
        for issue in errors:
            print(f"FAIL W01: {issue}")
        raise SystemExit(1)
    print("PASS W01 static topology guard: three Git deploy switches OFF, SPA/API separation and WSGI baseline.")
    print("LIMIT: this does NOT establish live Web/API/PostgreSQL connectivity, encrypted web storage or patient authorization.")
