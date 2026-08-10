from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
EXPECTED = "5f7fafd96adcf16b2ed16572910e9a23509696d1"
head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
if head != EXPECTED:
    raise SystemExit(f"stale product head: {head}")

# ROADMAP
roadmap = ROOT / "docs/ROADMAP.md"
text = roadmap.read_text()
replacements = [
    (
        "> **Last updated:** 2026-08-10 — P1-JOURNAL-7 Ramadan mode v2 is merged and 100% closed; P2-JOURNAL-8 Personal metabolic response is next.",
        "> **Last updated:** 2026-08-10 — P1-JOURNAL-7 is closed; P2-JOURNAL-8 Personal metabolic response is the active merge unit in PR #76.",
    ),
    (
        "| Journal metabolic-event redesign | 78% | 🟢 P1-JOURNAL-7 closed; P2-JOURNAL-8 next | P0-JOURNAL-1/2 + P1-JOURNAL-3/4/5/6/7 merged; PR #75; explicit Ramadan profile context, no fasting inference or fabricated medical defaults; UX 9.3/10; post-merge CI #1372 + drift #1184 green |",
        "| Journal metabolic-event redesign | 89% | 🟢 P2-JOURNAL-8 certified pre-merge | P0-JOURNAL-1/2 + P1-JOURNAL-3/4/5/6/7 merged; PR #76 deterministic personal-response patterns; exact-head CI #1380 + drift #1192 + PostgreSQL green; 24-view FR/AR UX 9.3/10; four specialist reviewers PASS; final docs-head recertification + merge/post-merge remain |",
    ),
    (
        "| P2-JOURNAL-8 | Personal metabolic response | ⬜ Planned | repeated-event associations with explicit evidence count/confidence; observational wording only; no invented causality/treatment advice |",
        "| P2-JOURNAL-8 | Personal metabolic response | 🟢 PR #76 merge unit | deterministic repeated observations only; explicit evidence count + distinct days + descriptive repetition grade; explicit positive context and post-meal facts only; 90-day synced scope; no causal/statistical/treatment claim; UX 9.3/10 |",
    ),
]
for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"ROADMAP anchor mismatch ({count}): {old[:100]!r}")
    text = text.replace(old, new, 1)

anchor = "P1-JOURNAL-7 is **100% closed**.\n\n\n\n---"
contract = '''P1-JOURNAL-7 is **100% closed**.\n\n### P2-JOURNAL-8 durable merge-unit contract\n\nPR #76 is the merge unit for Personal metabolic response. The Journal now computes deterministic, patient-scoped repeated-observation patterns from already-synchronized source logs; no derived pattern is persisted. Context patterns are eligible only from explicit positive patient-entered states (`stress=yes`, `activity=yes`, `illness=yes`, `sleep=bad`, explicit fatigue), and meal patterns require an explicit `post_meal` glycaemic context plus meal type. Historical `no/good/ok` values are never treated as a control cohort because older schemas may have materialized such defaults. Demo rows are excluded, the analysis window is bounded to 90 days, and insufficient repetition fails closed.\n\nEach visible pattern exposes its observation count, distinct-day count, pattern median, whole synced-window median and a **descriptive repetition grade**. That grade is product evidence density, not a probability, statistical significance test or clinical confidence score. The patient-facing contract explicitly states that an observed association does not establish cause and must not guide treatment or dosing. No predicted glucose, diagnosis, causal delta, treatment optimization, dose calculation or new AI/provider egress is introduced. API scope derives only from the authenticated `request.user.id`, and the UI states that only server-synchronized readings are analyzed.\n\nThe first real FR/AR max-density visual pass was rejected at **8.8/10** because three simultaneous pattern cards displaced Journal history too aggressively on `360×560`. The same LOT was remediated to show one strongest pattern by default with an explicit accessible disclosure for secondary patterns.\n\n**Pre-closeout evidence on product head `5f7fafd96adcf16b2ed16572910e9a23509696d1`:** canonical CI #1380 SUCCESS including PostgreSQL source-of-truth; migration drift #1192 SUCCESS; exact-head visual audit run `31384006870` SUCCESS with 24/24 FR/AR compact/expanded/insufficient renders across `1440×1000`, `768×1024`, `390×844` and `360×560`; artifact `9060989847`, digest `sha256:8a2db26d548f68e75f3938d793bde980ee865d0988770bc96b2e6dafae7514e3`; UX Auditor **9.3/10 PASS**; Clinical Safety, Security, Database/Migration and UX reviewers PASS. Canonical documentation changes make these anchors pre-closeout evidence, so exact-final-head CI + drift + visual recertification, reviewer re-anchoring, Release Certifier, expected-head merge and post-merge gates remain mandatory before the LOT is 100% closed.\n\n\n\n---'''
if text.count(anchor) != 1:
    raise SystemExit(f"ROADMAP contract insertion mismatch: {text.count(anchor)}")
text = text.replace(anchor, contract, 1)
roadmap.write_text(text)

# SPECS
specs = ROOT / "docs/SPECS.md"
text = specs.read_text()
anchor = "### Insulin logging v2 contract\n"
contract = '''### Personal metabolic response contract\n\n- personal-response patterns are deterministic derived observations recalculated from authoritative synchronized source logs; they are not persisted as clinical facts;\n- a context pattern may use only explicitly recorded positive states; historical `no`, `good` or `ok` values must not be treated as a negative/control cohort because older schemas may have materialized defaults;\n- a meal pattern requires an explicit `post_meal` measurement context plus an explicit meal type;\n- demo rows are excluded and patient scope is derived from the authenticated server identity, never a client-supplied patient identifier;\n- the analysis window is bounded to 90 days and the UI/API disclose that only server-synchronized logs are analyzed;\n- pattern eligibility requires at least 3 matching observations across at least 2 distinct days; insufficient repetition fails closed instead of producing a pattern;\n- each pattern may expose observation count, distinct-day count, its median glucose and the median of all eligible synchronized readings in the same window; no causal delta or predicted glucose is produced;\n- `limited` / `moderate` / `strong` describe only product repeatability/evidence density. They are not a probability, p-value, statistical significance test, diagnosis or clinical confidence score;\n- the patient-facing surface must state that association does not establish cause and must not guide treatment or dosing;\n- no pattern detector may produce treatment optimization, insulin-dose advice, diagnosis or autonomous clinical recommendation;\n- the Journal shows one strongest pattern by default and makes secondary patterns explicitly expandable so longitudinal context does not crowd out the primary history task.\n\n'''
if text.count(anchor) != 1:
    raise SystemExit(f"SPECS anchor mismatch: {text.count(anchor)}")
text = text.replace(anchor, contract + anchor, 1)
specs.write_text(text)

# MEDICAL DATA PLAN
med = ROOT / "docs/MEDICAL_DATA_PLAN.md"
text = med.read_text()
anchor = "### Ramadan profile context\n"
contract = '''### Personal metabolic response patterns\n\nPersonal metabolic response is a **deterministic detected-pattern layer**, not a diagnosis, prediction or treatment engine. Patterns are recalculated from source Journal logs and are not persisted as new clinical truth. Source edits/deletions therefore remain authoritative. Eligibility is deliberately conservative: at least 3 matching observations across at least 2 distinct days, within a maximum 90-day synchronized-data window. Demo rows are excluded.\n\nContext-derived patterns may use only explicit positive observations. Missing context remains unknown, and historical negative/neutral values such as `no`, `good` or `ok` must not become a synthetic control population because earlier schemas could materialize defaults. Meal patterns require an explicitly recorded `post_meal` measurement context and meal type.\n\nPatient-facing evidence may include observation count, distinct-day count, the median for matching observations and the median across all eligible synchronized readings in the same window. A product repetition grade may summarize evidence density, but it must be described as neither a probability nor statistical/clinical confidence. Comparing those descriptive medians must not be presented as a causal effect, treatment response estimate or predicted future glucose. No detector output may be converted into diagnosis, dose calculation, treatment optimization or autonomous advice. Insufficient evidence must fail closed.\n\n'''
if text.count(anchor) != 1:
    raise SystemExit(f"MEDICAL_DATA_PLAN anchor mismatch: {text.count(anchor)}")
text = text.replace(anchor, contract + anchor, 1)
med.write_text(text)
