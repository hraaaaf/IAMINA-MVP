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

## Mandatory Builder → full Decision FUE → evidence-based Certifier workflow

`AGENTS.md` and `docs/QUALITY_SCORING_POLICY.md` are normative. For **every product decision D**, the Builder must execute a **FUE (FIRST USER EXPERIENCE)** over **100% of the D's in-scope functionality** rather than waiting for a mandatory independent Reviewer. A FUE is a feature-by-feature first-user journey in actual Flutter Web/PWA (FR/AR RTL, 390×844/768×1024/1280×900, click/touch, keyboard, navigation, negative/recovery and storage/account behavior where relevant).

1. Builder defines the full D inventory, acceptance criteria and required FUE scenarios; implements and records focused/negative tests.
2. An adversarial pass challenges the result; then FUE records for each D feature: expected → observed → screenshot/log/test evidence → PASS/FAIL/NOT_RUN. **100% of required cases must have an observed PASS**. No independent Reviewer is required *just because the work is a D*; no static test or 9/9 CI may replace FUE.
3. Release Certification independently re-checks the **evidence**, score caps, final FUE verdict and exact-HEAD CI in a fresh pass. The same executor may perform isolated passes but must never claim independent review and is score-capped at 9.4.
4. Any risk-specific clinical/privacy/security/database reviewer or human approval is still mandatory **where risk and established policy require it**; no FUE can bypass safety gates.
5. Merge uses expected-head SHA locking where supported; verify `main` and post-merge CI before claiming 100%.

For non-D LOTs/hotfix/governance, use a Builder → critical evidence review → Release Certification chain. Mandatory skills for each relevant LOT: `.skills/lot-execution/SKILL.md` and `.skills/release-certification/SKILL.md`; include `.skills/ux-ui-certification/SKILL.md` for visual/interaction work. After any code or documentation change, revalidate all applicable exact-HEAD gates.

## Mandatory quality scoring and verification

`docs/QUALITY_SCORING_POLICY.md` is the canonical scoring contract and applies to every material step and every LOT.

- Every material step receives `EXECUTION_SCORE /10` and `ADVERSARIAL_SCORE /10`.
- The retained score is always the lower admissible score after applicable caps, never an average.
- A LOT score is the lowest retained material-step score, never an average across steps.
- A score gap greater than `0.5` requires investigation, remediation/justification, rerun of affected evidence, and rescore.
- `10/10` is exceptional; `9.5+` requires genuine independent review **to claim that exceptional score**, not as a generic D gate.
- Same executor + adversarial reviewer is automatically capped at `9.4/10`.
- Required red test or missing/stale required proof caps at `7.9/10`.
- Demonstrated regression caps at `6.9/10` until remediated and rerun.
- Blocking security/privacy/data-integrity/clinical-claim finding caps at `5.9/10` and forces `BLOCKED`.
- For UI/UX, visual fidelity without a real Target ↔ Render comparison at required identical viewports/states is capped at `7.5/10`.
- No weak critical dimension may be hidden by a strong average.
- A LOT may be `VERIFIED` only at retained score `>=9.0/10`, with every required binary gate green, no blocker, resolved scoring discrepancies, and a completed Perfection Pass.
- Even at `9.0+`, the final Perfection Pass is mandatory: enumerate remaining weaknesses, fix every materially improvable in-scope weakness, rerun affected evidence, and rescore.

Scores never override binary gates.

## Source of truth discipline

- `docs/ROADMAP.md`: single forward backlog, priorities, gates, recent closeout state.
- `docs/architecture/ARCHITECTURE.md`: current architecture and target boundaries.
- `docs/SPECS.md`: current product/API capability contract.
- `docs/MEDICAL_DATA_PLAN.md`: current clinical-data and safety contract.
- `docs/QUALITY_SCORING_POLICY.md`: canonical execution/adversarial scoring, caps, verification threshold and Perfection Pass.
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
5. material-step Execution/Adversarial/retained scores, applicable caps and any discrepancy investigation;
6. Perfection Pass result before VERIFIED;
7. any manual verification still required;
8. which canonical docs must change at closeout;
9. Builder pass, **for D: exhaustive FUE feature matrix, coverage and FUE_PASS/FUE_NO_GO**, any risk-specialist verdicts, and Release Certifier verdict.

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
