# IAmina — Agent Brief

This file is a **stable execution brief**, not a session diary or status tracker.

## Read first

1. `docs/ROADMAP.md` — single forward backlog and gates.
2. `docs/architecture/ARCHITECTURE.md` — current architecture and target boundaries.
3. `docs/CONTRIBUTING.md` — workflow + non-negotiable safety rules.
4. `docs/MISTAKES.md` — reusable engineering lessons.
5. `.skills/lot-execution/SKILL.md` — mandatory LOT procedure.
6. `.agents/README.md` — mandatory Builder/Reviewer/Certifier routing.
7. Every domain skill required by the touched surface.

Do not infer current priorities from old commit messages, assessments, archived transformation plans, or historical phase numbers.

## Product doctrine

- IAmina is a **MENA diabetes companion**.
- Diabetes is the only live condition.
- MENA rollout is country-by-country and locale-by-locale.
- Language/dialect is user-selected; location may suggest but never silently decide.
- Deterministic clinical/safety logic decides; generative models may verbalize approved minimized output or perform explicitly permitted media tasks.
- No diagnosis, prescription, or treatment optimization.
- Privacy, consent, minimization, and data-sovereignty constraints apply before provider convenience.
- D90 retention + a credible payer/distribution signal gate disease/module expansion.

## Current strategic reset

The critical path is:

1. Enforce one outbound AI/data-egress boundary.
2. Define MENA locale + safety contract.
3. Migrate sovereignty-critical auth from legacy Firebase dependencies to Django-native identity.
4. Benchmark text/STT/vision providers independently.
5. Deploy one safe pilot locale/cohort.
6. Measure D90 and decide.

See `docs/ROADMAP.md` for exact checkboxes.

## Architecture facts

- Frontend: Flutter only.
- Backend: Django + django-ninja.
- Database: PostgreSQL for Docker/staging/production path; SQLite may exist as lightweight manual-dev fallback.
- Auth: Firebase bridge is **legacy current-state**, not the target architecture.
- AI: provider-specific runtime exists as legacy current-state; target is a provider-agnostic, privacy-gated outbound boundary.
- Chassis/module seams from ADR-0008 exist, but **this does not authorize multi-condition product expansion**.
- Diabetes owns diabetes-specific clinical data and logic.
- Shared core owns cross-cutting identity/contracts/safety/observability concerns.

## Non-negotiable invariants

- Never bypass or silently reorder emergency and unit-normalization safety gates.
- Never let an external model decide emergency handling.
- Never send unapproved identifiers, unrelated raw clinical history, or media to a model provider.
- Every external AI/media call must ultimately pass the sanctioned outbound boundary.
- Never add a locale/dialect to a patient pilot without native safety parity and emergency-resource validation.
- KPIs remain SQL-first where ADR-0007 applies.
- `client_uuid` remains the offline-sync idempotency key.
- Do not edit historical ADRs to rewrite the past; add a superseding ADR when a decision changes.

## Work rules

- `main` is the current canonical branch in this repository.
- One roadmap unit = one short-lived branch = one focused PR.
- Keep status in `docs/ROADMAP.md`; do not create parallel state files or append session logs here.
- Update docs only when the change alters a durable contract, architecture fact, guardrail, or forward backlog.
- Historical documents are evidence, not instructions.
- Never commit `.env`, service-account credentials, API keys, local agent permission files containing secrets, or generated secret-bearing configuration.

## Mandatory team protocol

Every LOT must execute the repository-owned team model:

`Builder -> applicable Reviewer(s) -> Release Certifier -> merge -> post-merge verification`

- Builder: `.agents/lead-engineer.md`.
- Reviewer routing: `.agents/README.md`.
- Final Certifier: `.agents/release-certifier.md`.
- Every LOT loads `.skills/lot-execution/SKILL.md` and `.skills/release-certification/SKILL.md`.
- Domain skills/reviewers are mandatory when their surface is touched.
- Builder may not self-certify. Prefer separate agents; if only one runtime exists, execute isolated role passes with a fresh evidence review.
- UX/UI work additionally requires `.skills/ux-ui-certification/SKILL.md` and a final score strictly above 9.0/10.
- Any final code or documentation SHA change invalidates stale exact-head certification evidence and requires the applicable gates to run again.

## Validation baseline

Run the checks relevant to the changed surface before merge. At minimum for mixed backend/frontend work:

```bash
python backend/manage.py check
python -m pytest
cd frontend && flutter analyze && flutter test
```

Security/safety changes require focused tests proving the guardrail itself, not only broad regression tests.

## Commit format

```text
feat(scope): description
fix(scope): description
chore(scope): description
docs(scope): description
```
