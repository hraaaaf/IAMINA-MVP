# IAmina — Roadmap

> **Last updated:** 2026-08-10 — proof-only competitive benchmark remediation registered. **P0-BENCH-1 — Pilot evidence & retention contract** is the current internal engineering LOT on PR #94. UX-4 and UX-5 are also reconciled into the canonical tracker after their merges.
>
> **Authority:** this file is the single forward tracker. Detailed implementation history belongs in git, ADRs, architecture documents and supporting evidence files.

## North star

Ship a **safe, measurable MENA diabetes companion** to one founder-selected pilot cohort, then use retention, safety and payer evidence to decide whether IAmina deserves expansion.

## Product constraints

- One live condition: diabetes.
- MENA rollout is country-by-country and locale-by-locale.
- French, Modern Standard Arabic and English are baseline languages.
- Dialects require explicit selection, native review and safety parity.
- Location may suggest settings; it never silently determines language, consent, emergency resources or clinical behavior.
- IAmina is a companion, not a diagnostic or prescribing system.
- Deterministic clinical and safety logic decides; external models receive only approved minimized data.
- No second disease module before the retention gate passes.
- Competitive-benchmark work may improve product capability but may never bypass the pilot safety/compliance gate.

---

# Progress dashboard

| Workstream | Progress | Status | Evidence |
|---|---:|---|---|
| P0 historical foundations | 100% | ✅ Merged | P0-A, P0-B, P0-C and migration drift |
| P0 product truthfulness | 100% | ✅ Closed | PRs #39–#43; five executable UX truthfulness contracts |
| P0 agent governance | 100% | ✅ Closed | PR #63; Builder → Reviewer → Release Certifier protocol |
| P0 visual UX remediation | 100% | ✅ Closed | P0-UX-6 through P2-UX-14; PRs #53–#66 |
| UX visual rebase | 100% | ✅ Closed | UX-0 through UX-5; latest PR #92, mobile navigation 9.4/10 |
| Journal metabolic-event redesign | 100% | ✅ Closed | P0-JOURNAL-1/2 + P1-JOURNAL-3/4/5/6/7 + P2-JOURNAL-8/9; PR #77; UX 9.3/10 |
| P0-MENA-1 — outbound AI/data-egress contract | 100% | ✅ Merged | PRs #10–#15 |
| P0-MENA-2 — locale + safety contract | 63% | 🟡 Native review blocked | PR #16, RTL PR #36, review package PR #37; three human gates remain |
| P0-MENA-3 — sovereign authentication migration | 100% | ✅ Merged | PR #17, merge `185f680` |
| P0-MENA-4 — multimodal provider benchmark | 29% | 🟡 Live runs blocked | Framework PR #18; modality preparation PRs #19–#22 |
| Pilot safety/compliance gate | 69% | 🟡 External/human gates remain | 9 of 13 explicit gates complete; issue #30 remains blocking |
| Benchmark remediation | P0 active | 🔄 In progress | `docs/BENCHMARK_REMEDIATION.md`; P0-BENCH-1 PR #94 |

**MENA critical-path completion:** 32 of 41 explicit roadmap tasks closed, approximately **78%**.

The benchmark, Journal and UX lanes are separate product-quality/evidence workstreams and do not change the MENA critical-path numerator unless a future LOT explicitly closes an existing critical-path gate.

Preparation work does not close a live provider benchmark, legal/privacy approval, native review, credential-remediation task or real-patient outcome gate.

---

# Competitive benchmark remediation

Canonical evidence and acceptance details: [`docs/BENCHMARK_REMEDIATION.md`](BENCHMARK_REMEDIATION.md).

A proof-only evidence review against current Glooko, Dexcom, FreeStyle Libre and mySugr documentation, combined with the checked IAmina repository state, supports the following remediation priorities: **pilot outcome evidence, device/data ecosystem, clinician workflows, caregiver sharing, interoperability, MENA safety parity and external operational assurance**.

No global competitive score is canonical yet. A score may be added only after a versioned criterion-by-criterion matrix records the IAmina proof or `NON PROUVÉ`, the official competitor source, the scoring rule and observation date for every scored item.

| LOT | Responsibility | Priority | Status | Closure boundary |
|---|---|---|---|---|
| **P0-BENCH-1** | Pilot evidence & retention contract | P0 | 🔄 Current LOT — PR #94 | auditable/versioned rolling D1/D7/D30/D90; mature denominators; explicit `as_of`; explicit approved-roster scope; SQLite/PostgreSQL proof; no invented success threshold |
| **P1-BENCH-2** | Device/Data Integration Foundation | P1 | ⏳ Queued | canonical provenance-aware ingestion contract + prioritized MENA source/device matrix before vendor-specific expansion |
| **P1-BENCH-3** | IAmina Clinician Connect | P1 | ⏳ Queued | invitation + explicit patient consent + bounded clinician read access + report + revocation/audit; no prescribing authority |
| **P1-BENCH-4** | Care Circle | P1 | ⏳ Queued | granular patient-controlled caregiver/family scopes + revocation without exposing the complete record by default |
| **P2-BENCH-5** | Standards interoperability | P2 | ⏳ Queued | evidence-backed FHIR/export mapping for data IAmina actually supports; no speculative EHR claims |
| **P2-BENCH-6** | External assurance & real-world evidence | P2 | ⏳ Gated by pilot | completed cohort evidence, limitations, external assurance as applicable and D90 decision package |

## P0-BENCH-1 — Pilot evidence & retention contract — CURRENT

### Reproduced defect

The pre-LOT SQL retention implementation was inconsistent across horizons and insufficiently scoped for pilot evidence:

- D1 and D7 were declared ready as soon as any acquired patient existed, so a patient younger than one or seven days could enter the denominator as a false non-retained result.
- D30 and D90 already excluded patients too young to reach the horizon.
- rolling-return semantics existed implicitly but were not named in the evidence contract.
- retention and funnel snapshots depended on database current time and exposed no common evidence cutoff, so later events could change a historical evidence cut.
- the computation was product-wide only, so a future pilot cohort could be contaminated by unrelated patients with observability events.

### Acceptance criteria

- [x] Preserve and explicitly name existing **rolling retention** semantics: a return at or after the horizon counts, but only up to the evidence cutoff.
- [x] D1/D7/D30/D90 all exclude immature patients from that horizon denominator.
- [x] Expose `eligible_d1`, `eligible_d7`, `eligible_d30`, `eligible_d90` separately from total cohort size.
- [x] Define `cohort_ready_dN` as `eligible_dN > 0` for every horizon.
- [x] Use one timezone-aware `as_of` timestamp to bound acquisition, return, funnel and engagement evidence.
- [x] Reject naive `as_of` timestamps.
- [x] Support an explicit validated patient roster that scopes retention, funnel and engagement evidence consistently; an empty explicit roster fails closed to empty evidence.
- [x] Expose retention-contract version, semantics, cohort scope, roster size and evidence cutoff in the immutable result.
- [x] Add permanent regressions for immature D1/D7, mixed-age denominators, rolling D7, future-event/acquisition exclusion, roster isolation/validation and immutable output.
- [ ] Exact-head canonical CI including PostgreSQL source-of-truth is green.
- [ ] Exact-head migration drift is green.
- [ ] Database & Migration Reviewer FINAL PASS on the final diff/evidence.
- [ ] Release Certifier CERTIFIED on the final docs/code SHA.
- [ ] Merge with expected-head locking and verify post-merge CI + drift.

### Non-scope / fail-closed boundary

P0-BENCH-1 does **not** enroll a real patient, close the existing 13-item Pilot safety/compliance gate, choose a D7/D30/D90 success percentage, add device integrations, add clinician/caregiver access, implement FHIR, or turn retention into a patient-facing clinical metric.

No real-patient outcome may be called successful until a separate pilot protocol explicitly defines the decision rule. No threshold is inferred from competitor performance or invented in code.

---

# Completed P0 foundations — durable summary

## ✅ P0-A — API safety boundaries

- CSRF retained for session/cookie writes.
- Bearer/bootstrap behavior supported.
- Diabetes routes covered by unit guards.
- Unexpected normalization failures fail closed.
- Deterministic triage remains authoritative.

## ✅ P0-B — Server-side AI egress authorization

- Central provider-agnostic patient/purpose/modality boundary.
- Consent checked immediately before real egress.
- Text, audio, vision/OCR, documents, chat and summaries wired.
- CI prevents unauthorized provider callsites.

## ✅ P0-C — Clinical analytics and PostgreSQL parity

- GRI corrected against the normative disjoint-zone formula.
- Patient-facing GRI fails closed until CGM coverage is valid.
- SQLite/PostgreSQL analytics parity established.
- PostgreSQL 16 full-suite CI is permanent.

## ✅ Migration drift

- Migration state reconciled without unnecessary ALTER operations.
- `makemigrations --check --dry-run` is a permanent CI gate.

## ✅ Agent governance

`AGENTS.md`, `docs/CONTRIBUTING.md`, `.agents/` and `.skills/` require Builder → applicable Reviewer(s) → Release Certifier, exact-head evidence, expected-head merge locking and post-merge verification.

## ✅ Product truthfulness

PRs #39–#43 permanently cover real actions/CRUD, truthful sync/storage state, explainable clinical metrics, compact Importer/document picking and deployment-aware privacy wording.

Detailed historical closeout evidence remains in the corresponding PRs/commits and git history rather than being duplicated into the forward roadmap.

---

# Closed product-quality lanes

## Journal metabolic-event redesign — ✅ CLOSED

PRs #67–#77 delivered the factual metabolic-event journal: truthful glucose capture, express logging, sourced meal/nutrition data, already-administered insulin, explicit context, Ramadan profile context, deterministic repeated-observation patterns and factual post-save receipts. No LOT introduced autonomous dosing, diagnosis or treatment optimization. Final Journal UX evidence reached **9.3/10**.

Do not reopen Journal without a new evidence-backed roadmap decision.

## P0 visual UX remediation — ✅ CLOSED

P0-UX-6 through P2-UX-14 were certified through PRs #53–#66. Required UX LOTs were recaptured in FR/AR across desktop/tablet/mobile/hostile small-screen viewports and had to score strictly above 9.0/10 before closure.

## UX visual rebase — ✅ CLOSED

| LOT | Scope | Evidence | Status |
|---|---|---|---|
| UX-0 | baseline + visual constitution | PR #83 | ✅ |
| UX-1 | populated Dashboard locale parity + hierarchy | PR #84; 9.2/10 | ✅ |
| UX-2 | Summary load-error desktop composition | PR #86; 9.3/10 | ✅ |
| UX-3 | canonical IAmina shell brand signature | PR #89; 9.4/10 | ✅ |
| UX-4 | Summary degraded-state continuity | PR #91 merged as `57f2a672`; page hierarchy preserved in degraded state | ✅ |
| UX-5 | glass mobile navigation | PR #92 merged as `76daf3ad`; exact-head CI #1487 + drift #1299; 8/8 FR/AR mobile views; Product Design 9.4/10 | ✅ |

Do not open another UX remediation LOT unless fresh rendered evidence exposes a new <=9.0 state or a new requirement changes a certified surface.

---

# P0-MENA-1 — Outbound AI/data-egress contract — ✅ MERGED

- [x] Text payload allowlist and minimization.
- [x] Deterministic semantic DLP.
- [x] Granular raw-media consent.
- [x] Authenticated patient consent management.
- [x] Executable processor-policy registry.
- [x] Typed provider failures and bounded timeouts.
- [x] Stable non-sensitive API error contract.
- [x] Deterministic Flutter failure UX.
- [x] Safe stream cancellation and partial-failure handling.
- [x] Exhaustive synchronous, streaming and multimodal non-bypass proof.

**Merge:** PR #15. SQLite, PostgreSQL, migration, OpenAPI, security and Flutter gates passed.

---

# P0-MENA-2 — Locale + safety contract — 🟡 PARTIAL

## Closed

- [x] Separate country, UI language, response language, script/transliteration, dialect, units and timezone.
- [x] Require explicit user confirmation; location only suggests.
- [x] Deterministic fallback to MSA, English or French.
- [x] Versioned Morocco emergency-resource registry with confirmed-country-only selection.
- [x] Complete technical RTL coverage screen by screen through PR #36.

## Remaining human-language gates

- [ ] Native-speaker approval for every enabled safety corpus.
- [ ] Darija high-severity orthographic variants closed by native review.
- [ ] Safety parity approved across text, voice transcript, mixed language and transliteration.

PR #37 provides the fingerprinted review package. `audit_safety_corpus_review --require-approved` remains fail-closed until restricted native, clinical and safety-owner evidence covers the exact corpus fingerprint.

---

# P0-MENA-3 — Sovereign authentication migration — ✅ MERGED

Delivered through PR #17:

- Django-owned registration/login/logout;
- signed expiring IAmina bearer tokens and global revocation;
- native recovery/reset UX;
- controlled Firebase-to-Django migration boundary with collision handling and rollback;
- native-first Flutter initialization and secure token storage;
- reconciled SQLite/PostgreSQL migrations.

Permanent operational gates:

```bash
python manage.py audit_auth_migration
python manage.py audit_auth_migration --require-zero-firebase
```

The second gate remains required before removing the controlled legacy migration bridge/runtime dependencies.

---

# P0-MENA-4 — Multimodal provider benchmark — 🟡 LIVE RUNS DEFERRED

**Goal:** select text, STT and vision providers using evidence rather than configuration convenience.

- [x] Representative minimized/synthetic evaluation sets and stable fingerprints — PR #18.
- [x] Privacy/residency/no-training quality/safety/latency/availability/cost scoring with hard floors — PR #18.
- [x] Text execution boundary — PR #19.
- [x] STT execution boundary — PR #20.
- [x] Vision/OCR execution boundary — PR #21.
- [x] Cutover/readiness package — PR #22.
- [ ] Benchmark text providers live.
- [ ] Benchmark STT providers live.
- [ ] Benchmark vision/OCR providers live.
- [ ] Document evidence-backed decision matrix and rejected alternatives.
- [ ] Approve provider cutover only after privacy, quality and human-review gates pass.

No provider score, decision or production approval may be inferred from preparation status.

---

# Pilot safety/compliance gate — before one real patient

- [x] Deterministic refusal of insulin-dose/treatment requests without generative authority — PR #23.
- [x] Doctor-facing and summary outputs pass the same no-prescription policy — PR #23.
- [x] Truthful self-care-only emergency operating mode — PR #24.
- [ ] Close Darija high-severity review — prepared by PR #37; human approval absent.
- [x] Enforce base AI/model consent server-side.
- [x] Expose granular raw-media consent through authenticated patient API.
- [ ] Approve pilot consent matrix and processor/subprocessor register — executable gate prepared by PR #34; restricted approvals external.
- [ ] Approve cross-border/data-residency assumptions for actual pilot deployment — executable gate prepared by PR #35; restricted manifest external.
- [x] Implement audited patient data portability export — PR #25.
- [x] Define executable retention/deletion schedules — PR #26.
- [x] Approve incident-response/escalation procedure — PR #27.
- [x] Approve onboarding/monitoring/escalation/exit checklists — PR #28.
- [ ] Prove no committed/reachable secrets remain and rotate exposed keys — PR #38 tooling exists, but issue #30 still blocks rotation/history remediation.

**Checkpoint:** 9 of 13 explicit gates closed. Real-patient enrollment remains blocked until all required gates are genuinely satisfied; prepared tooling is not approval evidence.

---

# Current blockers and execution order

## External / human blockers

1. **Security emergency:** revoke/rotate potentially affected PekPik credentials, review provider activity under issue #30, then complete history remediation and passing non-shallow scan.
2. Complete restricted CNDP/contract/processor/privacy/security/deployment approvals and run PR #34/#35 fail-closed gates.
3. Complete PR #37 native/clinical review manifest and run `audit_safety_corpus_review --require-approved`.
4. Run deferred live text/STT/vision benchmarks once approved evidence, credentials, budget and human review are available.

## Internal engineering sequence from the competitive benchmark

1. **P0-BENCH-1 — current:** certify trustworthy pilot retention evidence before any outcome is collected.
2. Once P0-BENCH-1 is merged, keep real-patient pilot execution gated by the 13-item safety/compliance checklist above.
3. After P0 and according to the canonical safety priority at that time: **P1-BENCH-2 Device/Data Integration Foundation**.
4. Then **P1-BENCH-3 Clinician Connect** and **P1-BENCH-4 Care Circle**, each as separate branch/PR/LOT.
5. **P2-BENCH-5 interoperability** only after the internal data contract is stable; **P2-BENCH-6 evidence/assurance** requires actual pilot results.

No device, clinician, caregiver or standards LOT may be pulled into P0-BENCH-1. One responsibility remains one branch, one PR and one certification unit.
