# Security #30 — reachable Git-history remediation certification

Date: 2026-08-14

## Scope

This assessment certifies only the reachable Git-history remediation tracked by issue #30. It does not waive native-language, CNDP/privacy, processor, deployment-residency or provider-benchmark gates.

## Proven facts

- The project owner explicitly authorized the irreversible full-history rewrite and required force-updates.
- The historical target was `.claude/settings.local.json`; no credential values are reproduced here.
- Repository-owner attestation classifies the historical PekPik material as public/test access rather than a privately provisioned IAMINA credential. Provider-side rotation is therefore recorded as not applicable on owner evidence; this is not independent provider verification.
- The successful rewrite processed all 322 reachable branch refs; no tags existed at execution time.
- Before any remote mutation, the rewritten local graph no longer exposed the forbidden path, `scripts/check_secrets.py` passed, and the bounded full-history scanner passed.
- Force-update completed for the reachable branches. Rewritten `main` is `7c2bb4667151e4175f99327091dae0da178a52ae`.
- The temporary rewrite runner branch was deleted after the coordinated force-update.
- PR #229 had already merged before the rewrite and therefore required no post-rewrite rebase.

## Independent remote verification

Dedicated fresh-clone verification run `31821201798` completed **SUCCESS**. It cloned the repository anew from GitHub, fetched all branches/tags, required a full non-shallow repository, proved `.claude/settings.local.json` unreachable, passed tracked-tree secret hygiene, and passed the bounded full-history scanner.

## Regression evidence

- Django migration drift #2113 / run `31821238444`: **SUCCESS** on rewritten-main SHA `7c2bb4667151e4175f99327091dae0da178a52ae`.
- CI #2301 / run `31821238451`: **SUCCESS** on the same rewritten-main SHA.

## Independent security review

**PASS.** The isolated Security Reviewer pass re-read the security-review contract and evidence without relying on Builder conclusions. No auth/CSRF/egress boundary was modified by the rewrite; tracked-secret hygiene passed; SAST, architecture/anti-bypass and full backend/frontend/PostgreSQL regression gates completed green in CI #2301; fresh-clone full-history verification passed.

## Certification boundary

The reachable-history remediation is technically proven from a fresh GitHub clone and independently security-reviewed PASS. Canonical closure and issue #30 closure remain contingent only on the closeout PR exact-head CI + migration-drift gates and an independent Release Certifier pass.

The MENA critical-path numerator remains **32/41 (~78%)** because Gate A and this pilot-security remediation are governance/certification gates over already-counted foundations, not newly numbered MENA tasks. The pilot safety/compliance checklist advances from **9/13 to 10/13 (~77%)** because its explicit reachable-secret-history item is now satisfied.
