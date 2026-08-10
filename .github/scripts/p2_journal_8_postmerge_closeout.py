from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
EXPECTED_MAIN = "a8ff01b9298f49133b3201d72086ade2643a9167"
head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
if head != EXPECTED_MAIN:
    raise SystemExit(f"stale main: {head}")

roadmap = ROOT / "docs/ROADMAP.md"
text = roadmap.read_text()
replacements = [
    (
        "> **Last updated:** 2026-08-10 — P1-JOURNAL-7 is closed; P2-JOURNAL-8 Personal metabolic response is the active merge unit in PR #76.",
        "> **Last updated:** 2026-08-10 — P2-JOURNAL-8 Personal metabolic response is merged and 100% closed; P2-JOURNAL-9 Post-save experience is next.",
    ),
    (
        "| Journal metabolic-event redesign | 89% | 🟢 P2-JOURNAL-8 certified pre-merge | P0-JOURNAL-1/2 + P1-JOURNAL-3/4/5/6/7 merged; PR #76 deterministic personal-response patterns; exact-head CI #1380 + drift #1192 + PostgreSQL green; 24-view FR/AR UX 9.3/10; four specialist reviewers PASS; final docs-head recertification + merge/post-merge remain |",
        "| Journal metabolic-event redesign | 89% | 🟢 P2-JOURNAL-8 closed; P2-JOURNAL-9 next | P0-JOURNAL-1/2 + P1-JOURNAL-3/4/5/6/7 + P2-JOURNAL-8 merged; PR #76 deterministic personal-response patterns; UX 9.3/10; post-merge CI #1383 + drift #1195 green |",
    ),
    (
        "| P2-JOURNAL-8 | Personal metabolic response | 🟢 PR #76 merge unit | deterministic repeated observations only; explicit evidence count + distinct days + descriptive repetition grade; explicit positive context and post-meal facts only; 90-day synced scope; no causal/statistical/treatment claim; UX 9.3/10 |",
        "| P2-JOURNAL-8 | Personal metabolic response | ✅ Closed | PR #76 merged as `a8ff01b9298f49133b3201d72086ade2643a9167`; post-merge CI #1383 + drift #1195 green; deterministic repeated observations, explicit evidence basis, 90-day synced scope, no causal/statistical/treatment claim; UX 9.3/10 |",
    ),
    (
        "**Pre-closeout evidence on product head `5f7fafd96adcf16b2ed16572910e9a23509696d1`:** canonical CI #1380 SUCCESS including PostgreSQL source-of-truth; migration drift #1192 SUCCESS; exact-head visual audit run `31384006870` SUCCESS with 24/24 FR/AR compact/expanded/insufficient renders across `1440×1000`, `768×1024`, `390×844` and `360×560`; artifact `9060989847`, digest `sha256:8a2db26d548f68e75f3938d793bde980ee865d0988770bc96b2e6dafae7514e3`; UX Auditor **9.3/10 PASS**; Clinical Safety, Security, Database/Migration and UX reviewers PASS. Canonical documentation changes make these anchors pre-closeout evidence, so exact-final-head CI + drift + visual recertification, reviewer re-anchoring, Release Certifier, expected-head merge and post-merge gates remain mandatory before the LOT is 100% closed.",
        "**Final certification evidence:** final pre-merge head `7f4003c4511c5eb27e9d01528a71269cc9511548`; canonical CI #1382 SUCCESS including PostgreSQL source-of-truth; migration drift #1194 SUCCESS; exact-final-head visual audit run `31384539082` SUCCESS with 24/24 FR/AR compact/expanded/insufficient renders across `1440×1000`, `768×1024`, `390×844` and `360×560`; artifact `9061180931`, digest `sha256:d9dbf85b7df8785b0af139a5a1ee63f6a98f55362d3575db3f1a9482bf66e006`; UX Auditor **9.3/10 PASS** after an initial 8.8/10 density rejection and remediation; Clinical Safety, Security, Database/Migration and UX reviewers FINAL PASS; Release Certifier CERTIFIED; PR #76 merged with expected-head locking as `a8ff01b9298f49133b3201d72086ade2643a9167`; post-merge CI #1383 and migration drift #1195 SUCCESS. P2-JOURNAL-8 is **100% closed**. P2-JOURNAL-9 is next.",
    ),
]
for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"ROADMAP anchor mismatch ({count}): {old[:110]!r}")
    text = text.replace(old, new, 1)
roadmap.write_text(text)
