# P2-PROACTIVE — Deterministic Attention & Insight Lifecycle

> **Status:** certification candidate in PR #138. Closure requires exact-head CI + PostgreSQL + migration drift, Clinical Safety Reviewer, Release Certifier, expected-head locked merge and post-merge `main` CI + drift.

## 1. Purpose

P2-PROACTIVE decides which already-governed longitudinal diabetes observation deserves **internal product attention now**.

It does not create patient truth, diagnose, predict, prescribe, calculate a clinical risk score, alter emergency handling, generate a patient message or deliver a notification.

The source of clinical observation truth remains the certified `ClinicalObservationState` from P2-CLINICAL-TWIN.

## 2. Authority and emergency precedence

The proactive engine accepts only certified deterministic `personal_response` observations:

- truth kind: `deterministic_derivation`;
- source producer: `diabetes.personal_response.v1`;
- source evidence: `rule.personal-response.repetition.v1`;
- evidence registry authority: `GOVERNED_RULE`;
- evidence supersession state: `current`.

The evidence authority/supersession check runs **before** the proactive engine requests a clinical-twin refresh. A non-governed or superseded source rule therefore fails closed before source mutation.

Canonical deterministic emergency handling is an upstream prerequisite. The proactive selector requires explicit `EmergencyClearance.CLEAR` before any source refresh or proactive-state write. `UNKNOWN` fails closed; `ACTIVE` suppresses proactive attention. Emergency handling never enters or competes inside the attention budget.

## 3. Separate product-attention state

`ClinicalInsightState` is a one-to-one diabetes-owned state attached to a certified `ClinicalObservationState`.

It records only attention/lifecycle bookkeeping:

- observation key;
- deterministic/source provenance;
- current proactive lifecycle state;
- allowed next step;
- last deterministic source snapshots;
- material/decision/surfacing fingerprints;
- pending reason codes for candidates not yet selected;
- first/last internal selection timestamps and selection count.

This state is **not** a diagnosis/problem list, clinical emergency state, probability, treatment effect, companion memory or patient-visible notification record.

Database constraints independently reject:

- non-deterministic proactive provenance;
- unapproved proactive producer;
- unapproved source producer/evidence rule;
- direct `ESCALATED` writes in v1;
- next steps outside `MONITOR` / `COLLECT_MISSING_DATA`.

## 4. Explicit priority vector — no black-box score

P2-PROACTIVE exposes an auditable `PriorityVector` rather than a scalar score:

- `safety_time_sensitivity`;
- `clinical_relevance`;
- `persistence`;
- absolute descriptive distance from the recorded personal baseline;
- evidence strength;
- evidence maturity;
- actionability;
- interruption cost;
- observation count;
- distinct-day count;
- activation recurrence count;
- recency.

V1 ordering is deterministic and lexicographic. No `risk_score`, `confidence_score`, `priority_score`, companion `concern_level`, emotion, engagement signal, model inference or deep-memory field is clinical prioritization authority.

## 5. Lifecycle semantics

Supported state vocabulary:

`NEW → MONITORING → PERSISTING / IMPROVING → RESOLVED`

`ESCALATED` exists only as reserved vocabulary and is structurally unreachable in v1 until a separately governed safety/handoff criterion is approved.

Semantics:

- `NEW`: first internally selected eligible insight;
- `MONITORING`: selected/known insight without a stronger material lifecycle transition;
- `PERSISTING`: a materially changed observation with repeated activation episodes;
- `IMPROVING`: a materially changed observation whose descriptive baseline delta moved **toward the recorded personal baseline**;
- `RESOLVED`: a previously observed descriptive pattern is inactive and has had no supporting sighting across a full **eligible** evidence horizon.

`IMPROVING` is not treatment effect, causality or recovery. `RESOLVED` is not disease/problem resolution. Sparse/missing data cannot create `RESOLVED`.

Lifecycle transitions are driven by material source changes and governed time criteria, not API read frequency.

## 6. Attention budget and idempotency

A decision call returns **at most one** candidate.

- unchanged previously selected decisions are suppressed;
- material source changes may make an insight eligible to surface again;
- candidates not selected because another item wins retain pending reason codes;
- selection clears only the selected candidate's pending reasons;
- first `NEW` selection is acknowledged into stored `MONITORING` state so an identical next read does not create a second event.

"Surfaced" in this model means **selected by the internal deterministic attention budget**. It does not mean that a patient notification, message, push, local alert or clinician handoff was delivered.

## 7. Allowed actions

V1 proactive actions are intentionally narrow:

- `MONITOR` when the governed dataset is eligible;
- `COLLECT_MISSING_DATA` when a previously known observation exists but current data are insufficient for a fresh governed refresh.

No education prescription, clinician handoff, emergency action, treatment recommendation, medication change, dose suggestion or autonomous clinical instruction is enabled here.

## 8. Patient/API boundary

P2-PROACTIVE adds no patient-facing API field, endpoint, notification transport, scheduler or UX surface.

A later delivery LOT must independently certify:

- user-visible wording;
- localization/RTL;
- notification permissions and cadence;
- dismissal/snooze controls;
- emergency precedence at the delivery boundary;
- accessibility and interruption cost;
- any clinician-handoff transport.

## 9. Regression gates

Certification must prove:

- explicit emergency clearance before any write;
- active emergency suppresses proactive state;
- non-governed/superseded source evidence stops before clinical-twin refresh;
- first eligible insight selection and unchanged repeat suppression;
- max-one attention budget with pending-candidate preservation;
- material support re-surfacing;
- recurrent activation → `PERSISTING` only on material change;
- baseline movement → descriptive `IMPROVING` only;
- full eligible-horizon absence required for `RESOLVED`;
- sparse data never resolves and may only request missing data;
- strict patient isolation;
- direct ORM rejection of unapproved provenance, escalation and action;
- explicit `PriorityVector` and absence of companion/scalar-score authority;
- PostgreSQL full suite, migration drift and permanent repository safety gates remain green.
