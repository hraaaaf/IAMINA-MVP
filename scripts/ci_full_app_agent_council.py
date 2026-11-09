#!/usr/bin/env python3
"""Read-only 15-scope IAMINA evidence discovery, NOT autonomous AI subagents."""
from __future__ import annotations

import argparse
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ROLES = {
    "ia01-architecture": [("Flutter frontend", "frontend/pubspec.yaml", r"flutter:"), ("Django backend", "backend/manage.py", r"django")],
    "ia02-clinical-safety": [("Clinical authority contract", "docs/COMPANION_INTELLIGENCE_CONTRACT.md", r"deterministic|clinical")],
    "ia03-diabetes-clinical": [("Diabetes backend module", "backend/diabetes", None), ("Diabetes evidence skill", ".skills/diabetes-evidence-intelligence/SKILL.md", r"source|evidence")],
    "ia04-cgm-metrics": [("Patient log model", "frontend/lib/data/drift/database.dart", r"LogEntries|logEntries"), ("Glucose safety specialty", ".skills/diabetes-clinical-reasoning/SKILL.md", r"glucose|glycem")],
    "ia05-medication": [("Treatment declarations", "frontend/lib/data/drift/patient_treatment_declaration_store.dart", r"declaration|treatment"), ("No dosing authority", "AGENTS.md", r"dose advice|dose calculation")],
    "ia06-nutrition": [("Food pictogram directory", "frontend/assets/food/pictograms/v1", None), ("Evidence controls", ".skills/diabetes-evidence-intelligence/SKILL.md", r"evidence")],
    "ia07-mena-language": [("Multilingual safety skill", ".skills/mena-clinical-linguistic-safety/SKILL.md", r"Arabic|Darija|MENA"), ("App-lock localized copy", "frontend/lib/core/localization/app_lock_localized_copy.dart", r"fr|ar|en")],
    "ia08-security-privacy": [("Fail-closed app lock", "frontend/lib/services/app_lock_service.dart", r"recoveryRequired"), ("Clinical transport gate", "frontend/lib/services/api_client.dart", r"canSyncClinicalData")],
    "ia09-data-offline": [("Patient scoped Drift vault", "frontend/lib/data/drift/database.dart", r"forPatientVault"), ("Scoped patient backup", "frontend/lib/data/drift/local_backup.dart", r"exportVaultJson")],
    "ia10-companion-ai": [("Companion authority contract", "docs/COMPANION_INTELLIGENCE_CONTRACT.md", r"generative|provider|clinical"), ("Egress privacy module", "backend/core/phi_privacy.py", r"privacy|redact|phi")],
    "ia11-qa-verification": [("Flutter app lock unit tests", "frontend/test/services/app_lock_service_test.dart", r"test\("), ("CI workflows", ".github/workflows", None)],
    "ia12-ux-accessibility": [("Consent screen", "frontend/lib/features/auth/consent_screen.dart", r"Widget|Consent"), ("UX review skill", ".skills/ux-ui-certification/SKILL.md", r"viewport|BEFORE|AFTER")],
    "ia13-release-ops": [("Vercel build contract", "frontend/vercel_build.sh", r"VERCEL|flutter"), ("Release certification skill", ".skills/release-certification/SKILL.md", r"release|CI")],
    "ia14-regulatory-qms": [("Contributing clinical gates", "docs/CONTRIBUTING.md", r"privacy|clinical"), ("Roadmap source", "docs/ROADMAP.md", r"P5|pilot|roadmap")],
    "ia15-adversarial": [("Safety test non-bypass", "frontend/test/services/app_lock_service_test.dart", r"D10-B"), ("Issue evidence governance", "docs/QUALITY_SCORING_POLICY.md", r"ADVERSARIAL|score")],
}

def probe(label: str, path: str, regex: str | None) -> dict:
    target = ROOT / path
    if not target.exists():
        return {"control": label, "path": path, "status": "NOT_FOUND", "line": None}
    if target.is_dir():
        return {"control": label, "path": path, "status": "PATH_EXISTS_NOT_A_TEST", "line": None}
    try:
        lines = target.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return {"control": label, "path": path, "status": "UNREADABLE", "line": None}
    if not regex:
        return {"control": label, "path": path, "status": "SOURCE_PRESENT", "line": None}
    for i, line in enumerate(lines, 1):
        if re.search(regex, line, flags=re.IGNORECASE):
            return {"control": label, "path": path, "status": "PATTERN_OBSERVED_NOT_CERTIFIED", "line": i}
    return {"control": label, "path": path, "status": "NOT_OBSERVED_REVIEW_REQUIRED", "line": None}

def source_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return os.environ.get("IAMINA_AUDIT_SOURCE_SHA", "UNKNOWN")

def audit_one(role: str, output_dir: Path) -> dict:
    if role not in ROLES:
        raise ValueError(role)
    profile = ROOT / ".github" / "agents" / f"iamina-{role}.md"
    evidence = [probe(k, p, pattern) for k, p, pattern in ROLES[role]]
    profile_valid = False
    if profile.is_file():
        text = profile.read_text(encoding="utf-8")
        profile_valid = text.startswith("---\n") and f"name: iamina-{role}" in text and "description:" in text
    result = {
        "role": role,
        "audit_mode": "DETERMINISTIC_STATIC_PROBE_NOT_LLM_SUBAGENT",
        "agent_session_id": None,
        "source_sha": source_sha(),
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "profile_valid": profile_valid,
        "observations": evidence,
        "outcome": "EVIDENCE_DISCOVERY_ONLY_NOT_CERTIFIED",
        "unresolved_gates": ["specialist_llm_subagent_session_not_executed", "human_clinical_privacy_regulatory_gates_not_signed"],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{role}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{role}: profile={'OK' if profile_valid else 'MISSING'}; " +
          ", ".join(f"{e['control']}={e['status']}" for e in evidence), flush=True)
    return result

def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--role", choices=tuple(ROLES))
    group.add_argument("--all", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/full-app-council")
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if args.role:
        result = audit_one(args.role, out)
        return 0 if result["profile_valid"] else 2
    errors = []
    for role in ROLES:
        # Run each domain in its own process; these are static checks, not model sessions.
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--role", role, "--output-dir", str(out)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        print(proc.stdout, end="")
        if proc.returncode:
            errors.append({"role": role, "exit": proc.returncode, "stderr": proc.stderr[-400:]})
    docs = [json.loads((out / f"{role}.json").read_text(encoding="utf-8")) for role in ROLES if (out / f"{role}.json").exists()]
    report = {
        "roles_expected": len(ROLES),
        "roles_executed_deterministic": len(docs),
        "llm_subagents_executed": 0,
        "source_sha": source_sha(),
        "profile_errors": errors,
        "finding_counts": {
            "not_found": sum(x["status"] == "NOT_FOUND" for d in docs for x in d["observations"]),
            "review_required": sum(x["status"] == "NOT_OBSERVED_REVIEW_REQUIRED" for d in docs for x in d["observations"]),
        },
        "release_verdict": "NOT_CERTIFIED",
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "council-summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report), flush=True)
    return 1 if len(docs) != len(ROLES) or errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
