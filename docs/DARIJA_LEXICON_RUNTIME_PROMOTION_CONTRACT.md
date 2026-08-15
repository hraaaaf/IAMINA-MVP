# Darija Lexicon Runtime Promotion Contract

Status: **FAIL-CLOSED / NO CURRENT RUNTIME AUTHORIZATION**

Date: 2026-08-15  
Locale: Moroccan Darija (`ar-MA`)

## Purpose

The working Darija lexicon batches are linguistic evidence only. They must not enter runtime triage or other clinical/safety logic by copy/paste, transliteration, keyword expansion, or inference from automated tests.

This contract defines the minimum gate for a future, separate runtime-promotion lot.

## Required evidence before promotion

Every promoted phrase must have all of the following:

1. A stable candidate identifier and exact phrase/input form.
2. A source-evidence reference back to the reviewed working material.
3. The exact current safety-corpus fingerprint.
4. Native-review evidence reference.
5. Clinical-review evidence reference.
6. Safety-owner evidence reference.
7. Cross-channel/input-form parity evidence reference.
8. Regression evidence for all five classes:
   - positive,
   - negative,
   - contextual,
   - hyperbole,
   - ambiguity.
9. An explicit `approved_for_runtime` decision.

Missing or stale evidence blocks promotion.

## Batch 03 adversarial evidence

`backend/core/tests/fixtures/darija_lexicon_batch03_adversarial.json` records a focused non-runtime subset covering:

- lethal-token hyperbole (`nmout`, `lmout`, `kay9tel...`),
- broad inability/overwhelm wording,
- CGM LOW/HIGH readings,
- CGM/device failure wording,
- sensor/symptom disagreement,
- forgotten or duplicate insulin administration wording,
- uncertainty about whether insulin was taken.

Every fixture entry is explicitly `runtime_authorized: false`.

## Semantic boundaries that must survive promotion

- Lethal vocabulary is not sufficient by itself to establish death, suicidality, or a vital emergency.
- `ssehd` (ambient heat in the reviewed context) must not be collapsed into `skhana` (fever wording).
- A CGM LOW/HIGH value is an instrumental reading, not automatically a biologically confirmed glucose state.
- A reported sensor failure does not establish a glucose state.
- Sensor/symptom discordance must remain explicit rather than being silently resolved by the classifier.
- Medication uncertainty must not be converted into confirmed administration.
- Medication-event vocabulary does not authorize dose calculation, dose correction, prescription, or treatment optimization.

## Relationship to the restricted safety review manifest

This contract supplements, and does not replace, `backend/core/safety_corpus_review.py`.

The restricted manifest remains authoritative for native, clinical, safety-owner, case-level and parity review. A lexicon candidate cannot become runtime-authorized merely because this promotion contract is technically satisfied in a synthetic test.

The synthetic ready-path test proves only that the deterministic gate can reach an empty blocker set when all required fields are present. It is not evidence that any real Darija candidate has those approvals.

## Current state

- Working native evidence exists through concepts 1–67.
- Batch 03 adversarial cases are preserved outside runtime.
- No phrase in the Batch 03 adversarial fixture is authorized for runtime by this lot.
- Existing restricted human review gates remain open/fail-closed.
- No MENA roadmap numerator change is claimed by this contract-only lot.

## Technical closeout evidence — PR #244

The contract-only implementation lot is technically closed with no runtime promotion:

- PR: `#244` — `feat(safety): add fail-closed Darija lexicon promotion contract`
- exact PR head: `73d415f8e6f3f6c83a7bbcab424782fa2585682f`
- pre-merge CI: `#2404` — SUCCESS
- pre-merge Django migration drift: `#2216` — SUCCESS
- merge SHA: `9bda370c5d93e8b8ce620d5e6d967688327b146f`
- post-merge CI: `#2405` — SUCCESS on the exact merge SHA
- post-merge Django migration drift: `#2217` — SUCCESS on the exact merge SHA
- implementation review passes recorded: MENA linguistic, Clinical Safety, Release Certifier
- those technical/AI review passes are not substitutes for restricted native-human, clinical-human, or safety-owner approval evidence

Roadmap impact: **none**. The MENA critical-path numerator remains unchanged because this lot creates a promotion gate and adversarial regression contract only; it does not authorize any Darija phrase for runtime use.
