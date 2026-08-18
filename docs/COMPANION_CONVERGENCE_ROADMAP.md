# IAMINA — Companion Convergence Roadmap

Status: ACTIVE
Baseline: `main@a9c54858781e901389bbb476c647e523b92fc907`

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

Verified proof:
- PR #305 exact head `34ecd576c1a02ea40caac76c509dc613a04aa9ed`;
- exact-head CI #2738 SUCCESS;
- exact-head Django migration drift #2550 SUCCESS;
- expected-head merge `4d5c32eeaddfa4745495d71acad32db6659a7f93`;
- post-merge CI #2739 SUCCESS;
- post-merge Django migration drift #2551 SUCCESS.

Status: CLOSED

## P1 — Proactivity Convergence

Goal: eliminate parallel conversational proactivity and route check-ins through the governed proactive lifecycle/attention budget.

Verified proof:
- PR #308 exact head `3814fd3d213aeaa001bb665b889751da20c3c219`;
- exact-head CI #2752 SUCCESS;
- exact-head Django migration drift #2564 SUCCESS;
- expected-head merge `b015b7aa6d18cf4ad4f6bf28a10d6b039b03dd60`;
- post-merge Django migration drift #2565 SUCCESS;
- post-merge CI #2753 concurrency interruption was completed by rerunning the interrupted PostgreSQL job on the exact merge SHA, which passed.

Status: CLOSED

## P2 — Governed Companion Context

Goal: expose one read-only, module-neutral Companion Context contract for both UX and chat narration.

Verified proof:
- PR #313 exact head `ea35dc29d4df406859f46c35f01a5f56719cb3a1`;
- exact-head CI #2771 SUCCESS;
- exact-head Django migration drift #2583 SUCCESS;
- expected-head merge `f6ba1e3758043be211a4e403f8e603080588cc72`;
- post-merge CI #2772 SUCCESS;
- post-merge Django migration drift #2584 SUCCESS.

Status: CLOSED

## P3 — Narrator-Only Conversation Runtime

Goal: make the conversational bot a narrator/interface over approved Companion Context.

Implemented:
- conversation consumes `DomainContext` for bounded instant/session context and fresh governed `CompanionContext` for longitudinal narration;
- `CompanionContext` provenance and limitations are serialized into narrator input;
- chassis `conversation.py`, `state.py` and `tone.py` no longer own TIR/CV clinical threshold semantics;
- relationship/emotional memory remains reactive tone/history only and generated output cannot become durable clinical truth;
- degraded fallback is routed through `BaseEngine.offline_fallback()`, with diabetes-specific wording owned by the diabetes engine;
- narrator prompts are module-neutral and prohibit diagnosis, causality, clinical priority, prescription, dose, treatment action and proactive-eligibility authority;
- deterministic emergency and prescription-sensitive input guards remain ahead of generative execution.

Verified proof before merge:
- PR #317 exact head `5e6c1944d972e9a035ea11bf1985de69a29378a7`;
- exact-head CI #2798 SUCCESS;
- exact-head Django migration drift #2610 SUCCESS;
- 0 unresolved review threads and branch 0 behind `main` before merge;
- expected-head merge `852d66bc51d42749cefb3381b07f18a18ae2ff28`;
- `main` was verified to point exactly at that merge after merge.

Open proof:
- post-merge GitHub Actions push-run evidence for `852d66bc51d42749cefb3381b07f18a18ae2ff28` is not retrievable through the available connector;
- the prior draft closeout PR #322 was exact-head CI/drift green but was closed unmerged as superseded by this consolidated closeout.

Status: MERGED — POST-MERGE CI/DRIFT PROOF PENDING

## P4 — Conversation + Proactivity Evals

Goal: certify the converged brain end-to-end.

Certified/reused evidence map:
- emergency parity JSON/SSE/direct and streaming pre-emission filtering: existing P0 regression suites;
- prescription/no-prescription boundaries: existing medical-safety/input-safety suites;
- provider timeout/unavailable/internal failure, stream cancellation and partial-stream failure: `test_ai_provider_failures.py`;
- proactive 24h attention budget, anti-repeat, next-item cooldown behavior and patient scoping: `test_p2_proactive.py`;
- proactive reactivation fail-closed: `test_p2_proactive_reactivation.py`;
- longitudinal/negative/false-positive/boundary dimensions: existing L/N/F/B evaluation corpus and companion suites;
- evidence ceiling / insufficient evidence / module and patient isolation: existing P0/P2 suites.

New P4 runtime coverage:
- explicit multi-turn contradiction rule: the current patient message may correct conversational history for patient-declared facts, but cannot replace governed clinical context;
- narrator governance parity for FR / EN / AR / ar-MA;
- multi-turn correction/recovery prompt certification.

Verified proof before merge:
- PR #325 exact head `da04aaa7f89b515b1529d41c3c74014213b73cd1`;
- exact-head CI #2825 SUCCESS;
- exact-head Django migration drift #2637 SUCCESS;
- PR mergeable, 0 unresolved review threads and branch 0 behind `main` before merge;
- expected-head merge `a9c54858781e901389bbb476c647e523b92fc907`.

Open proof:
- post-merge GitHub Actions push-run evidence for `a9c54858781e901389bbb476c647e523b92fc907` is not retrievable through the available connector.

Status: MERGED — POST-MERGE CI/DRIFT PROOF PENDING

## Completion rule

A phase is CLOSED only after its runtime/tests are exact-head certified, merged with expected-head protection, post-merge CI/drift are green, and this roadmap is synchronized to verified evidence.
