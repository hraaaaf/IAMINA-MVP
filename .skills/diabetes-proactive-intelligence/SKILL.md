# Skill — Diabetes Proactive Intelligence

## Purpose
Decide whether an already evidence-qualified diabetes observation deserves attention now, later, or not at all, and how to follow it longitudinally without creating alert fatigue or autonomous treatment authority.

This skill is mandatory for LOTs that change proactive insights, prioritization, nudges, follow-up, longitudinal pattern state, notification semantics, clinician handoff prioritization or "what matters now" logic.

## Preconditions
Proactive intelligence may consume only:

- observed/patient-entered facts with provenance;
- deterministic clinical metrics and observations that passed eligibility checks;
- explicit preferences and care context;
- prior evidence-qualified insight state;
- evidence maturity from `.skills/diabetes-evidence-intelligence/SKILL.md`.

It must not consume model inference as if it were patient truth. It must not bypass deterministic emergency routing.

## Priority model
Do not reduce prioritization to a single opaque score unless the score is validated and auditable. Reason over an explicit priority vector:

1. **Safety/time sensitivity** — could delay materially increase risk?
2. **Clinical relevance** — is the observation meaningful for this population/context?
3. **Persistence/recurrence** — repeated across distinct eligible periods or a one-off?
4. **Change from personal baseline** — materially different from the patient's own eligible history?
5. **Evidence density** — enough observations, days and coverage to support surfacing?
6. **Actionability within companion scope** — can the next step be education, monitoring, missing-data collection, clinician preparation or emergency routing without treatment optimization?
7. **Confidence/evidence maturity** — standard-of-care rule, governed descriptive pattern, emerging evidence, or investigational signal?
8. **Interruption cost** — is surfacing now worth the attention burden?

Interruption cost can suppress low-value noise; it can never suppress deterministic emergency handling or an explicitly governed urgent safety action.

## Insight lifecycle
Use the state model:

`NEW → MONITORING → PERSISTING / IMPROVING → RESOLVED / ESCALATED`

State transitions require deterministic evidence, not model sentiment.

- `NEW`: first eligible occurrence that passes the surfacing rule.
- `MONITORING`: not yet enough longitudinal evidence for persistence/resolution.
- `PERSISTING`: repeated eligible evidence continues beyond the rule-defined persistence criterion.
- `IMPROVING`: eligible evidence trends toward the patient's baseline/target without claiming causality.
- `RESOLVED`: the observation no longer meets the governed criterion for the required resolution window.
- `ESCALATED`: a governed safety/clinical handoff criterion is met; escalation is not a diagnosis.

Never infer `RESOLVED` from missing data. Missing means unknown.

## Attention-budget rules
- Prefer the single highest-value insight when several compete for attention.
- Group related observations when this reduces duplication without hiding distinct safety signals.
- Suppress repeats that add no new information; preserve state internally.
- Re-surface when severity, persistence, evidence density or required action materially changes.
- Do not congratulate or alarm based only on short noisy windows.
- Avoid generic wellness nudges when a higher-priority diabetes-specific issue exists.
- Respect explicit notification preferences unless a deterministic safety contract requires otherwise.

## Proactive output contract
A patient-facing proactive item must be traceable to:

- `what_changed`
- `why_it_is_surfacing_now`
- `evidence_window`
- `personal_baseline_comparison` when eligible
- `evidence_density`
- `limitations_or_missing_data`
- `state`
- `allowed_next_step`
- `escalation_class`
- `source_version`

Wording should make clear the difference between observation, possible explanation and recommendation to seek clinician input.

## Follow-up rules
- Every follow-up window must be rule-defined, evidence-defined or explicitly labeled as a product reminder cadence; never invent a medically authoritative interval from a language model.
- Compare like with like: compatible modality, time-of-day definition, sufficient coverage and relevant treatment/context stability where required.
- Record whether an intervention/context change was merely reported versus clinically prescribed elsewhere.
- IAmina may remember that "after X was reported, Y changed"; it may not conclude "X caused Y" without governed evidence.
- Do not learn a treatment recommendation from one patient's past outcome.

## Safe action classes
Allowed terminal actions are:

- `EDUCATE`
- `MONITOR`
- `COLLECT_MISSING_DATA`
- `PREPARE_CLINICIAN_DISCUSSION`
- `CLINICIAN_HANDOFF`
- `DETERMINISTIC_EMERGENCY_ROUTE`

No proactive path may emit autonomous diagnosis, prescription, dose calculation, medication titration or treatment optimization.

## Hard stops
Block the LOT if it introduces:

- a black-box "risk score" with no validated definition/calibration;
- urgency inferred only by an LLM;
- notification spam as a substitute for prioritization;
- resolution inferred from silence/missing data;
- causal claims from before/after correlation;
- treatment advice derived from learned personal patterns;
- an evidence horizon paper that directly changes patient behavior without evidence-governance promotion;
- prioritization that can delay or override deterministic emergency handling.

## Required companion skills
Load `.skills/diabetes-clinical-reasoning/SKILL.md`, `.skills/diabetes-evidence-intelligence/SKILL.md`, `.skills/clinical-safety/SKILL.md` and `.skills/release-certification/SKILL.md` for any implementation LOT using this skill.
