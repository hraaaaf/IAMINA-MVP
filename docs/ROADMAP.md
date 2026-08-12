# IAmina — Roadmap

> **Last updated:** 2026-08-12 — P0-CLIN-INTEL-0 audited the real clinical-intelligence/proactivity stack and established the next evidence/safety workstream. UX visual rebase remains closed through UX-11 at 9.8/10.
>
> **Authority:** this file is the single **forward** tracker. Detailed implementation history belongs in git, merged PRs, ADRs, assessments and architecture documents.

## North star

Ship a **safe, measurable MENA diabetes companion** to one founder-selected pilot cohort, then use retention, safety and payer evidence to decide whether IAmina deserves expansion.

IAmina's intended product moat is now explicit: **evidence-qualified longitudinal clinical intelligence and proactive follow-up**, not a generic chatbot and not autonomous treatment optimization.

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
| Pilot safety/compliance gate | 69% | 🟡 External approvals/remediation remain | 9/13 explicit gates complete; issue #30 remains blocking |
| Clinical intelligence / proactivity | Audit complete; remediation next | 🔴 Active | P0-CLIN-INTEL-0 assessment; P0-CLIN-INTEL-1 is next executable LOT |

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

Turn the existing analytical stack into an evidence-governed longitudinal companion that can safely answer:

- what materially changed from the patient's own baseline;
- whether an observation is repeated enough to deserve attention;
- what evidence supports it and what remains unknown;
- whether the underlying knowledge is standard of care, emerging evidence or investigational;
- whether the same observation occurred before and what happened afterward;
- whether the appropriate product action is education, monitoring, clinician handoff or deterministic emergency routing.

The target lifecycle is:

`OBSERVE → QUALIFY EVIDENCE → DETECT → PRIORITIZE → EXPLAIN → FOLLOW UP → RESOLVE / ESCALATE`

The target insight state model is:

`NEW → MONITORING → PERSISTING / IMPROVING → RESOLVED / ESCALATED`

Generative AI never becomes the authority for detection, emergency classification, diagnosis, prescription, dose calculation or treatment optimization.

## P0-CLIN-INTEL-0 — Real brain audit — CLOSEOUT UNIT PR #124

**Assessment:** `docs/assessments/2026-08-12-clinical-intelligence-proactivity-audit.md`.

Durable findings:

- SQL-first KPI analytics and the shared safety/truth-capability architecture are strong foundations.
- `clinical/personal_response.py` is the preferred model for evidence-qualified personalization.
- legacy detector wording contains unsupported causal/treatment-oriented semantics that must be removed from detector authority;
- named Somogyi inference is too strong for sparse Journal pairs and must become neutral observation semantics or be retired;
- `correlations.py` uses an uncalibrated pseudo-confidence and historical negative/default controls that conflict with the current data contract;
- `prediction.py` is an unvalidated prototype and must not be patient/clinician authority;
- legacy diabetes emergency templates contain France-specific emergency-resource text and must not bypass jurisdiction-owned shared safety;
- doctor brief must consume evidence-qualified structured observations instead of raw legacy detector identity/evidence;
- there is no complete proactive Insight Lifecycle yet.

**Baseline clinical-intelligence maturity:** **5.8/10**. This is an engineering/product maturity score from the audit, not a clinical-performance claim.

## Ordered execution

| LOT | One responsibility | Status | Acceptance gate |
|---|---|---|---|
| P0-CLIN-INTEL-0 | Audit real clinical/proactive stack | ✅ Audited; PR #124 is merge unit | Findings grounded in current code/contracts; no runtime change |
| **P0-CLIN-INTEL-1** | **Clinical semantics hardening** | 🔴 **NEXT** | No reachable patient/doctor surface converts observational data into unsupported causality, diagnosis or treatment optimization; unvalidated prediction/correlation authority is impossible; emergency resources remain jurisdiction-governed |
| P1-CLIN-SKILLS | Diabetologist Skills Foundation | ⏳ Planned | Repository-owned clinical reasoning, proactive-intelligence and evidence-intelligence skills exist and cannot override deterministic authority |
| P1-EVIDENCE | Versioned Diabetes Evidence Registry | ⏳ Planned | Every governed clinical metric/rule/observation records source/version, population, modality, evidence maturity, review date and supersession state |
| P2-CLINICAL-TWIN | Longitudinal Observation Memory | ⏳ Planned | Recurring evidence-qualified observations can be followed without promoting model inference to patient fact |
| P2-PROACTIVE | Prioritization + Insight Lifecycle | ⏳ Planned | Clinical relevance, persistence, actionability, confidence/evidence density and interruption cost govern what surfaces and when |
| P2-DOCTOR | Consultation Intelligence | ⏳ Planned | Clinician brief reports evidence-qualified change since last review with uncertainty and provenance |
| P3-HORIZON | Evidence Horizon Scanner | ⏳ Planned | Standard-of-care, emerging and investigational evidence remain explicitly separated; papers cannot silently alter patient rules |
| P3-EVALS | Clinical Intelligence Evals | ⏳ Planned | Clinician-reviewed longitudinal, negative, false-positive and safety scenarios provide measurable release gates |

### P0-CLIN-INTEL-1 non-scope

- no new treatment recommendations;
- no new insulin/medication calculator;
- no new predictive model;
- no new proactive notification product;
- no evidence-registry platform yet;
- no broad UX redesign.

P0-CLIN-INTEL-1 first makes the **existing reachable brain trustworthy**. Capability expansion starts only after that gate closes.

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
- [ ] Prove no reachable committed secrets remain and rotate affected keys; issue #30 blocks final closure.

Preparation/executable gates do not imply that external legal, processor, linguistic, security or production-deployment approvals have occurred.

---

# Current blockers and next sequence

1. **Clinical intelligence product lane:** close PR #124, then execute **P0-CLIN-INTEL-1** immediately. This lane is executable without waiting for external MENA approvals and must remain isolated from them.
2. **Security emergency:** revoke/rotate all potentially affected PekPik credentials and review provider activity under issue #30.
3. After credential rotation confirmation, rewrite affected refs, require fresh clones, obtain a passing non-shallow secret-history scan and activate the blocking history gate.
4. Complete restricted CNDP, contract, processor, privacy, security and deployment-manifest approvals; then run PR #34/#35 `--require-approved` gates.
5. Complete the restricted PR #37 native/clinical review manifest and run `audit_safety_corpus_review --require-approved`.
6. Run deferred live text, STT and vision/OCR benchmarks when approved evidence, credentials, budget and human review are available.
7. UX visual rebase and Journal redesign remain closed. Reopen them only when fresh evidence or a new clinical-intelligence requirement changes a certified surface.
8. After pilot blockers are cleared, run the real-patient pilot go/no-go and cohort execution gates.
