# IAMINA B / D24 — Préflight parallèle 2026-11-03

Base: main@6adf3fbeecb0f6645f9c7a9e3934177ef9eca6c7. Test-only candidate: no production behavior, no patient data.

Goal: AI OFF means 0 further provider submissions after consent withdrawal. Added synthetic Django tests for (1) revocation during an already-open egress scope, showing provider call count stays zero; (2) fresh global consent cannot resurrect an earlier granular meal image grant.

Checked by static source assertions only. Django/Python test suite and GitHub Actions have **not** been run on this candidate. Release remains NO-GO pending all provider paths, lazy SSE iterator, concurrent requests, authenticated browser A/B, independent privacy review.

This commit is intentionally **unreferenced** (Git object only): no branch ref/PR/update, because a push could auto-deploy linked Vercel projects without the owner's separate deployment authorization. It must not be merged or represented as CI-green.

Next: run tests in a safe runner or on a guarded branch after verifying no automatic Vercel deployment; correct red cases and continue with D14 and D10 independent work.
