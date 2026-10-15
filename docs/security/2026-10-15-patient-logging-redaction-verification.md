# 2026-10-15 — Patient-content logging hardening: evidence and closeout

> Engineering scope only. This is not a clinical, patient-production, CNDP or independent agent certification. All synthetic tests avoid actual patient data.

## Goal / measurable success

Eliminate three observed paths where untrusted exception details, emergency transcripts or technical request identifiers could appear in the patient's batch response or in server log entries, without weakening IAMINA's deterministic safety, consent/AI-egress policy or the offline replay contract.

Success: exact-head synthetic canary regressions are green on SQLite and PostgreSQL, security/lint gates green, expected patient response paths preserved, merged source inspected, postmerge CI checked for each SHA. A successful build or static inspection by itself is insufficient proof.

## A. Batch journal synchronization — CLOSED

- Finding: `d3a2c75d79b6e1374c3e6ff9320a2d6a5f1e193b:backend/diabetes/api/v1/logs.py:173-174` previously included raw `str(exc)` in an error receipt.
- [Issue #1035](https://github.com/hraaaaf/IAMINA-MVP/issues/1035), [PR #1036](https://github.com/hraaaaf/IAMINA-MVP/pull/1036) merged on `405a10205ff60618598ad27df95eaac3fd5aef4e`; issue CLOSED.
- Fix returns controlled `internal error` and logs exception class only; synthetic tests also verify partial-batch successful row after a failed row and no canary in returned JSON/logs.
- Candidate exact-head CI [#38707355599](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38707355599): SQLite 2815 passed/5 skipped/3 xfailed; PostgreSQL 2819 passed/1 skipped/3 xfailed, 121 subtests each; Ruff, Bandit, anti-LLM bypass, AI egress gates successful. Django migrations #38707355603 SUCCESS.
- Exact main postmerge CI [#38708068060](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38708068060) SUCCESS, drift #38708068058 SUCCESS.

## B. Companion chat error logs — CLOSED

- Finding: `18e5a9f47e32b7c7fa5aba9eb7e9383de1426155:backend/ai/api/v1/ai.py:386-388,579-583` used `logger.exception` in normal chat/SSE error handling, which can log untrusted exception messages/tracebacks. No actual disclosure observed.
- [Issue #1049](https://github.com/hraaaaf/IAMINA-MVP/issues/1049), [PR #1050](https://github.com/hraaaaf/IAMINA-MVP/pull/1050) merged into `main@f26e010e18e3466b466cd6a9c8daeebe2b088d96`; issue CLOSED.
- Logs now have controlled event and exception type only. Synthetic tests verify both normal reply fallback and SSE `[DONE]` after an injected error with canary absent.
- Candidate exact-head [#38710632573](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38710632573) SUCCESS: SQLite 2817 passed/5 skipped/3 xfailed and PostgreSQL 2821 passed/1 skipped/3 xfailed; 121 subtests each. Migration #38710632659 SUCCESS.
- Independent *functional* synthetic local chat browser E2E [#38710632604](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38710632604) SUCCESS with provider network flag disabled; this is not an independent human/agent review.
- Exact main postmerge CI [#38711294833](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38711294833) SUCCESS, migration #38711294857 SUCCESS.

## C. Voice/STT/triage diagnostic logs — SOURCE MERGED, POSTMERGE GATE PENDING

- Finding on `3affe8bcc61c6ef111986fb740f05fbdc3acb08a`:
  - `backend/ai/api/v1/voice.py:139-140,157-163` logged raw STT error, voice emergency transcript[:120] and user ID.
  - `backend/core/middleware/triage_vital.py:334-341` logged emergency message snippet, URL and user ID.
  - `backend/media/voice.py:131-140` logged provider exceptions with stack detail.
- [Issue #1040](https://github.com/hraaaaf/IAMINA-MVP/issues/1040), [PR #1041](https://github.com/hraaaaf/IAMINA-MVP/pull/1041) SQUASH MERGED at `main@775a15a3c8c6156981583a773f4df766811a68b4`.
- Changed only controlled logging of these paths: static emergency event, deterministic classification `kind`, or exception class. Triage/response, patient scope and provider egress remain unchanged. Synthetic canary tests cover emergency voice, STT failure, deterministic middleware and provider exception logs.
- Candidate head `848d49864d46ece9f133482968602064817037f6`: [CI #38710958682](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38710958682) SUCCESS, SQLite **2819 passed/5 skipped/3 xfailed**, PostgreSQL **2823 passed/1 skipped/3 xfailed**, 121 subtests each, Flutter job successful, Ruff, Bandit and anti-LLM/egress passed. Migration drift #38710958764 SUCCESS.
- Source readback at merged SHA confirmed redaction of all three named handlers.
- Exact-main [CI #38712421453](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38712421453) **IN_PROGRESS at report creation**. Migration drift #38712421438 SUCCESS. **Do not close #1040 or call technical lot complete until this run succeeds**.

## Adversarial and scope limitations

- Different source-level checks and a second test-read pass were performed by the **same GPT session**: these are *not* genuinely independent Security Reviewer and Release Certifier identities. Their scope is code/logging behavior only and does not supersede AGENTS.md's review quality gates.
- Tests were all synthetic (canaries and a local synthetic identity), with no patient data, external patient LLM call or paid services activated.
- Still out of scope/open: full-app 15 genuine subagent audit #1029 (0/15), branch ruleset/required checks #1038, and GET SSE URL leakage #925; clinical/native MENA reviewers, privacy/CNDP sign-off, D31 physical proof and real patient release gates.
- No Vercel deployment authorized or undertaken. P5 canonical release progress historically 6/12 (50%), not re-scored by this security remediation.

## Sources

- OWASP Logging Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- OWASP Error Handling Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet
- Internal `AGENTS.md:86-107`, `docs/QUALITY_SCORING_POLICY.md:21-46` (same-executor cap and missing proof policy).

## Next exact

Check the completed conclusion and jobs for #38712421453 on `775a15a3c8c6156981583a773f4df766811a68b4`; if green, close #1040, replace this pending state by precise PASS evidence, then review/merge this docs-only verification record and inspect its exact-main CI. If red, fix on an isolated branch, rerun and do not falsely close.
