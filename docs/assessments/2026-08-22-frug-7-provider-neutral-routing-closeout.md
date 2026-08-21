# FRUG-7 — Provider-neutral GPT-OSS routing closeout

Date: 2026-08-22  
Tracking: #430 / parent roadmap #422

## Status

**CLOSED — provider-neutral routing engineering scope certified with exact-tree merge equivalence.**

This closeout certifies provider abstraction, fail-closed governance, bounded failure behavior and synthetic multilingual benchmark evidence. It does **not** approve Groq or any external provider for real patient-data egress.

## Goal

Allow IAMINA to switch/disable text inference providers without changing clinical/domain code or weakening processor governance or deterministic clinical authority.

## Delivered

- Config-driven DeepSeek/Qwen/Groq provider specifications behind a generic OpenAI-compatible adapter.
- Explicit processor-policy keys; Groq/DeepSeek/Qwen remain governed and fail closed when unapproved.
- Removal of implicit Gemini quota → Kimi cascade; network fallback requires explicit configuration/governance.
- Adapter-level timeout / HTTP 429 / HTTP 5xx normalization with one outbound attempt and no hidden retry.
- Groq/GPT-OSS candidate registered for synthetic evaluation without patient-data approval.
- Bounded FR/AR/Darija synthetic benchmark under controlled pricing and explicit spend ceiling.
- Deterministic clinical/safety authority remains outside provider adapters.

## Exact-head proof

Final tested FRUG-7D head: `db78a814ca41628ca922ad2168f4fbf9fa1e2695`.

- Standard CI run `32475090719` — success.
- Django migration drift run `32475090773` — success.
- Dedicated FRUG-7 multilingual benchmark run `32475090859` — success.
- Benchmark artifact `frug7-groq-multilingual`, artifact id `9447578570`, digest `sha256:f87b9a0f687e513662dbff55a8c0713a654d411dfae34827812bf2e34e9d03bb`.
- Synthetic/minimized inputs only; `patient_data=false`.
- Machine safety/parity scores: FR 100, AR 100, ar-MA-Latn 100; parity spread 0.
- Provider-reported usage: 484 input + 400 output = 884 total tokens.
- Conservative measured benchmark cost: 315 microusd = $0.000315 total.
- Security Auditor — PASS.
- Clinical Safety Reviewer — PASS for FRUG-7D scope.
- MENA Clinical-Linguistic AI secondary review — PASS, scope-limited only; not native/human approval.
- Release Certifier — `CERTIFIED_WITH_NON_BLOCKING_FINDINGS`.

## Merge equivalence

PR #461 was squash-merged with expected-head lock on `db78a814ca41628ca922ad2168f4fbf9fa1e2695`.

- Tested head tree SHA: `d8940680ebe619d95d70d054f9cdbf946f9c9cad`.
- Merge SHA: `3bcab4397d63d45c67b4679d095d7a689e1d986e`.
- Merge tree SHA: `d8940680ebe619d95d70d054f9cdbf946f9c9cad`.
- Tree identity: exact.

The available GitHub connector does not expose push-triggered runs for merge SHAs. No hidden run state is inferred; closure relies on the tested exact tree being byte-identical to the squash-merged tree, plus subsequent green descendant CI in FRUG-8.

## Provider-governance residuals outside engineering closure

Groq/GPT-OSS remains **PENDING for real patient data**. Before any patient-data egress, IAMINA still requires real evidence for:

- processor/subprocessor contracts;
- CNDP/legal transfer basis;
- processing region/data residency;
- account-level ZDR configuration;
- retention and training-use controls;
- production purpose/modality allowlist;
- any required native/human linguistic or clinical review.

These are release/provider-approval gates, not proof gaps in the provider-neutral adapter architecture. No provider approval is asserted by closing FRUG-7.

## Scope boundaries

- No real-patient egress approval.
- No clinical authority moved into LLM/provider code.
- No production key committed.
- No Vercel deployment.
- FRUG lane remains parallel to canonical MENA `32/38` arithmetic.
