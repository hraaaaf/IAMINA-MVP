# P0-MENA-2 — Human review gate

## Purpose

This document records the work that cannot be certified by automated tests alone before locale-specific safety support is declared complete.

The implementation may provide deterministic fallbacks, executable corpora and regression coverage, but it must not claim native-language or clinical approval without qualified reviewers and dated controlled evidence.

## Verified engineering and review progress

The current `main` lineage provides:

- canonical patient-owned locale preferences with independent country, UI language, response language, script, transliteration, dialect, glucose-unit and timezone provenance;
- deterministic fallback when a dimension is missing or unconfirmed;
- text and voice runtime wiring through the same locale contract;
- French, Arabic and English UI support;
- English active patient-facing surface coverage certified 16/16;
- versioned confirmed-country emergency-resource selection with fail-closed fallback;
- executable safety corpora covering text, voice transcripts, Arabic script, Latin transliteration and mixed-language inputs;
- screen-by-screen RTL technical certification through PR #36;
- Arabic orthographic emergency hardening through PR #232;
- native-reviewed Darija lexicon evidence through PRs #234, #235 and #239;
- exact high-severity Darija native review through PR #247: 36/36 current runtime variants have explicit native-language evidence outcomes;
- 21 native-rejected Darija runtime variants locked for fail-closed remediation and four replacement candidates staged but inactive through PR #255;
- full technical Darija representative parity matrix across two channels × three input forms through PR #256;
- fail-closed Darija runtime-promotion contract through PR #244.

Passing these technical/native gates does **not** imply clinical, safety-owner, restricted parity or runtime-promotion approval.

## Required reviewers

Each enabled locale requires two independent approvals:

1. **Native-language reviewer**
   - native or professionally fluent in the target locale;
   - able to review common, informal and high-severity phrasing;
   - independent from the author of the corpus.

2. **Clinical-safety reviewer**
   - qualified healthcare professional familiar with diabetes safety communication;
   - able to verify that detection and fixed responses neither prescribe nor delay urgent care.

For Moroccan Darija, language review covers Arabic script and Latin/Arabizi transliteration.

## Current review matrix

| Locale / gate | Native evidence | Clinical evidence | Current verified state |
|---|---|---|---|
| French | required; no complete human receipt found | required; no complete human receipt found | OPEN |
| Modern Standard Arabic | required; no complete human receipt found | required; no complete human receipt found | OPEN |
| English | technical 16/16 UI baseline closed; native-human safety receipt not found | required; no complete human receipt found | OPEN |
| Moroccan Darija — Arabic script | high-severity native evidence present in PR #247 | required; no complete clinical receipt found | PARTIAL |
| Moroccan Darija — Latin/Arabizi | high-severity native evidence present in PR #247 | required; no complete clinical receipt found | PARTIAL |
| Mixed French/Darija/Arabic | technical parity evidence present, including PR #256 | required; restricted parity approval not found | PARTIAL |
| RTL screen audit | n/a | n/a | TECHNICALLY CLOSED — PR #36 |
| Darija runtime remediation | native rejection/remediation evidence present | clinical + safety-owner + restricted parity approvals required | STAGED, NOT AUTHORIZED |

## Required controlled evidence

For each human review, record:

- reviewer name or controlled reviewer identifier;
- qualification and review role;
- locale and script reviewed;
- corpus version/fingerprint or commit SHA;
- review date;
- approved cases;
- corrected or rejected cases;
- unresolved findings;
- explicit approval or rejection decision.

Personal reviewer details do not need to be committed publicly. The repository should hold only controlled evidence references where privacy or compliance requires it.

## RTL acceptance gate

The screen-by-screen RTL technical gate is closed through PR #36. Future UI changes that touch covered surfaces still require ordinary visual/regression recertification and must not be treated as permanent immunity from RTL regressions.

## Emergency-resource gate

Country-specific emergency resources may be enabled only when:

- the country was explicitly confirmed by the patient;
- the source owner is identified;
- the source and verification date are recorded;
- a review/expiry date is present;
- the entry has not expired;
- the displayed wording has passed required locale review.

When any condition fails, the product must use the documented generic emergency fallback and must not guess a local number.

## Completion criteria

P0-MENA-2 may be declared complete only when:

- all enabled locale corpora have required native and clinical approval;
- the 21 currently native-rejected high-severity Darija runtime variants are removed/replaced only under the fail-closed promotion contract, with no unresolved blocking finding;
- required clinical, safety-owner and restricted parity approvals are present for the promotion fingerprint;
- parity is approved across text, voice transcript, mixed-language input and transliteration;
- the already-closed RTL technical gate remains green on the final product head;
- emergency-resource entries intended for the pilot country are current and approved;
- the final clean SHA passes the repository safety/CI gates.

Until then, technical and native evidence must not be presented as complete clinical or pilot authorization.
