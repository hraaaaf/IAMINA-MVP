# IAmina — Roadmap

> **Last updated:** 2026-08-12 — P2-DOCTOR-0 Consultation Brief Contract is certified, merged and post-merge green. **P2-DOCTOR-1 — Deterministic Brief Assembler is now NEXT.** UX visual rebase remains closed through UX-11 at 9.8/10.
>
> **Authority:** this file is the single **forward** tracker. Detailed implementation history belongs in git, merged PRs, ADRs, assessments and architecture documents.

## North star

Ship a **safe, measurable MENA diabetes companion** to one founder-selected pilot cohort, then use retention, safety and payer evidence to decide whether IAmina deserves expansion.

IAmina's intended product moat is **evidence-qualified longitudinal clinical intelligence and proactive follow-up**, not a generic chatbot and not autonomous treatment optimization.

## Product constraints

- One live condition: diabetes.
- MENA rollout is country-by-country and locale-by-locale.
- French, Modern Standard Arabic and English are baseline languages.
- Dialects require explicit selection, native review and safety parity.
- Location may suggest settings; it never silently determines language, consent, emergency resources or clinical behavior.
- IAmina is a companion, not a diagnostic or prescribing system.
- Deterministic clinical and safety logic decides; generative models may narrate only approved structured output.
- No diagnosis, prescription, dose calculation or treatment optimization.
- No second disease module before the retention gate passes.

---

# Progress dashboard

| Workstream | Progress | Status | Evidence |
|---|---:|---|---|
| P0 historical foundations | 100% | ✅ Merged | P0-A, P0-B, P0-C and migration drift |
| P0 product truthfulness | 100% | ✅ Closed | PRs #39–#43 |
| P0 agent governance | 100% | ✅ Closed | PR #63; Builder → Reviewer → Release Certifier protocol |
| P0 visual UX remediation | 100% | ✅ Closed | P0-UX-6 through P2-UX-14; PRs #53–#66 |
| UX visual rebase | 100% | ✅ Closed | UX-0–11; UX-11 reference parity 9.8/10; PR #110 |
| Journal metabolic-event redesign | 100% | ✅ Closed | P0-JOURNAL-1/2 + P1-JOURNAL-3/4/5/6/7 + P2-JOURNAL-8/9; PRs #67–#77 |
| P0-MENA-1 — outbound AI/data-egress contract | 100% | ✅ Merged | PRs #10–#15 |
| P0-MENA-2 — locale + safety contract | 63% | 🟡 Native review blocked | PR #16, #36, #37; three human linguistic/parity gates remain |
| P0-MENA-3 — sovereign authentication migration | 100% | ✅ Merged | PR #17 |
| P0-MENA-4 — multimodal provider benchmark | 29% | 🟡 Live runs externally blocked | PRs #18–#22 prepared execution paths |
| Pilot safety/compliance gate | 69% | 🟡 External approvals/remediation remain | 9/13 explicit gates complete; issue #30 remains a governance blocker despite being closed `not planned` |
| Clinical intelligence / proactivity | P0 foundation + Clinical Twin + proactive lifecycle + P2-DOCTOR-0 contract certified | 🟡 P2-DOCTOR active — assembler next | PR #143 merge `04fb6535…`; post-merge CI #1893 + drift #1705 green |

**MENA critical-path completion:** 32 of 41 explicit MENA tasks closed, approximately **78%**.

Clinical-intelligence, Journal and UX quality lanes are tracked separately and do not alter the MENA critical-path numerator unless a later pilot gate explicitly depends on them.

---

# Completed P0 foundations — durable summary

## ✅ P0-A — API safety boundaries

- CSRF retained for session/cookie writes.
- Bearer/bootstrap behavior supported.
- Diabetes routes covered by unit guards.
- Unexpected normalization failures fail closed.
- Deterministic triage remains authoritative.

## ✅ P0-B / P0-MENA-1 — AI egress authorization + outbound contract

- Central provider-agnostic patient/purpose/modality authorization boundary.
- Server-side consent checked at real egress time.
- Payload allowlists/minimization, semantic DLP, granular raw-media consent, processor-policy registry and typed provider failures implemented through the completed MENA-1 sequence.
- CI prevents unauthorized direct provider callsites.

## ✅ P0-C — Clinical analytics and PostgreSQL parity

- GRI corrected against the normative disjoint-zone formula.
- Patient-facing GRI fails closed until CGM coverage is valid.
- PostgreSQL is permanently exercised as the analytical source-of-truth path.
- Migration drift remains a permanent gate.

## ✅ Product truthfulness / Journal / UX foundations

- No fabricated patient facts or demo values may enter real patient UX.
- Journal records observed/patient-entered facts and preserves `client_uuid` offline-sync idempotency.
- Personal metabolic response uses repeated descriptive observations and explicitly does not claim causality, prediction or treatment optimization.
- UX visual rebase is closed through UX-11; certified surfaces are not reopened without fresh evidence or a new requirement.

Historical run IDs, viewport matrices, per-LOT visual scores and merge SHAs remain available in the corresponding merged PRs and git history rather than being duplicated in this forward tracker.

---

# Clinical intelligence & proactive differentiation — ACTIVE

## Objective

Turn the analytical stack into an evidence-governed longitudinal companion that can safely determine:

- what materially changed from the patient's own baseline;
- whether an observation is repeated enough to deserve attention;
- what evidence supports it and what remains unknown;
- whether underlying knowledge is standard of care, emerging evidence or investigational;
- whether the same observation occurred before and what happened afterward;
- whether the appropriate product action is education, monitoring, clinician handoff or deterministic emergency routing.

Target lifecycle:

`OBSERVE → QUALIFY EVIDENCE → DETECT → PRIORITIZE → EXPLAIN → FOLLOW UP → RESOLVE / ESCALATE`

Target insight state model:

`NEW → MONITORING → PERSISTING / IMPROVING → RESOLVED / ESCALATED`

Generative AI never becomes the authority for detection, emergency classification, diagnosis, prescription, dose calculation or treatment optimization.

## ✅ P0-CLIN-INTEL-0 — Real brain audit

**Closure:** PR #124, assessment `docs/assessments/2026-08-12-clinical-intelligence-proactivity-audit.md`.

The audit established a baseline clinical-intelligence maturity score of **5.8/10** as an engineering/product maturity score, not a clinical-performance claim. It identified SQL-first analytics, shared safety/truth contracts and `personal_response.py` as the foundations to keep.

## ✅ P0-CLIN-INTEL-1 — Clinical semantics hardening

**Closure:** PR #126 merged; exact-head CI + PostgreSQL + migration drift, Clinical Safety Reviewer and Release Certifier passed; post-merge `main` CI + migration drift passed.

Durable result:

- active detector authority is observation-only and evidence-qualified rather than diagnostic/causal/treatment-optimizing;
- unvalidated standalone prediction/correlation prototypes fail closed;
- raw-entry Python CV authority is retired in favor of eligible SQL-first CGM metrics;
- sparse/manual data cannot masquerade as validated CGM assessment;
- patient-visible glycemic emergency contacts are resolved only from confirmed-jurisdiction versioned resources;
- the clinician-summary boundary remains KPI/statistics-only rather than legacy pattern authority.

## ✅ P1-CLIN-SKILLS — Diabetologist Skills Foundation — CLOSED

Delivered in PR #127:

- repository-owned `diabetes-clinical-reasoning` procedure defines diabetologist-grade provenance, applicability, eligibility, uncertainty and allowed-next-step reasoning across the diabetes domain;
- `diabetes-proactive-intelligence` defines explicit prioritization dimensions, attention budget and the longitudinal insight lifecycle without black-box urgency or treatment authority;
- `diabetes-evidence-intelligence` separates `STANDARD_OF_CARE`, `EMERGING_EVIDENCE` and `INVESTIGATIONAL`, requires current-source verification and creates a promotion gate before evidence can affect patient rules;
- `CORE_SOURCES.md` maps the current 2026 starting corpus, including ADA Standards 2026, ISPAD pediatric guidance, KDIGO final-vs-draft status and IDF/DaR 2026 fasting-risk resources;
- `AGENTS.md` and `.skills/README.md` route future clinical-intelligence/proactivity LOTs through the new skills while explicitly preserving deterministic runtime precedence.

**Closure:** PR #127 head `763664f5…` passed CI #1731 + drift #1543, Clinical Safety Reviewer and Release Certifier; merge `572b53c3…` then passed post-merge CI #1732 + drift #1544.

## ✅ P1-EVIDENCE — Versioned Diabetes Evidence Registry — CLOSED

Delivered in PR #132:

- immutable, code-first evidence registry with stable IDs, maturity, finality, population, modality, limitations and runtime-authority metadata;
- external evidence cannot directly gain runtime authority; emerging evidence requires an explicit governed promotion before affecting patient rules;
- `source='cgm'` is treated as provenance rather than proof of sensor wear-time/cadence;
- normative TIR/CV/GMI/GRI publication fails closed without verified CGM sufficiency and the required governed-rule authority;
- GMI remains a candidate rule pending a separate formula-promotion decision; the 2018 GMI equation and 2026 updated-GMI evidence cannot silently change patient behavior;
- runtime, `/api/v1/kpis`, LLM context and desktop/mobile dashboard surfaces share the same evidence boundary while descriptive recorded-value statistics remain available;
- regression tests cover registry invariants, provenance, future verified-CGM simulation and non-activation of candidate metrics.

**Closure:** PR #132 head `2ff13282…` passed CI #1784 + drift #1596, Clinical Safety Reviewer and Release Certifier; merge `9d7add2b…` then passed post-merge `main` CI #1785 + drift #1597.

## ✅ P2-CLINICAL-TWIN — Longitudinal Observation Memory — CLOSED

P2 persists a diabetes-owned, recomputable lifecycle for approved deterministic `personal_response` observations without reusing companion/deep-memory state as clinical truth. The certified runtime stores first/last seen timestamps, activation-episode recurrence, active/inactive lifecycle state, evidence-strength evolution, baseline-relative descriptive evolution, evidence provenance and whitelisted recorded context. A short display window cannot change the canonical 90-day lifecycle. `USER_CLAIM`, `HEURISTIC_INFERENCE`, `MODEL_INFERENCE`, `CONVERSATIONAL_STATE` and other non-deterministic truth kinds are rejected as direct clinical-twin writes. Database constraints also reject unapproved truth kind, producer and evidence ID. No diagnosis, prediction, causal attribution, medication/dose/treatment semantics or patient-visible proactive behavior is introduced.

**Original runtime closure:** PR #135 head `1058ee4a…` passed CI #1804 + drift #1616, Clinical Safety Reviewer and Release Certifier; merge `00292e44…` then passed post-merge `main` CI #1805 + drift #1617.

**Derived-data lifecycle hardening:** PR #140 head `3d87940e2a789925ca0b491445c82ce4f9ca23ab` closed the explicit source-erasure concurrency/lifecycle gap. Destructive source DELETE/PATCH/batch replacement now purges and recomputes derived Clinical Twin state only from surviving authoritative source rows under a shared patient-row serialization lock; patient export, retention/account deletion and downstream proactive cascade behavior are regression-tested. Exact-head CI #1867 + drift #1679 passed, Clinical Safety Reviewer + Release Certifier passed, merge `55d6b1713db189dd62f90e96c3467bb47df60c7e`, then post-merge CI #1868 + drift #1680 passed.

## ✅ P2-PROACTIVE — Prioritization + Insight Lifecycle — CLOSED

PR #139 adds a diabetes-owned proactive workflow **derived from** `ClinicalObservationState`; it does not replace or mutate the Clinical Twin as clinical truth.

Certified contract:

- deterministic lifecycle: `NEW → MONITORING → PERSISTING / IMPROVING → RESOLVED`; the current descriptive `personal_response` source is not authorized to enter `ESCALATED`;
- an explicit priority vector exposes non-urgent safety/time sensitivity, observational/review-worthy relevance, persistence, change from the patient baseline, evidence density, bounded actionability, evidence maturity and interruption cost rather than a black-box risk score;
- the current source can emit only `MONITOR` or `PREPARE_CLINICIAN_DISCUSSION`; database constraints reject escalation and treatment-change authority;
- unchanged material state does not re-surface, and the product attention budget allows at most one **non-urgent** item per 24 hours; this is interruption-cost policy, not a medically authoritative follow-up interval;
- `RESOLVED` requires an eligible Clinical Twin refresh showing absence of the previously eligible observation; insufficient data cannot silently resolve prior state;
- true reactivation cannot remain stale-`RESOLVED`, including a matching-fingerprint edge case;
- explicit `POST /api/v1/proactive-insights/evaluate/` evaluates and consumes at most one evidence-qualified candidate; safe GET requests cannot consume delivery state or the attention budget;
- deterministic emergency routing remains separate/upstream and is never suppressed by the non-urgent attention budget;
- no diagnosis, prescription, dose calculation, causal attribution, treatment optimization or generative clinical authority is introduced.

**Closure:** exact head `28215cd944c32ef310fd9d847fb3959ccf86b2c7` passed CI #1844 + migration drift #1656, Clinical Safety Reviewer, Database/Migration Reviewer, Final Diff/Architecture Reviewer and Release Certifier. Expected-head merge produced `752f5543cc651cfeda6fd75f14fd544ae5e8d03a`; post-merge `main` CI #1845 + drift #1657 passed. The subsequent PR #140 lifecycle hardening preserves this authority contract and ensures proactive workflow state cannot outlive erased source Clinical Twin derivation.

## 🟡 P2-DOCTOR — Consultation Intelligence — ACTIVE

### ✅ P2-DOCTOR-0 — Consultation Brief Contract — CLOSED

P2-DOCTOR-0 in PR #143 defines the executable consultation-brief authority contract before any new clinician UX, endpoint replacement or model narration integration.

Certified contract:

- versioned schema `consultation-brief.v1` carries only immutable scalar facts/derivations plus explicit provenance, missing-data and limitation fields;
- v1 admits only `OBSERVED_FACT` and `DETERMINISTIC_DERIVATION`; deterministic derivations must reference a registered product RULE whose evidence registry authority is exactly `GOVERNED_RULE`;
- raw external source records, unknown evidence IDs, governed-rule candidates, `NARRATIVE_ONLY` rules, user claims, preferences, conversational state, heuristic inference and model inference fail closed;
- `CURRENT_SNAPSHOT` and `SINCE_REVIEW_CHECKPOINT` are distinct comparison modes; no `new/persisting/improving/resolved since review` claim is legal without an explicit timezone-aware review checkpoint;
- `limited/moderate/strong` remains evidence/repetition density rather than probability or clinical confidence; no numeric confidence field exists;
- allowed next steps are limited to `MONITOR`, `COLLECT_MISSING_DATA` and `PREPARE_CLINICIAN_DISCUSSION`; direct raw-string treatment/dose action injection is rejected at runtime;
- clinician-brief authority is fixed to `clinician_review_support_only`; any later model narration is limited to reformulating approved structured fields and cannot create clinical truth;
- no endpoint, persisted review checkpoint, deterministic assembler, legacy doctor-brief replacement, clinician UX, diagnosis, prescription, dose calculation or treatment optimization is introduced by P2-DOCTOR-0.

**Closure:** PR #143 head `1983829c…` passed CI #1892 + drift #1704, Clinical Safety Reviewer, Documentation/Architecture Reviewer and Release Certifier; expected-head merge `04fb6535…` then passed post-merge `main` CI #1893 + drift #1705.

### ▶️ P2-DOCTOR-1 — Deterministic Brief Assembler — NEXT

Build the deterministic assembler from approved synchronized observed facts, governed KPI/Clinical Twin derivations and an authoritative prior-review checkpoint source. The assembler must produce `consultation-brief.v1` without model-authored fields, must fail closed when the checkpoint or governed evidence is unavailable, and must not replace the legacy narrator endpoint until separately certified.

## Ordered execution

| LOT | One responsibility | Status | Acceptance gate |
|---|---|---|---|
| P0-CLIN-INTEL-0 | Audit real clinical/proactive stack | ✅ Closed | PR #124 merged and post-merge green |
| P0-CLIN-INTEL-1 | Clinical semantics hardening | ✅ Closed | PR #126 merged and post-merge green |
| **P1-CLIN-SKILLS** | **Diabetologist Skills Foundation** | ✅ **CLOSED** | PR #127 merged and post-merge green |
| **P1-EVIDENCE** | **Versioned Diabetes Evidence Registry** | ✅ **CLOSED** | PR #132 merged as `9d7add2b…`; post-merge CI #1785 + drift #1597 green |
| **P2-CLINICAL-TWIN** | **Longitudinal Observation Memory** | ✅ **CLOSED** | PR #135 runtime + PR #140 lifecycle hardening; current `main@55d6b171…` post-merge CI #1868 + drift #1680 green |
| **P2-PROACTIVE** | **Prioritization + Insight Lifecycle** | ✅ **CLOSED** | PR #139 head `28215cd9…`; merge `752f5543…`; post-merge CI #1845 + drift #1657 green |
| **P2-DOCTOR** | **Consultation Intelligence** | 🟡 **ACTIVE — P2-DOCTOR-1 NEXT** | P2-DOCTOR-0 PR #143 merge `04fb6535…` post-merge green; next = deterministic assembler, endpoint/UX later |
| P3-HORIZON | Evidence Horizon Scanner | ⏳ Planned | Standard-of-care, emerging and investigational evidence remain explicitly separated; papers cannot silently alter patient rules |
| P3-EVALS | Clinical Intelligence Evals | ⏳ Planned | Clinician-reviewed longitudinal, negative, false-positive and safety scenarios provide measurable release gates |

### P2-DOCTOR entry boundary

P2-DOCTOR-0 is closed and establishes the consultation-brief authority contract without exposing a new product surface. P2-DOCTOR-1 must now assemble that contract deterministically from approved source facts/governed derivations and an authoritative prior-review checkpoint; it must not infer review history from app activity or let a model populate unapproved fields. Existing deterministic emergency, no-prescription/no-dose and evidence-promotion boundaries remain upstream and authoritative.

---

# P0-MENA-2 — Locale + safety contract — PARTIAL

## Closed

- [x] Separate country, UI language, response language, script/transliteration, dialect, units and timezone.
- [x] Require explicit user confirmation; location only suggests.
- [x] Deterministic fallback to MSA, English or French.
- [x] Versioned Morocco emergency-resource registry with confirmed-country-only selection.
- [x] Complete technical RTL coverage screen by screen (PR #36).

## Remaining human-language gates

- [ ] Obtain native-speaker approval for every enabled safety corpus; PR #37 exports the exact fingerprinted corpus and requires qualified review evidence.
- [ ] Close remaining Darija high-severity orthographic variants through native review.
- [ ] Approve safety parity across text, voice transcript, mixed language and transliteration.

Automated corpus, route coverage and directionality groundwork is green. `audit_safety_corpus_review --require-approved` remains fail-closed until restricted native/clinical/safety-owner evidence covers the exact corpus fingerprint.

---

# P0-MENA-3 — Sovereign authentication migration — MERGED

Delivered Django-owned registration/login/logout, signed expiring IAMINA bearer tokens, global token revocation, password establishment/recovery, controlled Firebase identity migration/link/unlink, collision/readiness/rollback contracts, native-first Flutter initialization and secure token storage.

Permanent operational gates:

```bash
python manage.py audit_auth_migration
python manage.py audit_auth_migration --require-zero-firebase
```

Firebase dependencies are not removed until the second gate is legitimately satisfied.

---

# P0-MENA-4 — Multimodal provider benchmark — PREPARED, LIVE RUNS DEFERRED

**Goal:** select text, STT and vision providers from privacy, residency, no-training/no-retention, MENA quality, safety, latency, availability and cost evidence rather than brand preference.

- [x] Benchmark framework + representative minimized/synthetic evaluation sets.
- [x] Text/STT/vision execution boundaries and cutover-readiness aggregation prepared through PRs #18–#22.
- [ ] Run live text benchmark.
- [ ] Run live STT benchmark.
- [ ] Run live vision/OCR benchmark.
- [ ] Complete evidence-backed decision matrix and rejected alternatives.
- [ ] Approve provider cutover only after privacy, quality and human-review gates pass.

No provider score, decision or production approval may be inferred from preparation status.

---

# Pilot safety/compliance gate — before one real patient

- [x] Deterministic refusal of insulin-dose/treatment requests across sync chat, SSE and post-STT voice.
- [x] Doctor-facing and summary output passes the same no-prescription policy.
- [x] Truthful `SELF_CARE_ONLY` emergency operating model adopted; no false automatic-human-monitoring claim.
- [ ] Close Darija high-severity native review.
- [x] Base AI/model consent enforced server-side.
- [x] Granular raw-media consent exposed through authenticated patient API.
- [ ] Approve pilot consent matrix and processor/subprocessor register; PR #34 prepares fail-closed gate.
- [ ] Approve Morocco deployment residency/cross-border manifest; PR #35 prepares fail-closed gate.
- [x] Audited patient data portability export.
- [x] Versioned retention/deletion schedule and guarded deletion.
- [x] Incident-response/escalation procedure.
- [x] Pilot onboarding/monitoring/escalation/exit checklist framework.
- [ ] Prove no reachable committed secrets remain and rotate affected keys; issue #30 was closed `not planned`, not remediated, so this pilot gate remains open unless governance explicitly supersedes it.

Preparation/executable gates do not imply that external legal, processor, linguistic, security or production-deployment approvals have occurred.

---

# Current blockers and next sequence

1. **Clinical intelligence product lane:** start **P2-DOCTOR — Consultation Intelligence**, beginning with the consultation-brief authority/provenance/uncertainty contract before runtime or UX expansion.
2. **Pilot security blocker:** issue #30 is closed `not planned` but explicitly not remediated; either complete the documented history remediation/verification path or supersede the pilot policy through normal governance before any real-patient go/no-go.
3. Complete restricted CNDP, contract, processor, privacy, security and deployment-manifest approvals; then run PR #34/#35 `--require-approved` gates.
4. Complete the restricted PR #37 native/clinical review manifest and run `audit_safety_corpus_review --require-approved`.
5. Run deferred live text, STT and vision/OCR benchmarks when approved evidence, credentials, budget and human review are available.
6. UX visual rebase and Journal redesign remain closed. Reopen them only when fresh evidence or a new clinical-intelligence requirement changes a certified surface.
7. After pilot blockers are cleared, run the real-patient pilot go/no-go and cohort execution gates.
