# Pilot Safety Certification Contract

## Scope

This gate certifies deterministic refusal and non-bypass behavior for treatment,
prescription and insulin-dose requests before a generative chat LLM is initialized.

## Certified paths

- synchronous patient chat;
- SSE chat;
- voice chat after transcription;
- patient summary insight cards;
- doctor-facing structured text;
- OCR response schemas.

## Voice boundary

Audio transcription necessarily occurs before transcript intent is known. A blocked
transcript may not initialize any downstream generative conversation LLM. This is
reported separately from the STT operation and must not be described as zero total
AI egress.

## Required evidence

1. Multilingual corpus routes to a deterministic refusal.
2. Educational medication questions remain allowed.
3. Blocked sync and streaming requests do not initialize the LLM gateway.
4. Blocked voice transcripts do not initialize IAmina conversation generation.
5. Generated and template summary structures are recursively sanitized.
6. OCR endpoints expose observations only and no treatment recommendation field.
7. SQLite, PostgreSQL, migration drift, Ruff, import-linter, anti-bypass, Bandit,
   OpenAPI, Flutter analyze and secret hygiene are green.

## Non-claims

Automated tests do not replace native-speaker review, clinical approval, emergency
operations approval or processor/privacy approval.
