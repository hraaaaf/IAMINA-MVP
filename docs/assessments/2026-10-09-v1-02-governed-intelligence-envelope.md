# V1-02 — Governed patient intelligence envelope (first backend slice)

> Status: **OPEN / NOT CERTIFIED**. Scope is a read-only, internal Clinical Twin projection; it is **not** a released all-surface Intelligence Engine, verified medical device, or LLM payload.
> Baseline: `main@13b7cce12c86daf60119fb703f22e8c6c192cf8d`. Branch: `feat/v1-02-governed-intelligence-envelope-20261009`.
> Independent of V1-01 branch: no edits to clinical calculators, KPI APIs, user-facing copy, Flutter, provider routing or migrations.

## Goal / success / proof

**Goal:** start a single versioned, patient-scoped, deterministic fact/observation envelope consumable by later authorized surfaces, with provenance, uncertainty, missingness, eligibility, producer version and explicit authority ceiling.

**First-slice acceptance:** read the already-governed Clinical Twin personal-pattern projection and optionally the V2-D source-separated snapshot on an explicitly authorized window/contract; validate the original evidence admission mapping, producer/version/uncertainty agreement, subject ID, status/data consistency and timestamps; preserve missing evidence, do not invent observations. Patient A must never return patient B's records. No generation, provider/LLM calls, treatment action, scheduling, database writes, new public endpoint or unauthorized CGM comparisons.

**Proof plan:** Django tests on SQLite and the PostgreSQL source-of-truth job, malformed/foreign/pseudo-evidence negative cases, exact-HEAD lint/architecture/security/DB gates; specialist adversarial safety/security/data reviews; explicit independent certifier before any merge. Tests to be recorded only after actual execution.

## Existing component inventory (verified statically on main)

| Existing authority | Reuse in this slice | Guardrail |
| --- | --- | --- |
| `ClinicalObservationState` / `observation_memory.py` | Pre-existing patient-owned governed lifecycle | No new writes or second detector |
| `companion_pattern_intelligence.py` | Existing patient-ID filtered projection, evidence-density and descriptive baseline semantics | Reject invalid state/producer/evidence; no diagnosis |
| `companion_evidence_uncertainty.py` + `evidence_registry.py` | Governed rule/producer admission, supporting-source maturity and explicit missingness | An external source does not automatically authorize a clinical rule |
| `multi_source_fusion.py` and `governed_longitudinal.py` | **Composed conditionally:** explicit `GovernedSourceRequest` typed window and V2-C/V2-D contract | Preserve source population, ref, approved glucose concept/type/unit, global sufficiency gate; never mix CGM/manual/import |
| `companion_overview.py`, `companion_change.py` | **Not yet composed:** existing change/review UI projection | A review anchor is a user action, not inferred from chat |
| `whole_app_context_decision.py` | **Not yet composed:** deterministic fact-question router | The patient-context/LLM external-egress boundary is separate V1-03 work |

## First-slice contract

- Internal `patient-intelligence-envelope.v1`, no public endpoint or direct frontend integration in this PR.
- `patient_id` is validated as an exact positive integer; all underlying Clinical Twin reads are patient-filtered.
- `status` is `ready` only with admitted governed observations **or** an explicitly requested V2-D source projection whose every population is ready; otherwise `insufficient_data` with explicit missing data. Envelope `missing_data` includes per-source insufficiency codes even when Clinical Twin observations are present; the top-level readiness remains descriptive and partial consumers must inspect both sections.
- Each admitted observation retains source version, time span, descriptive lifecycle/baseline, evidence registry provenance (rule, producer, maturity, authority, supporting citations), uncertainty (evidence density, missing data, limitations), and a descriptive-only ceiling.
- Evidence density is repetition density, **not** clinical confidence. `llm_egress_authorized=False` is an explicit fail-closed marker but is **not** a substitute for V1-03 enforcement.
- Optional governed longitudinal evidence requires an explicit typed request with window and V2-D contract. The assembler checks patient identity on each fact, requested populations, contract/window consistency, source-ref counts and the existing V2-D fact/day sufficiency minima. It preserves source-specific medians **only when the whole requested V2-D contract is ready**, i.e. every explicitly requested population has sufficient evidence; otherwise **all** medians in this optional source projection are unavailable. It additionally verifies approved source type, glucose concept, mg/dL unit/UCUM, accepted decision, and provenance reference on every projected fact. Raw facts and any cross-source aggregate are not added to the envelope.
- Both the envelope and source snapshot permanently mark `clinical_metrics_authorized=False`. A V2-D `ready` state means **descriptive source sufficiency only**, never verified clinical CGM coverage, GMI/TIR or target achievement. No configured target becomes a clinician-confirmed target, no sensor coverage is inferred from manual records, no automatic safety/clinical action is activated.

## Planned subsequent V1-02 increments (not completed by first slice)

1. **Implemented initial explicit source-separated composition, tests pending:** V2-C/V2-D opt-in with source refs, per-population sufficiency and cross-patient forgery negative tests. Tests added for invalid cross-patient CGM-session and import identity; still need broader temporal/session fixture parity and runtime consumer certification.
2. Compose Clinical Twin changes and target assessments *only if* independently governed producer/evidence context already certifies the specific claim. Otherwise explicit unavailable.
3. Build authenticated, privacy-reviewed internal API projection for Home and Reports; compare both to the same original envelope with fixed fixtures.
4. Route IAmina through the same governed envelope **only after V1-03 outbound egress boundary is independently proven**. Do not pass raw patient context to an LLM.
5. Certify all three consumers, provenance, missingness and clinical gate parity; complete specialist review, exact-HEAD CI, Perfection Pass, merge and post-merge.

## Material step score (provisional; no binary proof yet)

Goal: first deterministic patient-scoped envelope.
Success criterion: provenance-preserving, read-only fail-closed source projection with passing independent oracles.
Evidence: added code and negative tests. Previous HEAD `fd2e213f` CI #37869147728 failed Ruff I001 and one incorrect negative test fixture (2805 PG tests passed). Imports and fixture corrected on `7b0b813b`; further global V2-D sufficiency/provenance hardening committed after that. **Fresh exact final-HEAD CI still to check.**
Critical dimensions: privacy, provenance, clinical authority, source scope, versioning, release gate.
EXECUTION_SCORE: 7.0/10 (provisional)
ADVERSARIAL_SCORE: 6.8/10 (provisional)
Gap: 0.2
Applicable caps: required runtime/independent evidence missing (<=7.9)
RETAINED_SCORE: 6.8/10
Status: OPEN
Remaining weaknesses: broad sensor-session/time-window oracles and all three UI consumers not completed; source-ref lineage limited by upstream Clinical Twin projection; atomic read consistency across independently fetched sources not proven; exact final-HEAD CI and independent clinical/security/data review pending.
Next exact action: inspect CI on the final HEAD, correct failures if any, obtain independent clinical/data/security review, then extend the authorized consumers while maintaining V1-03 hard AI egress separation. Do not merge on green CI alone.

No Vercel deployment authorized or performed. Historical P5 pilot pre-real-patient gates remain unchanged.
