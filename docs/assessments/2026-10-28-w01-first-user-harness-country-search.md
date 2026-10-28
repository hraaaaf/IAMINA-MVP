# IAMINA W01 — first-user E2E harness aligned with current Web onboarding

Date: 2026-10-28. Scope: test harness only, not application runtime.

## BEFORE — source evidence
- Old run #40739595534 at old SHA 8a9f7f1 failed the first-user journey on Maroc; a separate diagnostic also did not observe a signup POST. Neither is proof on today's code.
- The old test clicked a static Maroc button, while the actual current Flutter onboarding renders a searchable DropdownMenu with the onboarding-country-search key. Typing is not enough; a real menu option must be selected.
- Script still clicked removed D6 tone choices (Simple et chaleureux / Neutre et professionnel).

## AFTER — targeted repair
- Focus visible searchable country input, type Maroc, choose its suggestion using semantics, then require the exact current French diabetes-type question (only rendered after an actual country code is selected).
- Remove old D6 tone clicks. No product UI change.
- Static tests read current Flutter widget and French localization. A CI job runs Node syntax check and static contract without opening a browser or creating a user.

## Goal / success / evidence
Goal: reduce false failure in W01 first-user test without weakening protections or making claims about the real hosted journey.
Success: three static tests PASS and Node script syntax PASS on exact SHA; CI and PR readback attest code.
Limits: old signup POST failure is independent and not yet retested; hosted Web → BFF → API → Neon, authenticated app-lock and real first-user FUE remain NOT_RUN on candidate. No Vercel deployment, no Neon mutation, no account creation or clinical data.

Status: candidate, not a W01/D9 product certification. D9 remains OPEN.
