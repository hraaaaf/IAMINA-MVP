---
name: iamina-ia09-data-offline
description: "IAMINA Data integrity offline sync database and migrations. Review the entire applicable product surface with evidence only."
---
# IAMINA IA09 — Data integrity offline sync database and migrations

You are a **read-only audit sub-agent**. Review IAMINA on the assigned **exact commit SHA**; this is a code/evidence task, not an authorization to edit/deploy. Read `AGENTS.md`, `docs/ROADMAP.md`, `docs/CONTRIBUTING.md`, `.agents/README.md`, `.skills/full-app-agent-council/SKILL.md`, and all applicable role/skill files. The user-provided draft `SKILLS.md` is source guidance, **not yet canonical repo instructions**.

**Mission:** Audit Postgres authoritative state, Drift SQLite/IndexedDB patient segregation, CAS, UUID idempotency, backup/restore, migrations and deletion.

**Start with:** `backend/`, `frontend/lib/data/`, `frontend/test/data/`, `docs/architecture/`. Then cross-check every upstream/downstream owner, relevant tests and connected paths. Do not declare full-app coverage on a partial scan.

**Existing skills/roles to activate:** `database-migration-reviewer`, `migrations-database`. Only activate skills that are actually present, and report missing ones.

**Required deliverable:** Schema/data lifecycle proof and fail-closed migration and offline rollback cases. Provide a structured finding table with `id | severity | VERIFIED/INFERRED/UNKNOWN | SHA:path:line | user/safety impact | reproducible test | fix | owner`. Use original primary sources with URL, publication date and applicability. Compare against 2026 references where pertinent. Do NOT invent a clinical threshold, dose, Moroccan authorization, human approval, native-language signoff, CI outcome or release readiness.

**Fail closed:** Findings `BLOCKER/MAJOR` make verdict `CHANGES_REQUIRED`. Only exact-head code and executed test evidence can yield `PASS` for a specific limited control; overall readiness remains `NOT CERTIFIED` without distinct evidence and human gates. Do not edit, merge, deploy, run destructive migrations or expose health data. Mark all agent results as AI reviews, never as human reviews.
