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
Limits: the *complete* hosted Web → BFF → API → Neon, authenticated app-lock and first-user FUE remain NOT_VERIFIED on this candidate. This PR made no Vercel deployment or Neon write through the assistant; however its first automatic PR-triggered historical E2E **DID execute an authenticated-API signup attempt** before cancellation (see incident below). Never claim no account was created.

Status: candidate, not a W01/D9 product certification. D9 remains OPEN.

## 28/10/2026 incident — legacy CI fired a live signup on PR; forced safe-gate fix

- PR #1162 first code SHA `5fd9165a` inadvertently triggered legacy [first-user hosted run #40768344797](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40768344797) on pull_request. The main journey was CANCELLED, but its `if: always()` diagnostic ran at **21:02:42–21:02:57 UTC** and logged **"Synthetic pointer signup reached onboarding with a backend POST."** This confirms the diagnostic observed a successful signup POST to `https://iamina-review.vercel.app`. It does **not** certify an authenticated end-to-end first-user journey or cleanup. The old alias resolves to Vercel deployment `dpl_8eqWcB1cTJudwE9Rw581WenUsy1K` with target `production`, code SHA `60de80ec`, and therefore is **NOT** the current protected W02 Preview.
- Emergency correction at `5b8e3e0657cad00c6cdbec2d1b68d73c97df432b`: legacy `.github/workflows/first-user-prod-e2e.yml` now adds a job gate requiring both `workflow_dispatch` **AND** explicit repository variable `IAMINA_ALLOW_REAL_PROD_E2E == true`. On a new pull_request event, legacy E2E [#40768551237](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40768551237) was **SKIPPED**; static harness [#40768542592](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40768542592) **SUCCESS** at same SHA. **This guard currently lives only on the DRAFT branch, not on the default/base branch**, so merging/reconciling this security guard after review is still necessary to eliminate global PR-triggered signups.
- Read-only independent Neon QA `noisy-truth-00115950 / br-green-meadow-b9j6o0bp`: `auth_user=0`, zero username/email prefix `ux95-signup-`.
- Read-only independent Neon Production `square-sun-82359137 / br-fragrant-frost-b1lbdfzs`: **29** existing `ux95-signup-` user records, **22 created on 28/10**, but **0 created from 21:02:42 through 21:03:00 UTC**; latest matching `date_joined=20:59:20.707Z`. Thus **the successful signup from the cancelled run cannot be identified as a new user in this specific Production Neon DB**. It might have targeted another backend/database, might not have persisted, or timestamps might differ; do not infer identity or location without a verified deployment-to-database mapping. Do not retrieve or print users' PII.
- **No account cleanup authorized or performed** on Production. A direct SQL delete is forbidden for this workflow; any live synthetic account cleanup must be authorized and use the exact application's supported deletion route, with independent read-only postcheck. The 29 old synthetic records in Production are a distinct inventory issue, NOT attribution to the cancelled run.

**Incident status:** live signup POST observed; persisted identity/backend **UNRESOLVED**. **Next exact:** establish read-only alias→BFF→API→DB mapping; decide via explicit human authorization whether to clean known synthetic accounts through verified app endpoints; keep real E2E disabled. W01 and D9 product NO-GO, no new deployment/Neon write.
