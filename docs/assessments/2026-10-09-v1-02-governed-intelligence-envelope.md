# V1-02 — Governed patient intelligence envelope (first backend slice)

> Status: **OPEN / NOT CERTIFIED**. Scope is a read-only, internal Clinical Twin projection; it is **not** a released all-surface Intelligence Engine, verified medical device, or LLM payload.
> Baseline: `main@13b7cce12c86daf60119fb703f22e8c6c192cf8d`. Branch: `feat/v1-02-governed-intelligence-envelope-20261009`.
> Independent of V1-01 branch: no edits to clinical calculators, KPI APIs, user-facing copy, Flutter, provider routing or migrations.

## Goal / success / proof

**Goal:** start a single versioned, patient-scoped, deterministic fact/observation envelope consumable by later authorized surfaces, with provenance, uncertainty, missingness, eligibility, producer version and explicit authority ceiling.

**First-slice acceptance:** read only the already-governed Clinical Twin personal-pattern projection; validate the original evidence admission mapping, producer/version/uncertainty agreement, subject ID, status/data consistency and timestamps; preserve missing evidence, do not invent observations. Patient A must never return patient B's records. No generation, provider/LLM calls, treatment action, scheduling, database writes, new public endpoint or unauthorized CGM comparisons.

**Proof plan:** Django tests on SQLite and the PostgreSQL source-of-truth job, malformed/foreign/pseudo-evidence negative cases, exact-HEAD lint/architecture/security/DB gates; specialist adversarial safety/security/data reviews; explicit independent certifier before any merge. Tests to be recorded only after actual execution.

## Existing component inventory (verified statically on main)

| Existing authority | Reuse in this slice | Guardrail |
| --- | --- | --- |
| `ClinicalObservationState` / `observation_memory.py` | Pre-existing patient-owned governed lifecycle | No new writes or second detector |
| `companion_pattern_intelligence.py` | Existing patient-ID filtered projection, evidence-density and descriptive baseline semantics | Reject invalid state/producer/evidence; no diagnosis |
| `companion_evidence_uncertainty.py` + `evidence_registry.py` | Governed rule/producer admission, supporting-source maturity and explicit missingness | An external source does not automatically authorize a clinical rule |
| `multi_source_fusion.py` and `governed_longitudinal.py` | **Not yet composed:** V2-C/V2-D contracts identified | Requires explicitly selected populations, source separation and insufficiency gates; never silently merge CGM/manual/import |
| `companion_overview.py`, `companion_change.py` | **Not yet composed:** existing change/review UI projection | A review anchor is a user action, not inferred from chat |
| `whole_app_context_decision.py` | **Not yet composed:** deterministic fact-question router | The patient-context/LLM external-egress boundary is separate V1-03 work |

## First-slice contract

- Internal `patient-intelligence-envelope.v1`, no public endpoint or direct frontend integration in this PR.
- `patient_id` is validated as an exact positive integer; all underlying Clinical Twin reads are patient-filtered.
- `status` is `ready` only with admitted governed observations; otherwise `insufficient_data` with explicit missing data.
- Each admitted observation retains source version, time span, descriptive lifecycle/baseline, evidence registry provenance (rule, producer, maturity, authority, supporting citations), uncertainty (evidence density, missing data, limitations), and a descriptive-only ceiling.
- Evidence density is repetition density, **not** clinical confidence. `llm_egress_authorized=False` is an explicit fail-closed marker but is **not** a substitute for V1-03 enforcement.
- No configured target becomes a clinician-confirmed target, no sensor coverage is inferred from manual records, no automatic safety/clinical action is activated.

## Planned subsequent V1-02 increments (not completed by first slice)

1. Compose validated source-separated longitudinal facts via explicit opt-in V2-C/V2-D contracts, with source refs/eligibility and cross-patient/invalid-session tests.
2. Compose Clinical Twin changes and target assessments *only if* independently governed producer/evidence context already certifies the specific claim. Otherwise explicit unavailable.
3. Build authenticated, privacy-reviewed internal API projection for Home and Reports; compare both to the same original envelope with fixed fixtures.
4. Route IAmina through the same governed envelope **only after V1-03 outbound egress boundary is independently proven**. Do not pass raw patient context to an LLM.
5. Certify all three consumers, provenance, missingness and clinical gate parity; complete specialist review, exact-HEAD CI, Perfection Pass, merge and post-merge.

## Material step score (provisional; no binary proof yet)

Goal: first deterministic patient-scoped envelope.
Success criterion: provenance-preserving, read-only fail-closed source projection with passing independent oracles.
Evidence: code and added tests; **exact-HEAD CI not yet observed at creation**.
Critical dimensions: privacy, provenance, clinical authority, source scope, versioning, release gate.
EXECUTION_SCORE: 7.0/10 (provisional)
ADVERSARIAL_SCORE: 6.8/10 (provisional)
Gap: 0.2
Applicable caps: required runtime/independent evidence missing (<=7.9)
RETAINED_SCORE: 6.8/10
Status: OPEN
Remaining weaknesses: not yet integrated with longitudinal/multisource or all three UI consumers; source-ref lineage limited by upstream Clinical Twin projection; no current CI or independent review at time of creation.
Next exact action: inspect exact-HEAD CI, remediate tests, validate security and clinical boundaries; continue source-separated composition without depending on V1-01 calculator changes.

No Vercel deployment authorized or performed. Historical P5 pilot pre-real-patient gates remain unchanged.
