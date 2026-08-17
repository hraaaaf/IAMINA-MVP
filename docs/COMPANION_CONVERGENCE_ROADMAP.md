# IAMINA — Companion Convergence Roadmap

Status: ACTIVE
Baseline: `main@f6ba1e3758043be211a4e403f8e603080588cc72`

## Goal

Converge IAMINA's proactive intelligence and conversational bot onto one governed companion brain. Deterministic clinical/safety authority remains upstream; the LLM may narrate approved structured context but must not create a parallel medical, proactive, urgency, treatment or prioritization authority.

## Success criteria

- one patient-facing emergency response authority;
- one proactive attention/lifecycle authority;
- one governed Companion Context consumed by proactive UX and conversation;
- no diabetes-specific business logic in the chassis-level conversational orchestrator beyond module-provided context;
- generative output filtered before patient emission, including streaming;
- end-to-end conversation/proactivity evals cover longitudinal, negative, false-positive, boundary, multilingual, multi-turn and degraded-provider scenarios;
- no new diagnosis, prescription, dose, treatment optimization/change or autonomous medical authority.

## Invariants

1. `core.input_safety` classifies urgent/prescription-sensitive input before generative execution.
2. `core.emergency_response` is the only composer of patient-facing emergency text.
3. Clinical Twin / Evidence / Proactive state remain authoritative for longitudinal and proactive semantics.
4. Generative models never decide emergency status, clinical priority, treatment changes or proactive eligibility.
5. Patient scope comes from authenticated server context, never caller-supplied identity.
6. No Vercel deployment without explicit owner authorization.

## P0 — Safety Authority Convergence

Goal: converge patient-facing emergency authority and make medical streaming safe before emission.

Success:
- direct `companion.conversation.chat` and `stream_chat` delegate URGENT composition to `core.emergency_response`;
- local emergency copy/keyword authority in `companion/conversation.py` is removed;
- the final HTTP/SSE boundary replaces any compatibility-era urgent payload with `core.emergency_response` output before patient emission;
- the final HTTP/SSE boundary applies no-prescription filtering before yielding patient-visible generated tokens;
- route-local compatibility text, if still present internally, cannot become patient-visible authority;
- regression tests prove canonical emergency parity and pre-emission filtering.

Verified proof:
- PR #305 exact head `34ecd576c1a02ea40caac76c509dc613a04aa9ed`;
- exact-head CI #2738 SUCCESS: Ruff, import-linter, LLM gateway anti-bypass, AI egress anti-bypass, Bandit, OpenAPI, backend pytest, PostgreSQL full suite, Flutter analyze/tests, secret hygiene;
- exact-head Django migration drift #2550 SUCCESS;
- exact-diff safety review PASS with 0 unresolved review threads;
- expected-head merge `4d5c32eeaddfa4745495d71acad32db6659a7f93`;
- post-merge CI #2739 SUCCESS, including backend pytest, PostgreSQL full suite and Flutter analyze/tests;
- post-merge Django migration drift #2551 SUCCESS.

Status: CLOSED

## P1 — Proactivity Convergence

Goal: eliminate parallel conversational proactivity and route check-ins through the governed proactive lifecycle/attention budget.

Success:
- no independent `_inject_proactive_followup` authority;
- deterministic emotional memory remains available for reactive tone/context only and cannot emit an unsolicited assistant turn;
- `/proactive-insights/evaluate/` remains the single governed proactive delivery-budget authority;
- one non-urgent item per 24h attention budget remains authoritative;
- no duplicate patient-facing proactive message can bypass the governed attention lifecycle.

Verified proof:
- PR #308 exact head `3814fd3d213aeaa001bb665b889751da20c3c219`;
- runtime diff limited to `backend/companion/conversation.py` plus the dedicated P1 regression test;
- exact-head CI #2752 SUCCESS: Ruff, import-linter, LLM gateway anti-bypass, AI egress anti-bypass, Bandit, OpenAPI, backend pytest, PostgreSQL full suite, Flutter analyze/tests and secret hygiene;
- exact-head Django migration drift #2564 SUCCESS;
- 0 unresolved review threads and branch 0 behind `main` before merge;
- expected-head merge `b015b7aa6d18cf4ad4f6bf28a10d6b039b03dd60`;
- post-merge Django migration drift #2565 SUCCESS;
- post-merge CI #2753 was concurrency-cancelled after backend and Flutter had already passed; the only interrupted critical job was PostgreSQL full suite;
- the cancelled PostgreSQL job was re-run on the exact merge commit and completed SUCCESS, including migration validation and full PostgreSQL suite.

Status: CLOSED

## P2 — Governed Companion Context

Goal: expose one read-only, module-neutral Companion Context contract for both UX and chat narration.

Success:
- `DomainContext` remains the instant/session analytical contract;
- a distinct read-only `CompanionContext` carries governed longitudinal pattern/change/evidence/limitations/after-visit state;
- `BaseEngine` remains the single module→chassis clinical contract and exposes the backward-compatible read-only `companion_context()` hook;
- `core.companion.clinical` resolves longitudinal context only through the active engine selected by `ModuleRegistry`;
- diabetes adapts its certified `CompanionOverview` inside `EvidenceGuardedDiabetesEngine` rather than leaking diabetes services into the chassis;
- source provenance, uncertainty/limitations and longitudinal semantics survive module→chassis conversion;
- proactive delivery remains a separate command and this read-only path consumes no attention budget;
- no diagnosis, prescription, dose, treatment or new autonomous medical authority is added.

Verified proof:
- PR #313 exact head `ea35dc29d4df406859f46c35f01a5f56719cb3a1`;
- runtime diff limited to 5 files: shared CompanionContext contract, BaseEngine hook, chassis resolver, diabetes adapter and dedicated P2 regression tests;
- exact-head CI #2771 SUCCESS: Ruff, import-linter, LLM gateway anti-bypass, AI egress anti-bypass, Bandit, OpenAPI, backend pytest, PostgreSQL full suite, Flutter analyze/tests, secret hygiene and PR-size advisory;
- exact-head Django migration drift #2583 SUCCESS;
- 0 unresolved review threads and branch 0 behind `main` before merge;
- expected-head merge `f6ba1e3758043be211a4e403f8e603080588cc72`;
- post-merge Django migration drift #2584 SUCCESS;
- post-merge CI #2772 SUCCESS: backend pytest, PostgreSQL full suite, Flutter analyze/tests, architecture/security gates and secret hygiene all passed.

Status: CLOSED

## P3 — Narrator-Only Conversation Runtime

Goal: make the conversational bot a narrator/interface over approved Companion Context.

Success:
- conversational runtime consumes governed `CompanionContext` rather than reconstructing longitudinal meaning itself;
- LLM cannot add diagnosis, clinical priority, causality, prescription, dose or treatment action;
- module-neutral conversation orchestration;
- memory is clearly separated into conversational relationship memory vs clinical truth;
- degraded/offline fallbacks come from module contracts rather than diabetes-specific chassis copy;
- diabetes/TIR-specific fallback wording is removed from the chassis conversation layer.

Current direction:
- retain deterministic safety classification and canonical emergency composition ahead of any generative call;
- inject approved `CompanionContext` as bounded narration input with provenance/limitations preserved;
- keep `DomainContext` for instant session state where still needed, without allowing it to become a second longitudinal authority;
- remove diabetes-specific `_fallback_reply()` semantics from `companion/conversation.py` by routing fallback content through the active module contract;
- retain relationship/emotional memory only for reactive tone/history, never clinical truth or proactive eligibility.

Status: NEXT

## P4 — Conversation + Proactivity Evals

Goal: certify the converged brain end-to-end.

Hard scenarios:
- emergency parity JSON/SSE/direct call;
- prescription/dose refusal parity;
- streaming pre-emission safety;
- multi-turn contradiction and recovery;
- proactive cooldown/anti-repeat;
- longitudinal change semantics;
- missing/insufficient/contradictory evidence fail-closed;
- FR / EN / AR and approved dialect parity;
- provider failure/fallback;
- module isolation and no cross-patient leakage.

Status: NOT STARTED

## Completion rule

A phase is CLOSED only after its runtime/tests are exact-head certified, merged with expected-head protection, post-merge CI/drift are green, and this roadmap is synchronized to verified evidence.
