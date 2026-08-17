# IAMINA — Companion Convergence Roadmap

Status: ACTIVE
Baseline: `main@ac95b8ed772bea50660f285cfdba5490b3bb5a39`

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

Goal: remove duplicate emergency-response composition and make medical streaming safe before emission.

Success:
- direct `companion.conversation.chat` and `stream_chat` delegate URGENT composition to `core.emergency_response`;
- `/api/v1/ai/chat/stream` delegates URGENT composition to the same authority;
- local emergency copy/keyword authority in `companion/conversation.py` is removed;
- SSE sentence emission applies no-prescription filtering before yielding patient-visible tokens;
- regression tests prove canonical emergency parity and pre-emission filtering.

Proof:
- focused backend tests;
- full backend CI + PostgreSQL + migration drift;
- exact-head review/certification before merge.

Status: IN PROGRESS

## P1 — Proactivity Convergence

Goal: eliminate parallel conversational proactivity and route check-ins through the governed proactive lifecycle/attention budget.

Success:
- no independent `_inject_proactive_followup` authority;
- emotional follow-up, if retained, is represented as a governed non-clinical Companion suggestion class/state;
- one anti-repeat/cooldown authority;
- no duplicate patient-facing proactive message can bypass the governed attention lifecycle.

Status: NOT STARTED

## P2 — Governed Companion Context

Goal: expose one read-only, module-neutral Companion Context contract for both UX and chat narration.

Success:
- conversational runtime consumes governed pattern/change/evidence/suggestion context rather than reconstructing parallel clinical meaning from raw diabetes services;
- source provenance, uncertainty and limitations survive into narration input;
- chassis does not depend directly on diabetes models/services for clinical semantics.

Status: NOT STARTED

## P3 — Narrator-Only Conversation Runtime

Goal: make the conversational bot a narrator/interface over approved Companion Context.

Success:
- LLM cannot add diagnosis, clinical priority, causality, prescription, dose or treatment action;
- module-neutral conversation orchestration;
- memory is clearly separated into conversational relationship memory vs clinical truth;
- degraded/offline fallbacks come from module contracts rather than diabetes-specific chassis copy.

Status: NOT STARTED

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