# IAMINA — Whole-App Context Router

Status: IN PROGRESS  
PR: #861

## Goal

Make the Companion understand patient-owned application-data requests deterministically before any generative narration.

The router must decide **where to read**, fetch only patient-scoped persisted facts, and return a bounded descriptive result. An LLM must never decide data ownership, source selection, emergency status, treatment changes, dose, or missing facts.

## Success criteria

- all 12 gaps discovered by deterministic audit #860 are claimed by an explicit route;
- every claimed route reads a canonical patient-owned source or returns an explicit persistence/availability limitation;
- no route invents missing data;
- no diagnosis, causality, dose, prescription or treatment change;
- unrelated prompts remain unclaimed;
- deterministic context responses are verified before emission;
- at least one end-to-end demo contract proves the provider gateway is not invoked;
- exact-head CI and Django migration drift are green before merge.

## Route matrix

| Intent | Canonical source | Behavior |
| --- | --- | --- |
| diabetes type | DiabetesProfile | read-only |
| treatment | DiabetesProfile | read-only |
| configured glucose range | DiabetesProfile + provenance | read-only; no target-authority inflation |
| meal history | LogEntry | read-only journal retrieval |
| exact historical glucose | LogEntry | exact recorded-hour retrieval; no interpolation |
| sleep history | LogEntry.sleep_quality | descriptive counts |
| stress history | LogEntry.stressed | descriptive counts |
| latest lab/document | LabReport structured fields | confirmed persisted values only |
| imported medications | document persistence contract | explicit limitation: preview medications are not persisted structurally |
| latest CGM reading | CGMReadingRecord | exact latest recorded transport fact |
| pending proactive insight | preview_proactive_insights | read-only preview; no attention-budget mutation |
| paired meals | compute_paired_meal_response | explicit meal_episode_id links only |

## Safety invariants

1. Input safety remains upstream of this router.
2. The router is L1 descriptive authority only.
3. Patient identity is server-side; no caller-supplied patient id is accepted by the chat API.
4. The router may expose only persisted patient-owned facts already reachable through the diabetes module.
5. Missing data is stated as missing.
6. Deterministic output is the fallback and verifier authority; generative rewrites cannot alter it.
7. No Vercel deployment without explicit owner authorization.

## Current implementation

- whole_app_context_decision.py: intent classification + patient-scoped read adapters.
- whole_app_context_narration_verifier.py: exact deterministic-copy verification.
- DiabetesEngine.resolve_patient_advice(): routes whole-app context before generative narration.
- clinical_validation.py: diabetes.context.* registered as EXPERIMENTAL / max L1 while certification is in progress.
- regression tests cover the 12 audit gaps, source reads, false-positive treatment wording, deterministic rewrite rejection, and demo provider bypass.

## Closeout rule

Do not mark this chantier CLOSED until exact-head tests are green, the PR is merged with expected-head protection, post-merge evidence is green (or equivalent exact-SHA recertification), and this document is synchronized to those proofs.
