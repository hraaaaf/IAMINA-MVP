# MENA critical-path reconciliation — 2026-08-17

## Goal

Make the MENA pilot counter auditable from repository evidence, without inventing approvals or silently changing the canonical 32/41 numerator.

## Source-of-truth reconstruction

The MENA sovereignty reset at commit `38fca82a96006beb970e352ae0511d8538f9a166` contains the original forward checklists:

- P0-MENA-1: 12 checkbox occurrences (5 completed foundation + 7 remaining items).
- P0-MENA-2: 8 checkbox occurrences.
- P0-MENA-3: 6 checkbox occurrences.
- P0-MENA-4: 4 checkbox occurrences.
- Pilot safety/compliance: 12 checkbox occurrences.

That source exposes 42 checkbox occurrences, while later canonical ROADMAP versions report a 41-task MENA denominator. The exact historical de-duplication rule is not explicitly preserved in the current forward tracker, so this reconciliation does **not** change the 32/41 count.

A later detailed ROADMAP checkpoint at commit `7fca4aa2525c30fa7bc540b42a86953a9176d61f` provides the explicit expanded workstream checklists used during execution. It proves the 13-row Pilot Safety registry and the 7-row P0-MENA-4 benchmark registry that underlie the current percentage summaries.

## Verified completed work

### P0-MENA-1 — outbound AI/data egress

Canonical status: 100% complete.

All engineering requirements are covered through PRs #10–#15: payload contracts, semantic DLP, granular media consent, consent management API, processor policy registry, provider runtime isolation/resilience, typed failures, bounded timeouts and anti-bypass behavior.

### P0-MENA-2 — locale and safety

Canonical status remains 63% pending restricted human gates.

Verified progress:

- screen-by-screen RTL technical certification: PR #36;
- fingerprinted review workflow: PR #37;
- AI secondary review: PR #212, 70/70 cases and 8/8 parity tuples, explicitly non-human;
- English active-surface baseline: 16/16, closed through PR #228;
- Arabic orthographic hardening: PR #232;
- native-reviewed Darija lexicon batches: PRs #234, #235, #239;
- fail-closed Darija promotion contract: PR #244;
- exact high-severity Darija native review: PR #247, 36/36 exact runtime variants with explicit native outcomes;
- staged remediation: PR #255, 21 native-rejected runtime variants locked and four replacement candidates recorded but kept inactive;
- technical Darija parity matrix: PR #256, 2 channels × 3 input forms.

Still not proven closed:

- qualified clinical-human approval for enabled safety corpora;
- safety-owner / restricted approval required by the promotion contract;
- final restricted parity/runtime promotion approval;
- complete native-human approval for French, MSA and English as required by the human-review contract;
- pilot-country emergency wording approval where applicable.

No runtime promotion is authorized from the evidence above alone.

### P0-MENA-3 — sovereign authentication

Canonical status: 100% complete through PR #17.

### P0-MENA-4 — multimodal provider benchmark

Canonical status: 29%.

The detailed 7-row checkpoint proves why: two framework tasks are closed and five live/decision tasks remain.

Closed:

1. representative minimized/synthetic MENA evaluation sets;
2. deterministic scoring/evidence framework for privacy, residency, no-training/no-retention, MENA quality, safety, latency, availability and cost.

Prepared but **not closed**:

- text benchmark execution boundary: PR #19;
- STT benchmark execution boundary: PR #20;
- vision/OCR benchmark execution boundary: PR #21;
- readiness/cutover package: PR #22.

Remaining five benchmark outcomes:

1. benchmark text providers independently;
2. benchmark STT providers independently;
3. benchmark vision/OCR providers independently;
4. document the evidence-backed decision matrix and rejected alternatives;
5. approve provider cutover only after privacy, quality and human-review gates pass.

No live scores or provider ranking were found. These require current legal/processor evidence, credentials/environment, explicit paid/network authorization and human review.

### Pilot safety/compliance — exact remaining 3/13

Canonical status: 10/13 complete.

The historical 13-row checklist at `7fca4aa…`, combined with issue #30 closure through PR #230, identifies the three remaining gates exactly:

1. **Close Darija high-severity review.**  
   Native 36/36 evidence now exists, but qualified clinical-human, safety-owner/restricted parity and final runtime-promotion approval remain open. The 21 rejected variants are staged for atomic remediation, not yet changed in runtime.

2. **Approve the pilot consent matrix and processor/subprocessor register.**  
   Engineering gate prepared through PR #34. `audit_pilot_consent_governance --require-approved` must pass using current restricted CNDP, processor, transfer, contract, privacy and security evidence. No approval receipt was found.

3. **Approve Morocco cross-border/data-residency assumptions for the exact deployment.**  
   Engineering gate prepared through PR #35. `audit_pilot_data_residency --require-approved` must pass against a restricted manifest tied to the exact deployed SHA. No approved deployment manifest was found.

The former fourth blocker, reachable Git-history hygiene / issue #30, is closed through PR #230 with fresh-clone verification and Gate A 10/10.

## Accounting decision

Preserve until a deliberate re-baseline is approved:

- MENA numerator: **32**
- MENA denominator: **41**
- displayed completion: **~78%**

Do not increment the numerator for PRs #247/#255/#256: those PRs explicitly preserve clinical, safety-owner, parity and runtime-approval gates as open.

## Current executable critical path

### Immediately executable in-repo

- maintain the reconciled human-review gate and current external-approval handoff;
- use `docs/evaluation/DARIJA_HIGH_SEVERITY_CLINICAL_REVIEW_PACKET.md` for the qualified clinical-human review;
- once all restricted approvals exist, apply the staged Darija runtime delta atomically and recertify exact-head.

### Human / external evidence required

- qualified clinical-human receipt;
- safety-owner/restricted parity approval;
- CNDP/processor/subprocessor/foreign-transfer/privacy/security evidence;
- exact deployment residency manifest;
- provider credentials, budget/network authorization and current evidence for live multimodal benchmarks.

## Result

The official count remains 32/41, but the remaining work is now explicitly identified. Core engineering is largely complete; the real critical path is three Pilot Safety approvals plus five live/provider-decision outcomes, with Darija runtime remediation already staged behind the required human gates.
