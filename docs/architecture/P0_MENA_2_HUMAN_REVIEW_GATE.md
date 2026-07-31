# P0-MENA-2 — Human review gate

## Purpose

This document records the work that cannot be certified by automated tests alone before locale-specific safety support is declared complete.

The implementation may provide deterministic fallbacks, executable corpora and regression coverage, but it must not claim native-language or clinical approval without named qualified reviewers and dated evidence.

## Automated foundation already available

The current branch provides:

- a canonical patient-owned locale preference model;
- independent confirmation and revocation for country, UI language, response language, script, transliteration, dialect, glucose units and timezone;
- deterministic fallback when a dimension is missing or unconfirmed;
- text and voice runtime wiring through the same resolved locale contract;
- Flutter locale selection with French, Arabic and English support;
- automatic RTL direction for Arabic;
- a versioned emergency-resource registry selected only from a confirmed country;
- executable safety corpora covering text, voice transcripts, Arabic script, Latin transliteration and mixed-language inputs;
- expanded high-severity Moroccan Darija orthographic variants.

Passing automated tests proves implementation consistency only. It does not prove native fluency, cultural suitability or clinical safety.

## Required reviewers

Each enabled locale requires two independent approvals:

1. **Native-language reviewer**
   - native or professionally fluent in the target locale;
   - able to review common, informal and high-severity phrasing;
   - independent from the author of the corpus.

2. **Clinical-safety reviewer**
   - qualified healthcare professional familiar with diabetes safety communication;
   - able to verify that detection and fixed responses neither prescribe nor delay urgent care.

For Moroccan Darija, the language review must cover both Arabic script and Latin/Arabizi transliteration.

## Review matrix

| Locale | Native review | Clinical review | Status |
|---|---|---|---|
| French | Required | Required | `pending_native_review` |
| Modern Standard Arabic | Required | Required | `pending_native_review` |
| English | Required | Required | `pending_native_review` |
| Moroccan Darija — Arabic script | Required | Required | `pending_native_review` |
| Moroccan Darija — Latin/Arabizi | Required | Required | `pending_native_review` |
| Mixed French/Darija/Arabic | Required | Required | `pending_native_review` |

## Required evidence

For each review, record:

- reviewer name or controlled reviewer identifier;
- qualification and review role;
- locale and script reviewed;
- corpus version or commit SHA;
- review date;
- approved cases;
- corrected or rejected cases;
- unresolved findings;
- explicit approval or rejection decision.

Evidence must live in a controlled compliance location. Personal reviewer details do not need to be committed publicly.

## RTL acceptance gate

Global `Directionality` support is necessary but insufficient. RTL completion requires an explicit screen-by-screen audit at representative mobile, tablet and desktop widths.

The audit must verify:

- navigation order and back affordances;
- text alignment and wrapping;
- numeric values, glucose units and dates;
- charts, legends and axis labels;
- mixed Arabic/Latin content;
- form fields, validation messages and cursor behavior;
- icons whose meaning depends on direction;
- dialogs, sheets, tables and exported documents;
- accessibility reading order.

Screenshots or automated golden evidence should be attached for French, Arabic and English where applicable.

## Emergency-resource gate

Country-specific emergency resources may be enabled only when:

- the country was explicitly confirmed by the patient;
- the source owner is identified;
- the source and verification date are recorded;
- a review/expiry date is present;
- the entry has not expired;
- the displayed wording has passed locale review.

When any condition fails, the product must use the documented generic emergency fallback and must not guess a local number.

## Completion criteria

P0-MENA-2 may be declared complete only when:

- all enabled locale corpora have native and clinical approval;
- high-severity Darija variants have no unresolved blocking findings;
- parity is demonstrated across text, voice transcript, mixed-language input and transliteration;
- the RTL screen audit is complete;
- emergency-resource entries intended for the pilot country are current and approved;
- the final clean SHA passes SQLite, PostgreSQL, migration drift, Ruff, import-linter, anti-bypass checks, Bandit, OpenAPI, Flutter analysis and secret hygiene.

Until then, automated corpora remain evidence of engineering coverage, not evidence of human approval.
