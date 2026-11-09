#!/usr/bin/env python3
"""W01-B: inspect a sanitized *historical* cloud evidence snapshot, never deploy.

This is an offline anti-false-green review helper, NOT an attestation of live
Vercel configuration, database routing, patient security or approval.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "docs/assessments/w01b-2026-10-16-sanitized-cloud-inventory.json"

# Do not commit or print DSNs, credentials or decrypted environment values.
SECRET_PATTERNS = (
    re.compile(r"postgres(?:ql)?://", re.IGNORECASE),
    re.compile(r"https?://[^\s/]*:[^\s/@]+@", re.IGNORECASE),
)


def evaluate(evidence: dict) -> list[str]:
    """Return only source-specific blockers; nothing returned is deployment GO."""
    raw = json.dumps(evidence, sort_keys=True)
    if any(pattern.search(raw) for pattern in SECRET_PATTERNS):
        return ["SECRET_MATERIAL_IN_EVIDENCE: sanitized metadata only"]
    problems: list[str] = []

    def must(condition: bool, message: str) -> None:
        if not condition:
            problems.append(message)

    must(bool(evidence.get("snapshot_date")), "MISSING_DATED_EVIDENCE")
    must(bool(evidence.get("github_main_sha")), "MISSING_GITHUB_MAIN_SHA")

    vercel = evidence.get("vercel") or {}
    front = vercel.get("frontend") or {}
    back = vercel.get("backend") or {}
    must(front.get("id") == "prj_AYaUi32KTDHak8I7dmdQpDrqd8SI", "FRONTEND_PROJECT_NOT_VERIFIED")
    must(back.get("id") == "prj_Pn9FnyconF3h2w9gOU74iV98kJoU", "BACKEND_PROJECT_NOT_VERIFIED")
    must(front.get("root_directory_verified") is True, "FRONTEND_ROOT_DIRECTORY_UNVERIFIED")
    must(back.get("root_directory_verified") is True, "BACKEND_ROOT_DIRECTORY_UNVERIFIED")
    must(front.get("release_candidate_verified") is True, "FRONTEND_RELEASE_ARTIFACT_UNVERIFIED")
    must(back.get("release_candidate_verified") is True, "BACKEND_RELEASE_ARTIFACT_UNVERIFIED")
    must(back.get("iamina_env_declared") is True, "BACKEND_IAMINA_ENV_NOT_DECLARED")
    must(back.get("preview_db_isolated_verified") is True, "PREVIEW_PRODUCTION_DB_ISOLATION_UNVERIFIED")
    must("DATABASE_URL" in back.get("declared_env_names", []), "BACKEND_DATABASE_URL_NOT_DECLARED")
    must(evidence.get("github_main_sha") == front.get("production_target_commit"),
         "CURRENT_FRONTEND_DEPLOYMENT_NOT_MAIN_SHA")
    must(evidence.get("github_main_sha") == back.get("production_target_commit"),
         "CURRENT_BACKEND_DEPLOYMENT_NOT_MAIN_SHA")

    neon = evidence.get("neon") or {}
    prod = neon.get("production") or {}
    synthetic = neon.get("synthetic") or {}
    must(prod.get("project_id") == "square-sun-82359137", "NEON_PRODUCTION_PROJECT_UNVERIFIED")
    must(prod.get("branch_protected") is True, "NEON_PRODUCTION_BRANCH_UNPROTECTED")
    must(prod.get("network_and_processors_approved") is True,
         "NEON_PRODUCTION_NETWORK_PROCESSORS_NOT_APPROVED")
    must(prod.get("public_connections_blocked") is True,
         "NEON_PUBLIC_CONNECTION_EXPOSURE_NEEDS_REVIEW")
    must(synthetic.get("project_id") == "noisy-truth-00115950"
         and synthetic.get("project_id") != prod.get("project_id"),
         "SYNTHETIC_NEON_NOT_PROVEN_SEPARATE")
    must(synthetic.get("read_only_query_passed") is True
         and str(synthetic.get("server_version_num", "")).startswith("16"),
         "SYNTHETIC_NEON_PG16_READ_ONLY_PROBE_UNVERIFIED")
    must(synthetic.get("vercel_to_neon_verified") is True, "VERCEL_TO_NEON_ROUTING_UNVERIFIED")

    proofs = evidence.get("remaining_proofs") or {}
    for item in (
        "live_web_api_postgres", "migration_restore_rollback",
        "patient_A_B_A_offline", "local_vault_encryption_keys_recovery",
        "W02_human_approval", "W14_clinical_legal_security_approval",
    ):
        must(proofs.get(item) is True, f"UNPROVEN_{item.upper()}")

    # External attestation, candidate freeze, and explicit release approval
    # remain separate even when all snapshot metadata fields look favourable.
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, default=DEFAULT)
    parser.add_argument(
        "--assert-no-go", action="store_true",
        help="CI: pass only when the snapshot still explicitly blocks release",
    )
    args = parser.parse_args()
    data = json.loads(args.inventory.read_text(encoding="utf-8"))
    problems = evaluate(data)
    print("IAMINA W01-B: STATIC SNAPSHOT ONLY; NOT A LIVE PROD AUTHORIZATION")
    for problem in problems:
        print("BLOCKER:", problem)
    print("STATUS:", "NO_GO" if problems else "TECHNICAL_SNAPSHOT_REVIEW_ONLY")
    if args.assert_no_go:
        return 0 if problems else 1
    return 2 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
