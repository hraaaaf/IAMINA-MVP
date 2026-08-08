# IAmina — Agent Execution Brief

This file is a **stable execution contract for coding agents**, not a session diary, branch tracker, or historical status log.

## Read first

1. `docs/ROADMAP.md` — single forward backlog and gates.
2. `docs/architecture/ARCHITECTURE.md` — current architecture + target boundaries.
3. `docs/CONTRIBUTING.md` — workflow and non-negotiable guardrails.
4. `docs/MISTAKES.md` — durable lessons.
5. Relevant ADR/spec for the assigned unit.
6. `.skills/lot-execution/SKILL.md` — mandatory LOT procedure.
7. `.agents/README.md` — reviewer routing matrix.
8. Every additional `.skills/*/SKILL.md` required by the touched surface.

Do not choose work from old phase numbers, archived plans, assessments, or stale commit notes.

## Product doctrine

- IAmina is a **MENA diabetes companion**.
- Diabetes is the only live condition.
- Country/dialect rollout is gated by native safety parity, validated emergency resources, and privacy/compliance readiness.
- User choice determines language/dialect; location may suggest only.
- Deterministic clinical/safety logic decides.
- Generative models may verbalize approved minimized structured output or perform explicitly permitted media tasks.
- No diagnosis, prescription, dose calculation, or treatment optimization.
- D90 retention + a credible payer/distribution signal gate expansion to another condition.

## Current critical path

Execute only explicitly assigned work from these roadmap areas:

1. P0-MENA-1 — outbound AI/data-egress boundary.
2. P0-MENA-2 — locale + safety contract.
3. P0-MENA-3 — Django-native auth migration.
4. P0-MENA-4 — multimodal provider benchmark.
5. Pilot safety/compliance + staging + one-country pilot.

Do not pull gated platform/module work forward.

## Architecture facts

- Flutter is the only frontend.
- Django + django-ninja is the backend.
- PostgreSQL is the authoritative non-lightweight path; SQLite may remain a manual-dev fallback.
- Firebase is **legacy current-state**, not target architecture.
- Provider-specific AI integrations are **legacy current-state**, not target architecture.
- ADR-0008 chassis/module seams exist, but diabetes remains the only live condition.
- Shared core owns cross-cutting contracts/safety/auth/account/observability concerns.
- Diabetes owns diabetes-specific clinical data and logic.

## Hard guardrails

Never:

- bypass/reorder deterministic emergency or unit-normalization gates without explicit decision;
- route emergency authority to a generative model;
- create a direct provider call that bypasses the sanctioned outbound boundary;
- send unapproved identifiers, unrelated raw health history, or unapproved media externally;
- add autonomous diagnosis/prescription/treatment-change logic;
- enable a patient locale/dialect without its required safety gate;
- repurpose/remove `client_uuid` offline-sync idempotency;
- move SQL-first KPI authority into free-form Python/LLM logic where ADR-0007 applies;
- edit historical ADRs to rewrite a superseded decision;
- commit secrets, service-account files, provider keys, or local agent config containing credentials.

## Work discipline

- Repository canonical branch is currently `main`.
- One roadmap unit = one short-lived branch = one focused PR.
- Keep transient status in git/PRs, not in this file.
- Do not add session-state sections.
- Update a canonical doc only when a durable truth changes.
- Historical docs are evidence, not instructions.

## Mandatory Builder → Reviewer → Certifier chain

Every roadmap LOT, P-level remediation unit, hotfix or governance change must use the following sequence:

1. **Builder** — normally `.agents/lead-engineer.md`; inspects, reproduces, defines acceptance criteria, implements, tests and prepares evidence.
2. **Reviewer(s)** — selected from `.agents/README.md` according to the changed surface. Blocking findings must be remediated and affected evidence rerun.
3. **Release Certifier** — `.agents/release-certifier.md`; independently verifies final diff, reviewer closure, exact-head gates, canonical docs and merge readiness.
4. **Merge** — expected-head SHA locking is required when supported.
5. **Post-merge verification** — `main` must point to the expected merge and post-merge CI + migration drift must be green before declaring 100% complete.

The Builder may not certify its own LOT. Prefer separate agents when orchestration supports them. If only one runtime/session is available, roles must still be executed as explicit isolated passes: the Reviewer must re-read evidence without relying on Builder conclusions, and the Certifier must independently re-check the final diff and exact-head evidence.

For UX/UI LOTs, `.skills/ux-ui-certification/SKILL.md` is mandatory and a score **strictly above 9.0/10** is required. A score `<=9.0` keeps the LOT open.

Specialized skills are mandatory when their surface is touched:
- clinical/medical/safety → `.skills/clinical-safety/SKILL.md`;
- models/migrations/persistence/PostgreSQL → `.skills/migrations-database/SKILL.md`;
- auth/authorization/privacy/secrets/external egress → `.skills/security-review/SKILL.md`.

`.skills/release-certification/SKILL.md` is mandatory for every LOT.

## Validation

Run the narrowest focused tests first, then the relevant regression suite.

Baseline for mixed changes:

```bash
python backend/manage.py check
python -m pytest
cd frontend && flutter analyze && flutter test
```

Additional expectations:

- safety change → focused positive + negative guardrail tests;
- locale change → native-reviewed fixtures, mixed-script/transliteration and fallback tests where relevant;
- provider/egress change → tests proving bypass is impossible/detected and payload is minimized;
- auth migration → identity reconciliation + rollback/recovery tests;
- schema migration → forward migration + recovery plan validation.

## Documentation ownership

- `ROADMAP.md` — forward work only.
- `ARCHITECTURE.md` — current/target boundaries.
- `SPECS.md` — current capability contract.
- `TECHDEBT.md` — unresolved compromises only.
- `MISTAKES.md` — reusable lessons only.
- ADRs/timeline/assessments — historical record.

## Commit format

```text
feat(scope): description
fix(scope): description
refactor(scope): description
test(scope): description
chore(scope): description
docs(scope): description
```
