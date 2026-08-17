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

That source therefore exposes 42 checkbox occurrences, while later canonical ROADMAP versions report a 41-task MENA denominator. The current repository does not explicitly preserve the historical de-duplication rule that converts those 42 occurrences into 41 counted tasks. Therefore this reconciliation does **not** change the denominator or numerator until that accounting rule is explicitly frozen.

## Verified completed work

### P0-MENA-1 — outbound AI/data egress

Canonical status: 100% complete.

All original engineering requirements are covered through PRs #10–#15: payload contracts, semantic DLP, granular media consent, consent management API, processor policy registry, provider runtime isolation/resilience, typed failures, bounded timeouts and anti-bypass behavior.

### P0-MENA-2 — locale and safety

Canonical status remains 63% pending restricted human gates.

Verified technical/native progress beyond the older human-review document:

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

Still not proven closed in repository evidence:

- qualified clinical-human approval for every enabled locale corpus;
- safety-owner / restricted approval required by the promotion contract;
- final restricted parity/runtime promotion approval;
- complete native-human approval for French, MSA and English as required by `P0_MENA_2_HUMAN_REVIEW_GATE.md`;
- pilot-country emergency wording approval where required.

No runtime promotion is authorized from the evidence above alone.

### P0-MENA-3 — sovereign authentication

Canonical status: 100% complete through PR #17.

### P0-MENA-4 — multimodal provider benchmark

Canonical status: 29% preparation progress; live evaluation remains externally gated.

Verified complete preparation:

- permanent synthetic multimodal benchmark framework: PR #18;
- text execution path: PR #19;
- STT execution path: PR #20;
- vision/OCR execution path: PR #21;
- readiness/cutover package: PR #22.

Not found / not claimable:

- live network benchmark scores for text providers;
- live STT provider scores;
- live vision/OCR provider scores;
- evidence-backed final provider ranking;
- approved production cutover.

These require current provider/legal evidence, credentials/environment, explicit paid/network authorization and human review. No scores may be fabricated.

### Pilot safety/compliance

Canonical status: 10/13 explicit gates complete.

Verified closeout includes issue #30 reachable-history remediation through PR #230, with fresh-clone history verification and Gate A at 10/10.

The remaining canonical forward summary is restricted compliance/deployment approvals plus human linguistic/provider evidence. The current forward ROADMAP no longer retains a stable row-by-row 13-gate registry, so this document does not invent names for the three unresolved gates beyond evidence-backed descriptions.

## Accounting decision

Until a stable de-duplication map is reconstructed or explicitly re-baselined, preserve:

- MENA numerator: **32**
- MENA denominator: **41**
- displayed completion: **~78%**

Do not increment the numerator for PRs #247/#255/#256 merely because substantial work was completed: those PRs explicitly preserve clinical, safety-owner, parity and runtime-approval gates as open.

## Current executable critical path

1. Prepare a controlled clinical-human review packet tied to the exact current safety-corpus fingerprint and runtime inventory.
2. Obtain qualified clinical-human review evidence.
3. Obtain safety-owner/restricted approval and parity approval.
4. Only then apply the already-staged Darija runtime remediation atomically and recertify.
5. Execute live provider benchmarks only after current legal/processor evidence, credentials, budget/network authorization and human-review prerequisites are satisfied.
6. Close remaining pilot compliance/deployment approvals before any real-patient enablement.

## Result

The 32/41 figure remains the official canonical count, but its historical arithmetic is not sufficiently self-documenting. Product engineering is materially further advanced than the percentage suggests; the unresolved work is now dominated by controlled human approvals, live provider evidence and compliance/deployment gates rather than missing core product implementation.
