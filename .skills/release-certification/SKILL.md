# Skill — Release Certification

## Purpose
Provide an independent GO/NO-GO after Builder and Reviewer work is complete.

## Certifier must verify
1. Scope matches one LOT and the PR diff contains no unrelated changes.
2. Reviewer findings are resolved or explicitly accepted by the human owner; no blocker remains.
3. Exact-head CI and migration drift are green after the final code/docs SHA.
4. Required specialized evidence is green: UX captures, PostgreSQL, clinical safety, security, OpenAPI, locale parity, etc., according to touched surfaces.
5. Canonical docs reflect the delivered truth and do not claim work not yet merged.
6. No temporary workflow/script, generated dependency noise, credential, debug artifact or bypass remains in the merge diff.
7. Merge is performed with expected-head SHA locking.
8. `main` points to the expected merge SHA and post-merge CI + migration drift complete successfully.

## Verdicts
- `NO_GO`: any blocker, stale evidence, unresolved review finding or failed gate.
- `CERTIFIED_WITH_NON_BLOCKING_FINDINGS`: only when findings are explicitly non-blocking and recorded.
- `CERTIFIED`: all applicable evidence is complete and clean.

The Certifier must never infer PASS from Builder confidence or from a subset of checks.