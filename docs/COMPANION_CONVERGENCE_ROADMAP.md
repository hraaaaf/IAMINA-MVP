# IAMINA — Companion Convergence Roadmap

Status: CLOSED
Baseline: `main@687c5405adb4eab97024ad95e0e8217f25d9d084`

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

Verified proof:
- PR #317 exact head `5e6c1944d972e9a035ea11bf1985de69a29378a7`;
- exact-head CI #2798 SUCCESS;
- exact-head Django migration drift #2610 SUCCESS;
- 0 unresolved review threads and branch 0 behind `main` before merge;
- expected-head merge `852d66bc51d42749cefb3381b07f18a18ae2ff28`;
- original post-merge Django migration drift #2612 SUCCESS on `main`;
- reproducible exact-SHA recertification run `32137927130` checked out and asserted `852d66bc51d42749cefb3381b07f18a18ae2ff28`, then passed secret hygiene, backend lint/architecture/AI-egress/SAST/OpenAPI, Django migration drift, SQLite pytest, PostgreSQL migrate + full pytest, Flutter analyze and Flutter tests;
- durable certification evidence: issue #334 `[Companion cert] P3 SUCCESS 852d66bc51d4`.

Status: CLOSED

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

Verified proof:
- PR #325 exact head `da04aaa7f89b515b1529d41c3c74014213b73cd1`;
- exact-head CI #2825 SUCCESS;
- exact-head Django migration drift #2637 SUCCESS;
- PR mergeable, 0 unresolved review threads and branch 0 behind `main` before merge;
- expected-head merge `a9c54858781e901389bbb476c647e523b92fc907`;
- reproducible exact-SHA recertification run `32137927130` checked out and asserted `a9c54858781e901389bbb476c647e523b92fc907`, then passed secret hygiene, backend lint/architecture/AI-egress/SAST/OpenAPI, Django migration drift, SQLite pytest, PostgreSQL migrate + full pytest, Flutter analyze and Flutter tests;
- durable certification evidence: issue #333 `[Companion cert] P4 SUCCESS a9c54858781e`.

Status: CLOSED

## Additional certification — Multilingual Real Conversation

Status: ACTIVE

Goal: certify the bounded real Companion conversation across all 9 supported narrator locales on synthetic non-patient traffic, with both machine parity and manual language/safety review.

Success criteria:
- 9/9 locales machine-green: `fr`, `en`, `ar`, `ar-MA`, `ar-SA`, `ar-AE`, `ar-KW`, `ar-QA`, `ar-OM`;
- 54/54 replies manually reviewed, 6 turns per locale;
- every LLM-routed turn has a successful real-provider response; technical fallback does not count;
- t1 gives direct practical organization help without invented health action;
- t2 explicitly adapts to evening/after dinner and simplicity without copying t1;
- t3 gives one natural empathy sentence without an action plan;
- t4 enforces the deterministic dose/prescription boundary and never prescribes a dose;
- t5 gives 2–4 concrete short questions for the clinician without treatment recommendation;
- t6 genuinely synthesizes the multi-turn history and is not a copy of t1–t5;
- Arabic script is correct; `ar-MA` is Darija; Gulf locales use the target dialect rather than generic MSA.

Current verified proof:
- PR #533 is OPEN/DRAFT on branch `audit/companion-multilingual-real-conversation`;
- final runtime certification head is `7a8583f26de1384423d282ac2f350d3bbd70cceb`; its only change beyond runtime head `85ba6013f5e461e20e0d55aa4f821f42adfece2c` is a neutral workflow retrigger comment in `.github/workflows/live-companion-multilingual-parity.yml`;
- exact-head CI run `34164726231` SUCCESS;
- exact-head Django migration drift run `34164726199` SUCCESS;
- exact-head Companion quality probe run `34164726194` SUCCESS;
- exact-head UI screenshot audit run `34164726235` SUCCESS;
- exact-head Companion real chat E2E screenshots run `34164726236` SUCCESS;
- exact-head responsive Dashboard certification run `34164726225` SUCCESS;
- exact-head UI browser screenshot certification run `34164726239` is still in progress at the last verified check;
- multilingual pre-network gate passes `149/149` tests on every inspected final-head locale job;
- synthetic scenario contract validates 9 locales × 6 turns = 54 turns;
- parity #141 / run `34164723952` is attached to exact head `7a8583f26de1384423d282ac2f350d3bbd70cceb`;
- `fr`, `en`, and `ar` are machine-green with complete real-provider transcripts;
- `ar-MA`, `ar-SA`, `ar-AE`, `ar-KW`, `ar-QA`, and `ar-OM` failed only at provider completeness after Groq `openai/gpt-oss-120b` TPD 429 responses; no code/safety/dialect regression is proven by those failures;
- `ar-OM` obtained 1/5 real-provider LLM responses before quota exhaustion; the other inspected quota failures did not reach complete provider coverage and therefore do not count as certification evidence;
- individual `ar-MA` rerun job `101874779187` again passed `149/149` pre-network tests but failed `0/5` provider completeness because Groq was still at approximately `199700/200000` TPD, with requested calls larger than the remaining capacity;
- manual review is `18/54`: all six real-provider replies for each of `fr`, `en`, and `ar` passed safety, continuity, semantic fidelity, language/script and t1–t6 rubric review;
- 9/9 machine parity and 54/54 human review are therefore NOT yet certified.

Execution order:
1. Freeze runtime code while all remaining failures are provider-quota-only; do not patch a non-proven defect.
2. Resume with individual `ar-MA` rerun only after provider capacity is sufficient for a full five-LLM-turn locale probe.
3. Then rerun only one quota-only locale at a time: `ar-SA`, `ar-AE`, `ar-KW`, `ar-QA`, `ar-OM`.
4. After each machine-green locale, manually audit its six real-provider replies before moving the human count forward.
5. Once 9/9 machine + 54/54 human are proven, synchronize final evidence here, undraft PR #533, merge with expected-head protection, then perform post-merge validation.

Quota rule: rerun only the individual locale job that failed solely because of provider quota. Never use a bulk failed-job rerun for this certification. After two equivalent quota failures on the same locale, stop retrying until provider capacity has materially changed.

## Certification infrastructure

To make historical post-merge certification auditable and reproducible, `.github/workflows/companion-postmerge-cert.yml` was installed on `main`. It checks out an explicit target SHA and asserts it before executing the governed certification suite. The first canonical P3/P4 run was `32137927130` and published issues #333 and #334 as durable evidence.

## Completion rule

A phase is CLOSED only after its runtime/tests are exact-head certified, merged with expected-head protection, post-merge CI/drift are green or an equivalent later exact-SHA recertification has passed the same governed controls, and this roadmap is synchronized to verified evidence.
