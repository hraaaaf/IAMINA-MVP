# Skill — MENA Clinical-Linguistic Safety Review

## Purpose
Provide a reproducible AI secondary-review procedure for IAMINA's fingerprinted multilingual high-severity safety corpus without impersonating or replacing required human native, clinical or safety-owner approval.

## Required inputs
- `backend/core/safety_corpora.py`
- `backend/core/safety_corpus_review.py`
- `backend/core/triage_classification.py`
- exact `safety_corpus_fingerprint()`
- every `all_safety_corpus_cases()` entry
- every required parity tuple from `required_parity_dimensions()`
- current clinical/safety authority contracts

## Procedure
1. **Lock evidence.** Record source commit, schema version, exact corpus fingerprint, case count and parity tuple count. If any changes during review, invalidate the pass and restart.
2. **Enumerate 100%.** Review every representative case and every exact high-severity classifier variant. Sampling is not acceptable for certification evidence.
3. **Semantic review.** For each case, assess whether the wording plausibly carries the expected severe glycemic meaning and whether conservative classification is safety-compatible. Separate potential over-triage from unsafe under-triage.
4. **Language review.** Check French, Arabic and Moroccan Darija for meaning preservation, spelling/orthographic variation, Arabic script, Latin transliteration, Arabizi digits and code-switching.
5. **Channel parity.** Compare text, voice transcript, mixed-language and transliterated forms. A channel or script variant must not silently weaken the deterministic safety classification.
6. **Clinical-authority review.** Reject any path that introduces diagnosis, prescription, dose calculation, treatment optimization/change, fabricated certainty or generative emergency authority.
7. **Emergency-truth review.** Verify high-severity routing remains deterministic, fail-closed and jurisdiction-truthful. Do not infer automatic human monitoring.
8. **Decision.** Mark each reviewed unit `PASS`, `FAIL` or `UNCERTAIN`. Any unresolved high-severity `FAIL` or `UNCERTAIN` makes the overall AI secondary review `CHANGES_REQUIRED` or `UNCERTAIN`.
9. **Evidence.** Write a dated assessment containing fingerprint, coverage, findings, decision, limitations and residual human gates.
10. **Human boundary.** Never populate or synthesize `native_reviewer_reference`, `qualification_reference`, `clinical_approval_reference` or `safety_owner_approval_reference`. Never change the semantics of `audit_safety_corpus_review --require-approved` to accept AI evidence as human approval.

## Required output contract
- `reviewer_kind: AI_SECONDARY_REVIEW`
- source commit and corpus fingerprint
- cases reviewed / total
- parity tuples reviewed / total
- blocking findings
- non-blocking findings
- overall decision
- residual human/native/clinical/safety-owner requirements

## Fail-closed rules
- Fingerprint mismatch or incomplete case coverage => `UNCERTAIN`.
- Unreviewed high-severity variant => `UNCERTAIN`.
- Dangerous semantic ambiguity with plausible under-triage => `CHANGES_REQUIRED`.
- Any diagnosis/prescription/dosing/treatment-change leakage => `CHANGES_REQUIRED`.
- Missing genuine human approval remains a human gate even when AI review is `PASS`.

## Precedence
Canonical clinical, safety, architecture and roadmap contracts override this skill. Deterministic runtime safety authority always outranks reviewer narration.