# IAmina — Roadmap

> **Last updated:** 2026-08-13 — P3-HORIZON is certified, merged and post-merge green. **P3-EVALS automated implementation is complete; human review remains required.** UX visual rebase remains closed through UX-11 at 9.8/10.
>
> **Authority:** this file is the single **forward** tracker. Detailed implementation history belongs in git, merged PRs, ADRs, assessments and architecture documents.

## North star

Ship a **safe, measurable MENA diabetes companion** to one founder-selected pilot cohort, then use retention, safety and payer evidence to decide whether IAmina deserves expansion.

IAmina's intended product moat is **evidence-qualified longitudinal companion intelligence and proactive follow-up**, not a generic chatbot, not a virtual doctor and not autonomous treatment optimization.

## Product constraints

- One live condition: diabetes.
- MENA rollout is country-by-country and locale-by-locale.
- French, Modern Standard Arabic and English are baseline languages.
- Dialects require explicit selection, native review and safety parity.
- Location may suggest settings; it never silently determines language, consent, emergency resources or clinical behavior.
- IAmina is a **patient companion**, not a physician, diagnostic system, prescribing system or medical-consultation replacement.
- IAmina may observe, compare, explain and propose only bounded non-prescriptive next steps; the qualified clinician remains the medical decision authority.
- Deterministic clinical and safety logic decides; generative models may narrate only approved structured output.
- No diagnosis, differential diagnosis, prescription, dose calculation, treatment optimization/change or autonomous medical instruction.
- No second disease module before the retention gate passes.

Canonical companion authority: `docs/COMPANION_INTELLIGENCE_CONTRACT.md`.

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
| Companion intelligence / proactivity | P0 foundation + Clinical Twin + proactive lifecycle + P2-COMPANION-0..8 | 🟡 P3-EVALS automated implementation complete — human review required | H0..H3 merged; final H3 merge `100445b2…`; post-merge CI #2007 + drift #1819 green |

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

# Companion intelligence & proactive differentiation — ACTIVE

## Objective

Turn the analytical stack into an evidence-governed longitudinal **patient companion** that can safely determine and communicate:

- what materially changed from the patient's own baseline;
- whether an observation is repeated enough to deserve attention;
- what evidence supports it and what remains unknown;
- whether underlying knowledge is standard of care, emerging evidence or investigational;
- whether the same observation occurred before and what happened afterward;
- which bounded non-prescriptive suggestion is appropriate: understand, monitor, collect missing data, learn, prepare clinician discussion or follow-up recording.

Target companion loop:

`OBSERVE → QUALIFY EVIDENCE → COMPARE → EXPLAIN → SUGGEST → FOLLOW UP → PREPARE DISCUSSION WHEN USEFUL`

The forbidden loop is:

`DATA → AI DIAGNOSIS → AI TREATMENT DECISION`

Generative AI never becomes the authority for detection, emergency classification, diagnosis, prescription, dose calculation or treatment optimization/change.

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

## ✅ P2-COMPANION-0 — Companion Intelligence Contract — CLOSED

The former `P2-DOCTOR` product lane is superseded by the broader patient-first **P2-COMPANION** lane. The canonical contract lives in `docs/COMPANION_INTELLIGENCE_CONTRACT.md`.

Durable authority:

- IAmina is a patient companion, never a physician, diagnosis/prescription system or substitute medical consultation;
- personalization is allowed through governed observation, patient-baseline comparison, evidence qualification, uncertainty and longitudinal memory;
- suggestions are limited to `UNDERSTAND_DATA`, `MONITOR`, `COLLECT_MISSING_DATA`, `LEARN`, `PREPARE_CLINICIAN_DISCUSSION` and `FOLLOW_UP_RECORD`;
- a personalized suggestion cannot become diagnosis, prescription, dose advice or treatment optimization/change;
- emergency recognition/routing remains deterministic and upstream;
- generative models may narrate approved structured output but cannot create facts, urgency, diagnosis, causality or treatment authority;
- the certified PR #143 `consultation-brief.v1` contract is preserved without rollback as a restricted **P2-COMPANION-5 Consultation Companion** foundation; its `clinician_review_support_only` ceiling remains valid and does not define the product as a doctor.

### ✅ P2-COMPANION-1 — Change Since Last Review — CLOSED

PR #147 adds the deterministic runtime foundation for comparing current governed Clinical Twin state with the patient's last explicit IAmina companion review.

Candidate contract:

- the comparison anchor is a server-timestamped `CompanionReviewAnchor` created by an explicit companion-review action; app-open activity, conversation state, a model or a client-supplied timestamp cannot manufacture review history;
- each anchor snapshots only approved deterministic `ClinicalObservationState` fields and retains the existing `diabetes.personal_response.v1` / `rule.personal-response.repetition.v1` authority;
- anchor capture and comparison share the canonical patient-row serialization lock with Clinical Twin refresh/erasure;
- bounded change states are `new`, `persisting`, `improving`, `resolved` and `unknown`; missing anchor returns `insufficient_anchor`;
- `improving` means only that the descriptive baseline-relative delta moved toward the patient's governed personal-window baseline; it is not treatment response, clinical outcome or causality;
- missing current state, absent eligible post-review evidence or an unprovable transition returns `unknown` rather than fabricating persistence or resolution;
- reactivation is represented as `new` with explicit reactivation provenance;
- explicit source erasure/replacement invalidates companion-review anchors before Clinical Twin rebuild so removed source evidence cannot survive in historical comparison snapshots;
- patient export and account-deletion cascade include the persisted anchor/snapshot state;
- P2-COMPANION-1 does not add an endpoint, Flutter UX, model narration, notification behavior, diagnosis, prescription, dose logic, causal attribution, treatment optimization or clinician override.

**Closure:** PR #147 final head `cb8591281997f5e1acca227f6545a1023f4a8fb0` passed CI #1912 + migration drift #1724, Clinical Safety Reviewer, Database/Migration Reviewer, Documentation/Architecture/Companion Safety review 9.8/10 and Release Certifier. Expected-head merge produced `f689f63b2abd7e77739838d0cb3d3e0780628994`; post-merge `main` CI #1913 + drift #1725 passed.

### ✅ P2-COMPANION-2 — Personal Pattern Intelligence — CLOSED

PR #149 adds a deterministic read-only projection of already-governed `ClinicalObservationState`; it does not detect or persist new clinical truth.

Candidate contract:

- patient-scoped projection exposes first-observed time, activation-episode recurrence, active/resolved state, evidence density and repeatability trend, eligible observation/distinct-day counts, personal-window median, baseline-relative delta/direction/movement and provenance;
- accepted observation keys, kinds and recorded-context payloads must exactly match the existing governed personal-response contract; unapproved or mismatched state fails closed;
- the projection requires the canonical 90-day evidence window, finite numeric state, internally consistent baseline history and internally consistent evidence-density history;
- bounded markers are `persisting`, `recurring`, `improving_descriptively` and `resolved`; recurrence is activation-episode recurrence already stored by the Clinical Twin;
- `improving_descriptively` means only that the absolute baseline-relative delta moved toward the patient's own eligible window median; that median is not a clinical target, and the marker is not treatment response, therapeutic success, clinical outcome or causality;
- inactive/resolved rows disclose that numeric values describe the last eligible active evidence rather than current physiology;
- an empty projection means `no_governed_patterns`, not absence of disease or clinical issue; deterministic ordering is not clinical priority;
- evidence density/trend remains repeatability only, never probability, statistical significance or clinical confidence;
- P2-COMPANION-2 adds no endpoint, Flutter UX, model narration, notification, prioritization, new detector, migration, clinical threshold, diagnosis, prediction, prescription, dose logic, treatment optimization/change or clinician override.

**Closure:** PR #149 final head `59401d82e9fa4dc20a5c5c6b53e59d59c19f3bd1` passed CI #1921 + migration drift #1733, Clinical Safety Reviewer FINAL PASS, Documentation/Architecture/Companion Safety review 9.8/10 and Release Certifier GO. Expected-head merge produced `a0560b38ba97c095dfdea4e6a210bd93cbbf0ae3`; post-merge `main` CI #1922 + migration drift #1734 passed.

### ✅ P2-COMPANION-3 — Evidence + Uncertainty — CLOSED

PR #151 adds one deterministic evidence/uncertainty envelope to material P2-COMPANION-1 and P2-COMPANION-2 observations without creating new clinical truth.

Candidate contract:

- material observations expose the governed rule/evidence ID, approved producer, rule topic/summary, evidence maturity, clinical authority, finality, review date, population/modality and any registered supporting-source metadata;
- uncertainty is explicit through repetition density, optional density trend, `missing_data` and limitations; no numeric confidence score exists;
- evidence maturity describes source/rule governance state, while `limited` / `moderate` / `strong` remains only personal-response repetition density; neither is patient probability or clinical confidence;
- external source records remain supporting evidence only and never become runtime authority merely because they are cited;
- unknown, source-only, candidate, narrative-only, superseded or non-versioned rules fail closed for material companion observations;
- `GOVERNED_RULE` alone is insufficient: an explicit Companion rule↔producer registry currently admits only `rule.personal-response.repetition.v1 ↔ diabetes.personal_response.v1`;
- P2-COMPANION-1 `unknown` reasons become explicit item-level missing-data facts; provable change items retain empty missing-data state;
- P2-COMPANION-2 exposes absent prior density/baseline history and resolved-state lack of current active evidence instead of hiding those limitations;
- P2-COMPANION-3 adds no detector, threshold, evidence source, database model/migration, endpoint, Flutter UX, model narration, suggestion, notification, prioritization, diagnosis, prediction, prescription, dose logic, treatment optimization/change or clinician override.

**Closure:** PR #151 final head `4e9cfd0a8d6151fe7f72e1f32c449e7bd969aac3` passed CI #1928 + migration drift #1740, Clinical Safety Reviewer FINAL PASS, Documentation/Architecture/Companion Safety review 9.9/10 and Release Certifier GO. Expected-head merge produced `d8fe70d1803cbf035252ac4d9174e7ecc843b9aa`; post-merge `main` CI #1929 + migration drift #1741 passed.

### ✅ P2-COMPANION-4 — Smart Suggestions — CLOSED

PR #153 adds a deterministic bounded suggestion projection over already-governed P2-COMPANION and P2-PROACTIVE authority; it does not create a second prioritization or clinical decision system.

Certified contract:

- consumes the single non-urgent `ProactiveInsight` already selected by the certified proactive engine, then requires a unique matching P2-COMPANION-2 governed pattern and P2-COMPANION-3 evidence/uncertainty envelope;
- reuses the existing priority vector, material-state delivery signature and one-non-urgent-item-per-24h attention budget rather than inventing a new score;
- canonical suggestion vocabulary remains six classes, but V1 activates only `UNDERSTAND_DATA`, `MONITOR` and `PREPARE_CLINICIAN_DISCUSSION`; `COLLECT_MISSING_DATA`, `LEARN` and `FOLLOW_UP_RECORD` fail closed until explicit prerequisite authority exists;
- deterministic mapping is bounded: first eligible proactive `MONITOR` → `UNDERSTAND_DATA`; eligible monitoring/improving/resolved proactive `MONITOR` → `MONITOR`; existing proactive clinician-discussion authority → `PREPARE_CLINICIAN_DISCUSSION`;
- evidence ID/producer must agree across proactive output, pattern projection and P2-COMPANION-3 envelope; optional P2-COMPANION-1 change metadata remains descriptive and grants no authority;
- proactive delivery and downstream provenance checks share one transaction so failed validation cannot consume attention budget without a safely produced suggestion;
- no detector, clinical threshold, database model/migration, endpoint, Flutter surface, LLM/free-text authority input, diagnosis, causality, prediction, prescription, dose or treatment-change authority is introduced; deterministic emergency routing remains separate/upstream.

**Closure:** PR #153 exact head `afb13fabc4424c20ad88f1f13ea4d1f93bb8eb1a` passed Clinical Safety Reviewer, CI #1932 + migration drift #1744, zero review threads and Release Certifier GO. Expected-head merge produced `71c63ef852ca2c84b7cee86099ed69a762e700ec`; post-merge `main` CI #1933 + drift #1745 passed.

### ✅ P2-COMPANION-5 — Consultation Companion — CLOSED

PR #155 adds the deterministic read-only consultation dossier assembler over already-governed glucose facts, P2-COMPANION-2/3 pattern evidence and authoritative P2-COMPANION-1 review history.

Certified contract:

- reuses the certified `consultation-brief.v1` contract from PR #143 rather than inventing a second clinical-summary authority;
- public assembly accepts only patient identity plus dossier window; no caller checkpoint, diagnosis, free text, model output or action authority is accepted;
- non-demo glucose rows contribute only recorded facts and a descriptive arithmetic average, never CGM target assessment;
- Clinical Twin evidence is accepted only through governed Companion pattern/evidence projection with provenance, density and dossier-window consistency checks;
- since-review semantics require the persisted server-captured companion review anchor inside the requested dossier window; otherwise the brief remains a truthful `CURRENT_SNAPSHOT`;
- `new`, `persisting`, `improving` and `resolved` remain descriptive and authorize only `MONITOR`; change state alone cannot manufacture clinician-discussion authority;
- `unknown` may authorize only `COLLECT_MISSING_DATA` and must preserve explicit missing evidence;
- future/post-window evidence cannot leak backward into the dossier;
- patient-row serialization protects consultation reads against concurrent Clinical Twin refresh/erasure and companion-review capture;
- the clinician remains the medical decision authority; no diagnosis, causality, prediction, urgency, prescription, dose, treatment optimization/change or clinician override is introduced;
- no endpoint, Flutter surface, database migration, notification behavior or LLM/provider change is introduced.

**Closure:** PR #155 exact head `d15d35592fb1e118951cde4f806c3e30d12c40e2` passed Clinical Safety Reviewer, CI #1945 + migration drift #1757, zero review threads and Release Certifier GO. Expected-head merge produced `135d284a5b16df853d74ef791233060b4fffe815`; post-merge `main` CI #1946 + drift #1758 passed.

### ✅ P2-COMPANION-6 — After-Visit Continuity — CLOSED

Track what happened after a consultation and what changed over the interval without judging, overriding or optimizing the clinician's treatment decision. The runtime must distinguish patient/clinician-recorded facts from governed descriptive derivations and must not infer treatment efficacy merely from temporal association.

### ✅ P2-COMPANION-7 — Companion UX — CLOSED

Organize patient-first surfaces around **Understand → Follow → Prepare** rather than around a virtual-clinic or doctor-replacement metaphor.

### ✅ P2-COMPANION-8 — Safety + Certification — CLOSED
Add permanent clinician-reviewed negative, longitudinal, false-positive and boundary evals that block diagnosis, prescription, dosing, treatment-change, false certainty and doctor-replacement regressions.

## Ordered execution

| LOT | One responsibility | Status | Acceptance gate |
|---|---|---|---|
| P0-CLIN-INTEL-0 | Audit real clinical/proactive stack | ✅ Closed | PR #124 merged and post-merge green |
| P0-CLIN-INTEL-1 | Clinical semantics hardening | ✅ Closed | PR #126 merged and post-merge green |
| **P1-CLIN-SKILLS** | **Diabetologist Skills Foundation** | ✅ **CLOSED** | PR #127 merged and post-merge green |
| **P1-EVIDENCE** | **Versioned Diabetes Evidence Registry** | ✅ **CLOSED** | PR #132 merged as `9d7add2b…`; post-merge CI #1785 + drift #1597 green |
| **P2-CLINICAL-TWIN** | **Longitudinal Observation Memory** | ✅ **CLOSED** | PR #135 runtime + PR #140 lifecycle hardening; post-merge green |
| **P2-PROACTIVE** | **Prioritization + Insight Lifecycle** | ✅ **CLOSED** | PR #139 merge `752f5543…`; post-merge CI #1845 + drift #1657 green |
| **P2-COMPANION-0** | **Companion Intelligence Contract** | ✅ **CLOSED** | Canonical authority contract; former P2-DOCTOR framing superseded without rollback of certified PR #143 sub-contract |
| **P2-COMPANION-1** | **Change Since Last Review** | ✅ **CLOSED** | PR #147 head `cb859128…`; merge `f689f63b…`; post-merge CI #1913 + drift #1725 green |
| **P2-COMPANION-2** | **Personal Pattern Intelligence** | ✅ **CLOSED** | PR #149 head `59401d82…`; merge `a0560b38…`; post-merge CI #1922 + drift #1734 green |
| **P2-COMPANION-3** | **Evidence + Uncertainty** | ✅ **CLOSED** | PR #151 head `4e9cfd0a…`; merge `d8fe70d1…`; post-merge CI #1929 + drift #1741 green |
| **P2-COMPANION-4** | **Smart Suggestions** | ✅ **CLOSED** | PR #153 head `afb13fab…`; merge `71c63ef8…`; post-merge CI #1933 + drift #1745 green |
| **P2-COMPANION-5** | **Consultation Companion** | ✅ **CLOSED** | PR #155 head `d15d3559…`; merge `135d284a…`; post-merge CI #1946 + drift #1758 green |
| **P2-COMPANION-6** | **After-Visit Continuity** | ✅ **CLOSED** | Explicit visit/fact provenance; no treatment-efficacy inference; runtime merged and post-merge green |
| **P2-COMPANION-7** | **Companion UX** | ✅ **CLOSED** | P2-7A/B/C/D delivered; final merge `bb5b9cb8…`; post-merge CI #1966 + drift #1778 green |
| **P2-COMPANION-8** | **Safety + Certification** | ✅ **CLOSED** | PR #166 merge `7e4bfe36…`; release matrix + pytest manifest; post-merge CI #1980 + drift #1792 green |
| **P3-HORIZON** | **Evidence Horizon Scanner** | ✅ **CLOSED** | H0..H3 merged; final H3 merge `100445b2…`; post-merge CI #2007 + drift #1819 green |
| **P3-EVALS** | **Companion Intelligence Evals** | 🟡 **HUMAN REVIEW REQUIRED** | EVALS-0..3 implemed and merged; automated gates green; explicit human review provenance still required before closeout |

### Inherited consultation sub-contract

PR #143 and its executable `consultation-brief.v1` contract remain certified historical/runtime foundations. They are **not deleted or weakened** by the P2-COMPANION rebase. P2-COMPANION-5 now implements that narrow authority as a patient consultation-preparation sub-capability without reviving the superseded P2-DOCTOR product framing or expanding the inherited brief into autonomous diagnosis, treatment or clinician-override authority.

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

1. **Companion intelligence product lane:** P2-COMPANION-0..8 and P3-HORIZON are closed; **P3-EVALS automated implementation is complete and awaits explicit human review provenance before closeout.**
2. **Pilot security blocker:** issue #30 is closed `not planned` but explicitly not remediated; either complete the documented history remediation/verification path or supersede the pilot policy through normal governance before any real-patient go/no-go.
3. Complete restricted CNDP, contract, processor, privacy, security and deployment-manifest approvals; then run PR #34/#35 `--require-approved` gates.
4. Complete the restricted PR #37 native/clinical review manifest and run `audit_safety_corpus_review --require-approved`.
5. Run deferred live text, STT and vision/OCR benchmarks when approved evidence, credentials, budget and human review are available.
6. UX visual rebase and Journal redesign remain closed. Reopen them only when fresh evidence or a new companion-intelligence requirement changes a certified surface.
7. After pilot blockers are cleared, run the real-patient pilot go/no-go and cohort execution gates.
