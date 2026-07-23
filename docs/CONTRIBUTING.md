# Contributing to IAmina

This document defines the engineering workflow and guardrails. Product priority lives only in `docs/ROADMAP.md`.

## Non-negotiable safety and privacy guardrails

A change touching any item below requires explicit human review in the PR description and focused tests.

- Deterministic emergency handling must remain upstream of generative AI.
- Glucose unit normalization must remain upstream of clinical/AI logic.
- External model/media calls must use the sanctioned outbound boundary; direct provider bypasses are forbidden.
- Outbound payloads are default-deny and must follow purpose, consent, minimization, redaction, retention, and processor rules.
- IAmina must not diagnose, prescribe, or optimize treatment.
- `client_uuid` on log entries is the offline-sync idempotency key.
- KPI calculations covered by ADR-0007 remain SQL-first.
- A language/dialect cannot enter a real-patient pilot without native-speaker safety parity and validated emergency resources.
- Historical ADRs are immutable. Changed decisions require a superseding ADR, not history rewriting.

### Hard pilot blockers

Before any real-patient pilot, the roadmap's pilot safety/compliance gate must be complete, including:

- high-severity language-variant safety coverage for the enabled pilot locale;
- monitored emergency-event handling or an explicitly documented alternative operating model;
- enforced AI/model consent at the outbound boundary;
- documented processors/subprocessors, retention, incident response, and pilot escalation;
- no reachable committed secrets and rotation of exposed credentials.

## Branch model

The repository currently uses `main` as the canonical branch.

```bash
git checkout main
git pull origin main
git checkout -b feature/short-description
```

Use short-lived prefixes such as `feature/`, `fix/`, `docs/`, or `chore/`.

One roadmap unit should normally map to one focused branch and one PR.

## Source of truth discipline

- `docs/ROADMAP.md`: single forward backlog, priorities, gates, current status.
- `docs/architecture/ARCHITECTURE.md`: current architecture and target boundaries.
- `docs/SPECS.md`: current product/API capability contract.
- `docs/TECHDEBT.md`: unresolved technical debt only.
- `docs/MISTAKES.md`: reusable engineering lessons only.
- `CLAUDE.md`: stable agent brief, never a session diary.
- ADRs / architecture timeline / assessments: historical evidence, not active backlog.

Do not duplicate roadmap state across multiple documents.

## Pull requests

A PR should state:

1. the exact roadmap unit or durable maintenance purpose;
2. what changed and why;
3. safety/privacy impact;
4. tests/checks run;
5. any manual verification still required.

Keep PRs focused. Large diffs are acceptable when a coherent cleanup cannot safely be split, but explain why.

## Validation

Run checks relevant to the changed surface.

### Backend

```bash
python backend/manage.py check
python -m pytest
```

### Frontend

```bash
cd frontend
flutter analyze
flutter test
```

### Additional requirements

- Safety changes: add focused positive + negative tests for the guardrail.
- API schema changes: regenerate and verify the OpenAPI artifact if the repository enforces it.
- Database migrations: test forward migration and rollback/recovery strategy appropriate to the migration risk.
- Locale changes: test script/RTL where relevant, mixed-language input, deterministic fallback, and native-reviewed safety corpus.
- Provider/outbound changes: prove no direct bypass and inspect minimized payloads.

## Commit format

Use imperative, scoped commits:

```text
feat(scope): description
fix(scope): description
refactor(scope): description
test(scope): description
chore(scope): description
docs(scope): description
```

## Secrets and local configuration

Never commit:

- `.env` files containing secrets;
- service-account credentials;
- API keys/tokens;
- local agent permission/configuration files that embed credentials;
- production exports or patient data.

If a secret is committed, deleting the line later is not enough. Treat it as compromised: rotate/revoke it, remove it from reachable history where appropriate, and document the incident response.

## Dependency and provider changes

Do not select an AI provider by brand preference alone. Text, STT, and vision may use different providers. Any production selection must satisfy the current roadmap benchmark criteria: privacy/residency, contractual retention/training terms, MENA quality, safety, latency, availability, and cost.

## Hotfixes

For urgent production fixes, branch from `main`, keep scope minimal, run the most relevant safety/regression checks, and merge back through a PR whenever operationally possible.
