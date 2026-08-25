# P4-FRUGAL — Pre-pilot evidence boundary

Date: 2026-08-25
Base audited: `main@e694b082d379ca3dea56babbab4a5184ddd9f8cd`

## Goal

Close every frugality claim that can be proven before real user traffic exists, while preventing synthetic/dev evidence from being mislabeled as observed production economics.

## Verified product state

IAMINA has not yet run a real-patient/user pilot that provides representative MAU, workload mix, storage occupancy, egress, provider billing, or paid-user conversion data. Existing evidence consists of repository tests/fixtures, controlled non-patient probes, CI evidence, and provider documentation.

Therefore a monthly ledger from a development/test PostgreSQL instance is not a substitute for production usage evidence and is not required as a pre-pilot closeout gate.

## Pre-pilot evidence that is valid now

- FRUG-0 instrumentation and durable privacy-safe ledger implementation can be certified structurally and with synthetic fixtures.
- FRUG-5 token/call budgets, deterministic zero-model routing, multilingual/safety regression tests, provider failure behavior, and controlled non-patient provider probes can be certified pre-pilot.
- FRUG-6 relational/media-storage contracts, lifecycle aggregation, egress fixtures and the absence/presence of retained object-storage paths can be certified pre-pilot.
- FRUG-9 scale-model mechanics and scenario envelopes at 1k/10k/50k/100k MAU can be certified as scenarios when every non-measured input is explicitly labelled `scenario` with provenance.
- Current provider prices/quotas may be pinned as dated external inputs; they are not observed IAMINA spend.

## Evidence that must remain deferred until a real pilot exists

- real MAU and interactions per MAU;
- real workload/modality mix and LLM-call rate per interaction;
- real p50/p95 token distributions from representative user traffic;
- real cache-hit/cached-token ratio when provider telemetry exposes it;
- real retained storage GB-month and egress GB;
- real provider/storage/infrastructure bill reconciliation;
- real cost per MAU / paying user / accepted safe answer;
- predicted-versus-observed reconciliation.

These are post-pilot validation gates, not blockers to pre-pilot engineering completion.

## Guardrail

No empty/dev ledger, synthetic fixture, controlled probe, provider price page, or scale scenario may be described as measured production economics. Missing observed evidence remains unavailable rather than zero.

## Success / proof

Success is reached when the roadmap and FRUG issues distinguish pre-pilot engineering certification from post-pilot economic validation, and no current engineering task is blocked solely on nonexistent production traffic.

Proof is this boundary plus the already-merged FRUG instrumentation/tests and issue-level evidence. No Vercel deployment is part of this closeout.
