# Skill — Security Review

## Purpose
Review authentication, authorization, secrets, external egress and security-sensitive boundaries.

## Required checks
- Confirm no secret-bearing files or credentials are tracked.
- Run repository secret-hygiene and Bandit/SAST gates when relevant.
- Preserve CSRF for cookie/session writes unless a narrow explicit exception is approved.
- Prove external AI/media calls pass the sanctioned outbound boundary and authorization/consent checks.
- Run architecture/import-linter and anti-bypass gates relevant to the change.
- Inspect error handling for sensitive data leakage.
- Prefer fail-closed behavior at authorization, consent, normalization and provider boundaries.

## Blockers
Direct provider bypass, weakened auth/CSRF, secret exposure, authorization fail-open, unsafe logging, or a security gate disabled/reordered to make CI pass.