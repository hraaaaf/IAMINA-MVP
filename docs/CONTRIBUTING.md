# Contributing

---

## ⛔ Guardrails — never break these (patient safety + compliance)

These are non-negotiable. A change that touches any of them needs an explicit human decision —
flag it in the PR's "Needs manual inspection" section. Do **not** let an agent silently alter them.

- **`TriageVitalMiddleware` runs first** in the middleware chain — the medical-emergency gate.
  Never bypass, reorder, or route an emergency message to the LLM. New interactive endpoints must
  register in the triage registry.
- **`UnitGuardMiddleware` runs second** — glucose-unit normalization, upstream of all AI logic.
- **PHI is stripped before the LLM** — patient data never reaches the model. The only sanctioned
  LLM entry point is `core/llm_gateway.narrate()`; modules must not call `get_llm()` directly.
- **KPIs are SQL-first** (ADR-0007) — never computed in Python.
- **No diagnosis, no prescription** — companion role only; medical urgencies get a fixed,
  pre-validated response, never an LLM-generated one.
- **Never modify middleware order** without explicit approval.
- **`client_uuid` on log entries** is the offline-sync idempotency key — don't remove or repurpose it.

**Hard safety gate — must clear before a single real patient touches the app:**
- **Darija orthographic-variant suicidal-ideation coverage** — one `xfail` documents that misspelled
  high-severity terms in Darija slip past the triage gate. Close it with a native corpus. **Hard
  launch blocker**, not a soft one.
- **Emergency events must reach a human** — `ClinicalLogger` emergency events must route to a
  monitored alert channel before any pilot. A triage gate that fires into an unread log protects no one.

> Full architectural rationale: `docs/architecture/ARCHITECTURE.md` (Key Invariants) and `docs/adr/`.

---

## Branches

```
main          production-ready, tagged releases
dev           integration — all feature branches merge here
```

```bash
# Always branch from dev
git checkout dev && git pull origin dev
git checkout -b feature/short-description   # or fix/, chore/, docs/
```

---

## Working in parallel (2-person / agent handoff)

The goal: either of us (or an agent) can pick up work, ship it, and hand off — without stepping
on each other. There is **no claim/lock layer**; collisions are avoided by keeping units small and
merging fast. The discipline:

- **`docs/ROADMAP.md` is the backlog.** Pick the next unstarted item from there (prelaunch path or
  "Platform seam debt"), in order. It is the single source of truth for *what* and *what's next*.
- **`CLAUDE.md` is the auto-loaded brief** — it's read into every agent session automatically. Its
  "Session State" block is a *pointer* to ROADMAP plus the current branch + next actionable. Keep
  it tiny. **Replace** that block each session — never append a new one (that's how it drifted to
  three stacked blocks before).
- **One unit = one short-lived branch off `dev` = one small PR.** Branch from up-to-date `dev`,
  keep the change focused (< ~400 lines), open the PR, merge fast (`--rebase --delete-branch`).
  A taken unit is visible as an open branch/PR — that's the only signal you need at this size.
- **Pull before you start.** `git checkout dev && git pull` so you branch from the latest.
- **Handoff lives in git, not prose.** The next person's context = the open PR (description + diff),
  commit messages, and ROADMAP checkboxes. Don't maintain a separate "where we are" status file —
  it rots and forks. (This is why `STATE.md` was removed.)

### Update ritual (after any unit of work — only 2 steps)

1. Tick / update the relevant checkbox(es) in `docs/ROADMAP.md`.
2. Refresh the single "Session State" block in `CLAUDE.md` (branch + next actionable). Replace, don't append.

That's it. Don't update multiple "compass" files — one backlog (ROADMAP), one brief (CLAUDE.md).

---

## Commits

Format: `type(scope): subject` — keep subject under 50 chars, imperative mood.

```
feat(api): add batch log endpoint
fix(flutter): null guard on fatigueLevel in SyncService
chore(deps): upgrade firebase_core to 3.15
docs(roadmap): update Phase 5 status
```

Types: `feat` `fix` `refactor` `test` `chore` `docs`

---

## Pull Requests

```bash
git push origin feature/short-description
gh pr create --title "type(scope): description" --body "..."
```

PR body: follow `.github/pull_request_template.md` — name the **one ROADMAP unit**, what/why,
and fill the "⚠️ Needs manual inspection" section (that's how an agent flags judgement calls,
migrations, or middleware/security changes to the human dev). Keep PRs under ~400 lines.

### Merge model — CI gates, no human approval

Development is done by agents; **no one reviews/approves PRs**. The gate is **CI, not a human**:

- A PR merges as soon as CI is green. Use auto-merge so the agent doesn't wait or merge on red:
  ```bash
  gh pr merge --auto --rebase --delete-branch
  ```
- **CI is the integration gate** (runs on PRs to `dev` and `main`): ruff · import-linter · bandit ·
  OpenAPI-schema-current · pytest · flutter analyze. Red CI = the merge does not happen. Fix and push.
- **`pr-size` is advisory, not blocking** — it warns (PR summary) when a diff exceeds ~400 lines so a
  large or multi-unit PR is visible to the human dev, without stopping the agent pipeline.
- If the OpenAPI check fails, regenerate: `python backend/manage.py export_openapi > docs/api/openapi.json`.

Merge strategy: **rebase** (`--rebase --delete-branch`). No merge commits.

> To *enforce* "green before merge" without a human, enable GitHub branch protection on `dev` with
> **required status checks + 0 required reviewers** (not done yet — `dev` currently relies on agents
> using `--auto`). That's the only setting that hard-blocks a red merge while requiring no approval.

---

## Pre-PR Checklist

```bash
# Backend
source venv/bin/activate
python backend/manage.py check
python backend/manage.py test

# Frontend
cd frontend
flutter analyze
flutter test
```

---

## Code Standards

**Python:** PEP 8, type hints on function signatures, `ruff format backend/` before committing.

**Dart:** 2-space indent, trailing commas on multiline, `dart format lib/` before committing.

**Migrations:** Never edit generated migration files. Always test `migrate` → `migrate zero` → `migrate` locally.

---

## Hotfix

```bash
git checkout -b hotfix/description main
# fix, test, then:
gh pr create --title "fix: ..." --base main
# after merge, also merge into dev
git checkout dev && git merge main
```
