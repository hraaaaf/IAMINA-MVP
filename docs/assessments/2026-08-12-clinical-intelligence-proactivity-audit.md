# IAmina — Clinical Intelligence & Proactivity Audit

> **Date:** 2026-08-12  
> **LOT:** P0-CLIN-INTEL-0 — Audit réel du cerveau IAmina  
> **Baseline:** `main@6bb631c5e048e01df2e5a5a51602264604248e94`  
> **Status:** assessment evidence; not a capability claim and not a clinical rule source.

## 1. Executive verdict

IAmina already has a materially stronger clinical foundation than a generic diabetes chatbot: SQL-first diabetes analytics, deterministic pattern detectors, an upstream safety architecture, a truth/capability contract, longitudinal personal-response analysis, a clinician brief surface, and optional generative narration.

However, the current **clinical-intelligence/proactivity layer is not yet safe or evidence-governed enough to be positioned as a virtual diabetologist**. Several legacy/prototype rules overstate causality or confidence, some detector fallback text crosses the repository's treatment-optimization boundary, and proactive follow-up is still mostly on-demand analysis rather than a closed clinical observation lifecycle.

**Baseline maturity score: 5.8/10.**  
The moat is plausible, but it is not yet defensible.

The target is not “more AI.” The target is:

`OBSERVE → QUALIFY EVIDENCE → DETECT → PRIORITIZE → EXPLAIN → FOLLOW UP → RESOLVE/ESCALATE`

with deterministic clinical authority, explicit provenance and no autonomous treatment optimization.

## 2. What exists today

| Surface | Current implementation | Audit verdict |
|---|---|---|
| Core metrics | `clinical/sql_analytics.py`, SQL-first KPI contract | **KEEP** — strongest analytical foundation |
| Clinical pattern engine | `clinical/engine.py` with 10 deterministic detectors | **REFACTOR** — useful ideas, inconsistent evidence/wording quality |
| Patient-visible sanitation | `core/medical_safety.py` structured observation-only envelope | **KEEP / EXPAND** — currently mitigates unsafe detector prose on structured insight paths |
| Personal metabolic response | `clinical/personal_response.py` | **KEEP AS FOUNDATION** — best-aligned implementation |
| Lifestyle correlation prototype | `clinical/correlations.py` | **QUARANTINE / REPLACE** |
| Glucose prediction prototype | `clinical/prediction.py` | **QUARANTINE** until validated for a defined modality/population |
| Emergency glucose state machine | `clinical/alerts.py` | **REVIEW / CONSOLIDATE** with shared core safety and jurisdiction contract |
| Legacy diabetes shield | `clinical/shield.py` | **REVIEW / CONSOLIDATE** — shared core must remain authoritative |
| Summary | `/api/v1/ai/summary` | **KEEP**, but evidence contract must become richer |
| Doctor brief | `/api/v1/ai/doctor-brief` | **HARDEN** — useful differentiator, currently receives raw detector evidence |
| Proactive lifecycle | no complete persisted/prioritized observation lifecycle identified | **MISSING DIFFERENTIATOR** |
| Diabetologist skill | no `.skills/*/SKILL.md` dedicated to diabetes expertise/evidence review | **MISSING** |

No live API route was identified in the inspected routers for the standalone `prediction.py` or `correlations.py` helpers. That is not proof of global unreachability; they must remain classified as prototype/dormant until a call-graph gate proves otherwise.

## 3. Strongest component: personal response

`backend/diabetes/services/clinical/personal_response.py` is the architectural model to preserve.

It already enforces the right doctrine:

- repeated observations rather than one-off interpretation;
- at least 3 observations across at least 2 days;
- maximum 90-day synchronized-data window;
- demo exclusion;
- explicit positive context only;
- historical `no/good/ok` values are not treated as a synthetic control cohort;
- descriptive medians, not causal deltas;
- `limited/moderate/strong` is a product evidence-density grade, not a probability;
- no causal inference, prediction, treatment recommendation or significance claim.

This matches `docs/MEDICAL_DATA_PLAN.md` and `docs/SPECS.md` and should become the pattern for all future personalized clinical intelligence.

## 4. Blocking findings

### P0-1 — Treatment-oriented fallback semantics exist inside the detector engine

**Severity: BLOCKER before promoting the engine as expert clinical intelligence.**

Examples in `clinical/engine.py` include:

- suggesting rapid-acting insulin before a meal;
- suggesting discussion of basal insulin adjustment as the apparent solution to a detected pattern;
- prescribing a fixed carbohydrate snack after exercise.

The current structured insight path is partially protected because `sanitize_patient_visible()` replaces recognized structured clinical insight text with an observation-only envelope. That mitigation is valuable, but unsafe clinical semantics should not remain embedded as the detector's nominal fallback/action authority: other surfaces can consume raw pattern codes/evidence, and future refactors could bypass the current envelope.

**Required next action:** remove treatment optimization from detector-owned content; detectors return evidence-qualified observations only.

### P0-2 — Several observational associations are worded as causes

**Severity: BLOCKER.**

Examples:

- stress delta becomes “directly linked” to stress hormones;
- fatigue “worsens” glucose;
- poor sleep is described as causing the patient's observed glucose difference;
- food labels are converted to “sensitivity” from sparse logs.

This conflicts with the canonical contract: patient-entered context is observational, missing context is unknown, and association must not be promoted to causality.

**Required next action:** neutral observation vocabulary + explicit evidence basis + insufficiency state.

### P0-3 — Named Somogyi detector overstates certainty

**Severity: BLOCKER.**

`detect_somogyi_rebound()` labels two sparse night→morning pairs as “Effet Somogyi détecté” and supplies a mechanistic explanation.

Modern CGM literature treats post-hypoglycemic nocturnal hyperglycemia as a phenomenon requiring nuanced interpretation; the classical Somogyi hypothesis has been questioned and revisited rather than being suitable as a deterministic diagnosis from sparse journal pairs.

**Required next action:** remove the diagnostic label from patient authority. If retained at all, model only the neutral observation “nocturnal low followed by later high,” with modality/sufficiency requirements and evidence provenance.

### P0-4 — `correlations.py` uses pseudo-clinical confidence and unsafe historical controls

**Severity: BLOCKER if surfaced.**

The module computes a handcrafted numerical `confidence` from sample size and effect size and treats `stressed=no`, `exercise=no`, and `sleep=good` as control populations.

This conflicts with the current personal-response contract because historical neutral/negative values may have been materialized by old defaults. The numeric confidence is also not calibrated statistical or clinical confidence.

**Required next action:** replace this path with the `personal_response.py` evidence-density model or prove a separate statistically validated contract.

### P0-5 — `prediction.py` is not a clinically validated prediction engine

**Severity: BLOCKER if surfaced as clinical prediction.**

The implementation:

- fits a simple linear trend over sparse recent journal readings;
- adds fixed offsets for stress (`+12 mg/dL`), poor sleep (`+10`), activity (`-8`) and fatigue (`+6`);
- generates a handcrafted confidence score;
- exposes no calibration evidence, external validation, uncertainty interval, modality eligibility or prospective performance gate.

It therefore must not be promoted as patient-facing clinical prediction or as evidence of “diabetologist-level” reasoning.

**Required next action:** quarantine from patient authority; future prediction requires a separately scoped validation program.

### P0-6 — Emergency resource is hard-coded to France in diabetes alert templates

**Severity: CRITICAL for MENA locale safety.**

`clinical/alerts.py` contains `15 (SAMU)` in French emergency messages. IAmina's canonical locale contract explicitly requires jurisdiction-specific validated emergency resources before a locale enters a real-patient pilot.

**Required next action:** no hard-coded foreign emergency number in patient authority. Resolve through validated emergency-resource jurisdiction owned by shared core safety.

### P0-7 — Doctor brief consumes raw detector identity/evidence

**Severity: HIGH.**

`/api/v1/ai/doctor-brief` sends raw pattern codes and detector evidence into a generative summarization step. Output is passed through the no-prescription text policy, but that policy does not itself prove that causal wording, contested detector identity or evidence limitations were correctly represented.

**Required next action:** doctor brief must consume an evidence-qualified structured clinical observation contract, not raw legacy detector identity.

## 5. Proactivity gap

Current IAmina can analyze and narrate. It is not yet a full proactive longitudinal companion.

The missing product primitive is an **Insight Lifecycle**:

`NEW → MONITORING → PERSISTING / IMPROVING → RESOLVED / ESCALATED`

Each candidate insight should carry at minimum:

- observation code;
- patient/data scope;
- first/last observed time;
- evidence count and distinct-day count;
- data sufficiency state;
- normative source/version;
- evidence maturity (`standard_of_care`, `emerging_evidence`, `investigational`);
- actionability class;
- safety class;
- explanation limits;
- follow-up criterion;
- resolution criterion;
- clinician-handoff eligibility.

The prioritizer should optimize **clinical relevance and interruption cost**, not notification volume. A patient should usually see the one observation that most deserves attention, not every mathematically detectable pattern.

## 6. Differentiation target

IAmina should not try to beat CGM manufacturers at sensor hardware or raw glucose alarms.

The defensible layer is a **longitudinal clinical companion** that can safely answer:

- What materially changed since the patient's own baseline?
- Is the observation repeated enough to deserve attention?
- What evidence supports it?
- What is still unknown?
- Is this standard-of-care knowledge, emerging evidence, or investigational?
- Has the same pattern occurred before?
- What happened after it previously appeared?
- Does it need patient education, simple monitoring, or clinician review?
- What are the few highest-signal facts for the next consultation?

This is the intended “Clinical Twin” direction, while preserving the non-diagnosis/non-prescription boundary.

## 7. Maturity scorecard

| Axis | Score | Rationale |
|---|---:|---|
| Deterministic analytics | 8.5/10 | SQL-first metrics, existing parity/safety work |
| Safety architecture | 7.5/10 | strong shared gates, but legacy clinical semantics/jurisdiction drift remain |
| Personalization | 6.5/10 | `personal_response.py` is strong but narrow |
| Evidence provenance | 4.0/10 | clinical definitions are not uniformly versioned at detector level |
| Clinical reasoning quality | 4.5/10 | many useful detector ideas; several are overconfident or under-validated |
| Proactivity | 3.0/10 | analysis exists; prioritization/follow-up/resolution lifecycle does not |
| Clinician handoff | 5.0/10 | doctor brief exists but needs evidence-qualified input |
| **Overall clinical-intelligence maturity** | **5.8/10** | strong foundation, not yet a defensible expert moat |

## 8. Ordered follow-up LOTs

### P0-CLIN-INTEL-1 — Clinical semantics hardening

One responsibility: make every currently reachable detector/output obey the existing clinical authority contract.

Must cover:

- remove treatment/dose optimization semantics;
- neutralize causal claims;
- replace/retire Somogyi diagnostic naming;
- isolate unvalidated prediction/correlation prototypes;
- route emergency resources through validated jurisdiction handling;
- make doctor-brief input evidence-qualified;
- add permanent regression tests.

**Gate:** no reachable patient/doctor surface may turn observational data into unsupported causality, diagnosis or treatment optimization.

### P1-CLIN-SKILLS — Diabetologist Skills Foundation

Create repository-owned diabetes expertise procedures, at minimum:

1. `diabetes-clinical-reasoning/SKILL.md`
2. `diabetes-proactive-intelligence/SKILL.md`
3. `diabetes-evidence-intelligence/SKILL.md`

These are execution/evidence procedures, not prompts that can override deterministic clinical authority.

### P1-EVIDENCE — Versioned Diabetes Evidence Registry

Every clinical rule/metric/observation references source, publication/version, population, modality, evidence level, review date and supersession state.

### P2-CLINICAL-TWIN — Longitudinal Observation Memory

Track recurring evidence-qualified observations without promoting model inference into clinical fact.

### P2-PROACTIVE — Prioritization + Insight Lifecycle

Implement candidate scoring, interruption budget, monitoring, resolution and escalation logic.

### P2-DOCTOR — Consultation Intelligence

Generate an evidence-qualified change-since-last-visit brief with source observations and uncertainty.

### P3-HORIZON — Evidence Horizon Scanner

Separate current standard of care from emerging evidence and investigational/future work. No emerging paper silently changes patient rules.

### P3-EVALS — Clinical Intelligence Evals

Build a clinician-reviewed scenario bank, negative cases, false-positive tests, longitudinal cases and safety regression gates. “Expert” becomes a measured claim, not a prompt claim.

## 9. External clinical references used for this audit

1. American Diabetes Association Professional Practice Committee for Diabetes. **Standards of Care in Diabetes—2026: Glycemic Goals, Hypoglycemia, and Hyperglycemic Crises.** Diabetes Care. 2026;49(Suppl 1):S132–S149. DOI: `10.2337/dc26-S006`.
2. American Diabetes Association Professional Practice Committee for Diabetes. **Standards of Care in Diabetes—2026: Diabetes Technology.** Diabetes Care. 2026;49(Suppl 1):S150–S165. DOI: `10.2337/dc26-S007`.
3. **Post-hypoglycemic nocturnal hyperglycemia in type 1 diabetes: the Somogyi hypothesis revisited.** CGM analysis in 755 FreeStyle Libre 2 users with T1D; PubMed PMID `40465171` (2025). The paper explicitly notes that the plausibility of the classical hypothesis has been questioned and studies the phenomenon using CGM rather than treating sparse paired readings as diagnostic proof.

These references inform the audit and future rule-review requirements; they do not directly authorize new patient-facing recommendations.

## 10. P0 closeout criteria

This audit LOT is complete only when:

- the assessment is reviewed against current code and canonical clinical contracts;
- findings are converted into ordered forward work in the canonical roadmap before merge/closeout;
- no clinical runtime behavior is silently changed inside this audit LOT;
- Clinical Safety Reviewer performs an isolated pass;
- Release Certifier verifies exact-head evidence and documentation hygiene;
- merge and post-merge gates are verified before claiming 100% completion.
