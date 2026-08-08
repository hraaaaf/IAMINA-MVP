# Contributing to IAmina

This document defines the engineering workflow and guardrails. Product priority lives only in `docs/ROADMAP.md`.

## Non-negotiable safety and privacy guardrails

A change touching any item below requires explicit human review in the PR description and focused tests.

- Deterministic emergency handling must remain upstream of generative AI.
- Glucose unit normalization must remain upstream of clinical/AI logic and fail closed on unexpected normalization failures.
- Cookie/session-authenticated API writes must retain CSRF protection; exemptions must be narrow and explicit.
- External model/media calls must use the sanctioned outbound boundary; direct provider bypasses are forbidden.
- External egress requires patient/purpose/modality authorization and server-side consent before a real provider call.
- Outbound payloads remain default-deny and must ultimately follow purpose, consent, minimization, redaction, retention, residency, and processor rules.
- IAmina must not diagnose, prescribe, or optimize treatment.
- `client_uuid` on log entries is the offline-sync idempotency key.
- KPI calculations covered by ADR-0007 remain SQL-first.
- PostgreSQL-specific analytical behavior must be tested on PostgreSQL before pilot-critical certification.
- A language/dialect cannot enter a real-patient pilot without native-speaker safety parity and validated emergency resources.
- Historical ADRs are immutable. Changed decisions require a superseding ADR, not history rewriting.

### Hard pilot blockers

Before any real-patient pilot, the roadmap's pilot safety/compliance gate must be complete, including:

- high-severity language-variant safety coverage for the enabled pilot locale;
- monitored emergency-event handling or an explicitly documented alternative operating model;
- enforced AI/model consent at the outbound boundary;
- complete payload/media governance for approved external model flows;
- documented processors/subprocessors, retention, residency, incident response, and pilot escalation;
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

## Mandatory Builder → Reviewer → Certifier workflow

Every roadmap LOT, P-level remediation unit, hotfix or governance change must follow the repository-owned team protocol in `AGENTS.md` and `.agents/README.md`:

1. **Builder** inspects, reproduces, defines acceptance criteria, implements and prepares evidence.
2. **Applicable Reviewer(s)** independently review the final behavior/diff using the relevant `.skills/*/SKILL.md` procedures. Blocking findings return the LOT to the Builder.
3. **Release Certifier** independently verifies reviewer closure, exact-head gates, final diff hygiene, canonical documentation and merge readiness.
4. **Merge** uses expected-head SHA locking when supported.
5. **Post-merge verification** on `main` is required before a LOT may be declared 100% complete.

The Builder may not certify its own LOT. Prefer separate agents when orchestration supports them. If only one runtime/session is available, Builder, Reviewer and Certifier must still be executed as explicit isolated passes; Reviewer and Certifier must re-read evidence rather than inheriting Builder conclusions.

Mandatory skills for every LOT:

- `.skills/lot-execution/SKILL.md`;
- `.skills/release-certification/SKILL.md`.

Additional skills/reviewers are mandatory according to `.agents/README.md` when UX/UI, clinical safety, database/migrations or security/privacy/egress surfaces are touched.

A code or documentation change after certification changes the head SHA and invalidates stale exact-head evidence. Re-run the applicable gates before merge.

## Source of truth discipline

- `docs/ROADMAP.md`: single forward backlog, priorities, gates, recent closeout state.
- `docs/architecture/ARCHITECTURE.md`: current architecture and target boundaries.
- `docs/SPECS.md`: current product/API capability contract.
- `docs/MEDICAL_DATA_PLAN.md`: current clinical-data and safety contract.
- `docs/TECHDEBT.md`: unresolved technical debt only.
- `docs/MISTAKES.md`: reusable engineering lessons only.
- `CLAUDE.md` / `AGENTS.md`: stable agent briefs, never session diaries.
- `.agents/`: role briefs; `.skills/`: durable execution procedures. Neither replaces canonical product/safety/architecture sources.
- ADRs / architecture timeline / assessments: historical evidence, not active backlog.

Do not duplicate roadmap state across multiple documents.

## Pull requests

A PR should state:

1. the exact roadmap unit or durable maintenance purpose;
2. what changed and why;
3. safety/privacy impact;
4. tests/checks run;
5. any manual verification still required;
6. which canonical docs must change at closeout;
7. Builder identity/pass, applicable Reviewer verdict(s), and Release Certifier verdict.

Keep PRs focused. Large diffs are acceptable when a coherent cleanup cannot safely be split, but explain why.

## Mandatory documentation closeout

**A task/phase is not complete when code merges. It is complete when the merged truth and canonical documentation agree.**

Before starting the next roadmap unit, perform this closeout:

1. **Always inspect `docs/ROADMAP.md`.**
   - mark/remove the completed work;
   - record only the concise operationally relevant closeout;
   - identify the next open blocker.
2. **Update `docs/architecture/ARCHITECTURE.md` only if the as-built architecture changed.**
3. **Update `docs/SPECS.md` only if a durable current capability/API contract changed.**
4. **Update domain contracts** such as `docs/MEDICAL_DATA_PLAN.md` when safety/data/clinical truth changed.
5. **Update `docs/TECHDEBT.md`.**
   - delete fully resolved debt;
   - rewrite partially resolved debt so it describes only what remains.
6. **Update README/onboarding/migrations only when their current instructions or product truth changed.**
7. **Create/supersede an ADR only for a durable architectural decision**, not for routine implementation status.

Do not carry stale checkboxes or “not implemented” statements into the next phase when the code has already changed.

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
- Clinical analytics changes: cite the normative definition, test eligibility/insufficient-data behavior, and run production-database parity checks.

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

For urgent production fixes, branch from `main`, keep scope minimal, run the most relevant safety/regression checks, merge back through a PR whenever operationally possible, then perform the same documentation closeout before normal roadmap work resumes.
