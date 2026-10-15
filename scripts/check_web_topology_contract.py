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
        problems.append("frontend: Vercel functions must not be embedded in static SPA project")
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
        build = (root / "frontend/vercel_build.sh").read_text(encoding="utf-8")
        if 'VERCEL_PROJECT_ID' not in build or 'API_BASE_URL' not in build:
            problems.append("frontend: project gate or API origin define missing")
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
