# MENA external gates handoff — 2026-08-18

## Goal

Freeze the remaining MENA pilot blockers as explicit external gates, without inventing progress, approval, provider scores or deployment evidence.

## Canonical baseline

- Main before this handoff: `3e08ced43b5672e96e70b31af19cdef18cde443d`.
- Canonical MENA counter remains **32/41 (~78%)**.
- PR #315 reconciled the historical critical path and prepared the controlled clinical review packet.
- PR #316 recorded current CNDP/provider public evidence and marked the Moroccan legal-entity selection task **CLOSED_GRAY** for roadmap/engineering purposes.
- `CLOSED_GRAY` does not constitute CNDP approval and does not waive the real-patient release prerequisite to designate the actual controller when a pilot filing is prepared.

## Remaining external gate 1 — clinical / linguistic safety

Canonical tracker: issue #318 — `P0-MENA-2 — Qualified clinical review for enabled safety corpus`.

Prepared evidence already exists:

- PR #247: 36/36 exact high-severity Darija runtime variants received native-review outcomes;
- PR #255: 21 native-rejected variants locked; four replacement candidates staged but inactive;
- PR #256: technical parity matrix across two channels and three input forms;
- `docs/evaluation/DARIJA_HIGH_SEVERITY_CLINICAL_REVIEW_PACKET.md`;
- `docs/architecture/P0_MENA_2_HUMAN_REVIEW_GATE.md`.

Still required before closure:

1. qualified clinical-human approval of the exact fingerprinted enabled corpus;
2. safety-owner approval;
3. final parity approval across text, voice transcript, mixed-language and transliteration rows;
4. explicit disposition of the 21 rejected variants and four staged candidates;
5. restricted approval manifest tied to the exact candidate fingerprint;
6. passing `audit_safety_corpus_review --require-approved`.

Status: **BLOCKED_EXTERNAL_HUMAN**.

## Remaining external gate 2 — live multimodal providers

Canonical tracker: issue #319 — `P0-MENA-4 — Execute live multimodal provider benchmarks`.

Prepared engineering is already merged through PRs #18–#22. Current provider/CNDP evidence snapshot is in PR #316.

Still required:

1. live text-provider benchmark;
2. live STT-provider benchmark;
3. live vision/OCR-provider benchmark;
4. evidence-backed decision matrix and rejected alternatives;
5. cutover approval only after privacy, processor, region, quality and human-review gates pass.

No live score, ranking or provider cutover is currently claimable.

Status: **BLOCKED_EXTERNAL**.

## Remaining external gate 3 — Morocco compliance / deployment evidence

Canonical tracker: issue #320 — `Pilot Safety — CNDP, processor and Morocco residency approval gate`.

Prepared engineering already exists through PRs #34, #35, #103, #315 and #316.

Still required for real-patient release:

1. exact release/deployment SHA and topology;
2. exact runtime/database/cache/email/export/provider countries or regions;
3. approved patient notice and consent wording;
4. applicable CNDP health-data processing authorization/evidence;
5. applicable foreign-transfer authorization or approved basis for every actual external destination;
6. account-specific processor/DPA/subprocessor/retention/no-training/privacy/security evidence for enabled external providers;
7. restricted residency manifest tied to the exact deployed SHA;
8. passing `audit_pilot_consent_governance --require-approved` and `audit_pilot_data_residency --require-approved`.

The legal-entity selection subtask remains **CLOSED_GRAY** until real-patient release preparation; it must not be repeatedly reopened as engineering work.

Status: **BLOCKED_EXTERNAL_RELEASE**.

## Accounting

This handoff does not change the MENA numerator. The three issues above track unresolved evidence gates, not new roadmap tasks. Preserve **32/41 (~78%)** until an existing counted task is closed with observable proof and the canonical accounting rule is reconciled.

## Next exact

1. issue #318 first, because its qualified-human verdict can unlock the already-staged Darija remediation and final runtime recertification;
2. issue #319 only when provider/account/legal/network prerequisites are available;
3. issue #320 at real-patient release preparation against an exact deployment SHA.

## Non-claims

This document is a handoff. It is not clinical approval, CNDP/legal approval, processor approval, provider selection, deployment approval or pilot authorization.