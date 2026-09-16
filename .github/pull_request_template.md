<!-- One focused PR = one ROADMAP unit or one clearly scoped maintenance purpose. -->

## Scope
<!-- Name the exact ROADMAP item or maintenance purpose. -->


## What changed and why


## Safety / privacy impact
<!-- State impact on emergency handling, clinical authority, locale safety, auth, data egress, consent, or write "none". -->


## Validation
- [ ] Relevant focused tests added/run
- [ ] Backend checks/tests run when applicable
- [ ] Flutter analyze/tests run when applicable
- [ ] API/OpenAPI artifact updated when applicable
- [ ] Migration/recovery path validated when applicable
- [ ] Production-database parity checked when clinical/raw SQL behavior differs by database

## Quality scoring
<!-- Mandatory for every material step. Canon: docs/QUALITY_SCORING_POLICY.md -->

### Material step
- Goal:
- Success criterion:
- Evidence:
- Critical dimensions:
- EXECUTION_SCORE: `/10`
- ADVERSARIAL_SCORE: `/10`
- Gap:
- Applicable caps: `none`
- RETAINED_SCORE: `/10`
- Status: `OPEN | BLOCKED | READY_FOR_PERFECTION_PASS | VERIFIED`
- Remaining weaknesses:
- Next exact action:

### LOT closeout
- [ ] No Execution/Adversarial averaging used; retained score is the minimum admissible score
- [ ] Any score gap `>0.5` investigated and resolved
- [ ] Required caps applied (`7.9` missing/red proof, `6.9` regression, `5.9 + BLOCKED` security/privacy/data/clinical blocker, UI fidelity `7.5` without Target ↔ Render)
- [ ] Same executor + adversarial reviewer capped at `9.4/10`
- [ ] Any `9.5+` score has a genuinely independent review
- [ ] No weak critical dimension hidden by a stronger average
- [ ] All required binary gates green on exact HEAD
- [ ] Final retained LOT score is `>=9.0/10` before `VERIFIED`
- [ ] Final Perfection Pass completed and all materially improvable in-scope weaknesses fixed + affected evidence rerun

Final retained LOT score: `/10`
Independent reviewer: `yes | no`
Perfection Pass result:

## Documentation closeout
<!-- A merged task is not closed until canonical docs match the merged truth. -->
- [ ] `docs/ROADMAP.md` inspected and updated for closeout/next blocker when needed
- [ ] `docs/architecture/ARCHITECTURE.md` updated if the as-built architecture changed
- [ ] `docs/SPECS.md` updated if a durable capability/API contract changed
- [ ] Domain contract docs (for example `MEDICAL_DATA_PLAN.md`) updated if their truth changed
- [ ] `docs/TECHDEBT.md` cleaned: resolved debt removed; partially resolved debt rewritten to only what remains
- [ ] README/onboarding/migrations updated only if their current instructions or product truth changed
- [ ] No session-state/status diary added to `CLAUDE.md` or `AGENTS.md`

## Remaining debt / explicit non-goals
<!-- List what remains open so the next phase does not assume this PR solved more than it did. -->


## Manual inspection required
<!-- List judgement calls, security/safety-sensitive changes, migrations, deployment steps, or API-breaking changes. Write "none" if none. -->

none
