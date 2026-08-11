# IAmina — Competitive benchmark remediation track

> **Baseline date:** 2026-08-10  
> **Authority:** supporting evidence for benchmark remediation. `docs/ROADMAP.md` remains the single forward tracker and must be updated at LOT closeout without overwriting newer roadmap state.

## Why this track exists

A proof-only comparison against current diabetes leaders identified remaining product gaps around ecosystem depth and real-world evidence: device/data connectivity, clinician workflows, caregiver sharing, interoperability, and a mature real-patient pilot.

This track must not weaken or bypass the existing MENA safety/compliance critical path. No benchmark LOT authorizes a first real patient before the existing pilot safety/compliance gate is fully closed.

## Evidence rule

No global competitive score is canonical in this file. A numeric score may be versioned only after a complete criterion-by-criterion matrix exists with IAmina proof or `NON PROUVÉ`, current official competitor evidence, scoring rule and observation date.

## Remediation order

| LOT | Responsibility | Priority | Closure boundary |
|---|---|---|---|
| **P0-BENCH-1** | Pilot evidence & retention contract | P0 | versioned rolling D1/D7/D30/D90; mature denominators; reproducible `as_of`; explicit approved-roster scope; SQLite/PostgreSQL proof; no invented success threshold |
| **P1-BENCH-2** | Device/Data Integration Foundation | P1 | provenance-aware ingestion contract and prioritized MENA device/source matrix before vendor integrations |
| **P1-BENCH-3** | IAmina Clinician Connect | P1 | explicit invitation/consent, time-bounded read access, summary/report, revocation and auditability; no prescribing authority |
| **P1-BENCH-4** | Care Circle | P1 | granular patient-controlled sharing, revocation and alert/data scopes |
| **P2-BENCH-5** | Standards interoperability | P2 | evidence-backed FHIR/export mapping for data actually supported by IAmina |
| **P2-BENCH-6** | External assurance & real-world evidence | P2 | completed pilot analysis, limitations and external assurance evidence as applicable |

## P0-BENCH-1 — exact contract

### Problems reproduced

1. D1 and D7 could treat patients younger than the measured horizon as non-retained, while D30/D90 excluded immature patients.
2. Retention/funnel evidence lacked one reproducible `as_of` cutoff, so later events could alter a historical snapshot.
3. Computation was product-wide only, allowing unrelated patients to contaminate a future approved pilot cohort.

The implementation preserves **rolling retention**: a return on or after the horizon counts, bounded by the evidence cutoff.

### Acceptance criteria

- [x] D1/D7/D30/D90 denominators include only patients mature enough for the corresponding horizon.
- [x] Each horizon exposes `eligible_d1/d7/d30/d90` separately from total cohort size.
- [x] `cohort_ready_dN` is equivalent to `eligible_dN > 0`.
- [x] Retention semantics are named and versioned.
- [x] One timezone-aware `as_of` bounds acquisition, return, funnel and engagement evidence.
- [x] Product-wide computation remains available when no roster is supplied.
- [x] Explicit patient roster scopes all evidence; empty roster fails closed; invalid IDs are rejected.
- [x] Result exposes contract version, semantics, scope, roster size, `as_of` and computation timestamp.
- [x] Permanent regressions cover immature horizons, rolling retention, future-event exclusion, roster isolation and immutable output.
- [ ] SQLite and authoritative PostgreSQL behavior pass exact-head CI; migration drift remains green.
- [ ] Database & Migration Reviewer FINAL PASS.
- [ ] Release Certifier CERTIFIED on final SHA.
- [ ] Expected-head merge and post-merge CI/drift verified.
- [ ] `docs/ROADMAP.md` closeout entry added against the current roadmap head without reverting newer UX/security state.
- [x] No schema migration, patient-facing clinical logic, treatment behavior, diagnosis/prescription behavior or generative authority is introduced.
- [x] No D7/D30/D90 success threshold is invented.

### Boundary

`compute_retention_metrics(..., patient_ids=[...])` measures an explicit roster but does not decide pilot membership. The approved roster remains an input from pilot governance. Product-wide metrics must not be presented as pilot results when a restricted cohort is intended.

Real-patient cohort execution remains blocked by the existing pilot safety/compliance gate.
