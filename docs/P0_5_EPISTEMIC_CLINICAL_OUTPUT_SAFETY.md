# P0.5 — Epistemic Clinical Output Safety

> **Status:** ✅ Implementation CLOSED 100%; canonical closeout certification is owned by the documentation-only PR containing this file.  
> **Parent:** GitHub issue #119.  
> **Scope:** patient-visible claim authority for deterministic clinical insights and generative summary / doctor-brief narration.  
> **Non-scope:** no detector threshold/formula change, no diagnosis/prescription/treatment logic, no provider-routing change, no patient-data schema/migration and no UX redesign.

## Problem

IAmina already separated deterministic clinical calculations from generative narration, but compatibility-era presentation strings still had more authority than the underlying evidence justified.

Two distinct risks remained:

1. **Structured insight cards:** a deterministic detector could carry a legacy title/content/action that named a mechanism, implied causality or suggested a therapeutic workaround. A malformed/adversarial model response could also attempt to upgrade the same pattern into a diagnosis-like or treatment-like statement.
2. **Summary / doctor brief:** the generative prompt received semantic detector names/codes and included a legacy therapeutic few-shot example. This allowed the model to turn observational KPI/pattern context into a named phenomenon, asserted mechanism, causal claim or intervention.

P0.5 closes those two authority gaps without changing what the deterministic engines detect.

---

## P0.5A — Patient-visible insight envelope

**PR:** #120  
**Exact certified head:** `18f14805a240594071a147ad527448a7dcee909b`  
**Merge commit:** `8a941185511b1c0e96b0acb9754794cdfb6209b3`

### Contract

The final `sanitize_patient_visible()` boundary recognizes the stable structured clinical-insight shape:

```text
code
priority
icon
title
content
action
```

It preserves only stable metadata (`code`, `priority`, `icon`) as supplied by the deterministic pipeline. The patient-visible `title`, `content` and `action` are replaced by a deterministic observation-only envelope.

The envelope is available in:

- French;
- English;
- Modern Standard Arabic;
- Moroccan Darija in Arabic script.

It explicitly states that the observed trend alone does **not** establish a cause or diagnosis and offers only a non-therapeutic next step: note the context and prepare the observation for discussion with a healthcare professional.

Therefore:

- detector names do not become patient-facing diagnoses;
- legacy fallback advice does not survive a provider failure;
- adversarial model text cannot turn a structured insight into a causal/mechanistic claim;
- insulin/treatment advice cannot survive the structured insight boundary;
- detector thresholds, formulas and internal codes remain unchanged.

### Executable evidence

Regression contracts prove:

- metadata survives while generative/legacy authority is removed;
- gateway failure still returns a safe observation-only structure;
- adversarial diagnosis-like, causal and insulin-advice text is discarded;
- FR/EN/AR/ar-MA envelopes preserve the evidence ceiling;
- unrelated dictionary/string output retains the pre-existing no-prescription sanitation behavior.

### Certification

- Exact-head CI #1680 — **SUCCESS**.
- Exact-head migration drift #1492 — **SUCCESS**.
- Clinical Safety Reviewer — **PASS** on `18f14805…`.
- Release Certifier — **GO** on `18f14805…`.
- Expected-head locked merge — **SUCCESS**.
- Post-merge CI #1681 on `8a941185…` — **SUCCESS**.
- Post-merge drift #1493 — **SUCCESS**.

**P0.5A = CLOSED 100%.**

---

## P0.5B — Summary / doctor-brief evidence ceiling

**PR:** #121  
**Exact certified head:** `4ac2f3a9a0c86ffad4386ff22bb9b75b30b8a190`  
**Merge commit:** `9febaaf96b9b17d716f183d2adae625f11d1dce2`

### Input authority

`SUMMARY_USER` is now KPI/stat evidence-only.

The prompt no longer exposes a `{patterns}` placeholder, so the legacy `patterns=` argument cannot leak semantic detector names/codes into the model context. The legacy therapeutic few-shot example was removed.

The prompt explicitly forbids the model from:

- upgrading an association or temporal sequence into proven causality;
- naming a syndrome, phenomenon, physiological mechanism or diagnosis from the supplied data alone;
- proposing food, exercise, timing, medication or insulin interventions;
- turning `key_insight` into a recommendation;
- adding causal/diagnostic interpretation to `doctor_brief`.

### Output authority

`core.epistemic_safety` adds a focused multilingual fail-closed guard for the exact structured summary schema:

```text
narrative
key_insight
doctor_brief
```

If one generated field contains a prohibited causal/diagnostic/mechanistic assertion or unauthorized intervention, only that field is discarded to an empty value. Safe sibling fields remain intact.

The guard is intentionally scoped to this exact summary/doctor-brief schema; other parser schemas are unchanged by P0.5B.

### Executable evidence

Regression contracts prove:

- semantic detector names such as compatibility-era named mechanisms cannot enter `SUMMARY_USER` through the old `patterns=` argument;
- safe KPI/stat narration survives;
- French named-mechanism/causal overclaim fails field-closed;
- English intervention language fails field-closed;
- Arabic assertive causality fails field-closed;
- uncertainty/caveat wording remains allowed;
- non-doctor parser schemas are not reclassified by this focused lot.

### Certification

- Exact-head CI #1688 — **SUCCESS**.
- Exact-head migration drift #1500 — **SUCCESS**.
- Clinical Safety Reviewer — **PASS** on `4ac2f3a9…`.
- Release Certifier — **GO** on `4ac2f3a9…`.
- Expected-head locked merge — **SUCCESS**.
- Post-merge CI #1690 on `9febaaf9…` — **SUCCESS**.
- Post-merge drift #1502 — **SUCCESS**.

**P0.5B = CLOSED 100%.**

---

## Final P0.5 invariants

After P0.5:

1. **Detection authority and presentation authority are separate.** A deterministic detector may identify an internal signal without granting its historical label patient-facing diagnostic authority.
2. **Observation is not causation.** Patient-visible structured insight copy cannot claim a cause or diagnosis from the pattern alone.
3. **Fallback is not a safety bypass.** Provider failure cannot resurrect legacy therapeutic or causal strings.
4. **Summary evidence is minimized.** The summary/doctor-brief LLM receives deterministic KPI/stat evidence rather than semantic detector names.
5. **Generative narration cannot upgrade evidence.** Targeted output guards fail closed on named mechanisms, affirmative causality and unauthorized interventions.
6. **Clinical math is unchanged.** P0.5 changes claim authority and presentation only; it does not recalibrate a detector, threshold or formula.
7. **Existing independent safety layers remain mandatory.** Capability policy, AI-egress authorization, PHI stripping, deterministic triage and no-prescription sanitation remain separate defense-in-depth boundaries.

## Final closure evidence

P0.5 implementation is complete on `main@9febaaf96b9b17d716f183d2adae625f11d1dce2`, with both implementation merge units independently exact-head certified and post-merge green.

The parent issue #119 may be closed as **completed** only after the canonical documentation PR containing this closeout and the updated Truth & Capability Contract itself passes exact-head CI + migration drift, Release Certifier review, expected-head merge, then post-merge CI + drift.
