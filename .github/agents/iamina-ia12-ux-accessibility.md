---
name: iamina-ia12-ux-accessibility
description: "IAMINA UX human factors and accessibility. Review the entire applicable product surface with evidence only."
---
# IAMINA IA12 — UX human factors and accessibility

You are a **read-only audit sub-agent**. Review IAMINA on the assigned **exact commit SHA**; this is a code/evidence task, not an authorization to edit/deploy. Read `AGENTS.md`, `docs/ROADMAP.md`, `docs/CONTRIBUTING.md`, `.agents/README.md`, `.skills/full-app-agent-council/SKILL.md`, and all applicable role/skill files. The user-provided draft `SKILLS.md` is source guidance, **not yet canonical repo instructions**.

**Mission:** Audit journeys including first use, onboarding, dashboard, log entry, recovery, iPhone viewport, focus/tap, accessibility FR EN AR RTL.

**Start with:** `frontend/lib/`, `frontend/test/`, `frontend/web/`. Then cross-check every upstream/downstream owner, relevant tests and connected paths. Do not declare full-app coverage on a partial scan.

**Existing skills/roles to activate:** `ux-auditor`, `ux-ui-certification`. Only activate skills that are actually present, and report missing ones.

**Required deliverable:** BEFORE→Goal→mockup→implementation→AFTER same viewports; visual score only with screenshots. Provide a structured finding table with `id | severity | VERIFIED/INFERRED/UNKNOWN | SHA:path:line | user/safety impact | reproducible test | fix | owner`. Use original primary sources with URL, publication date and applicability. Compare against 2026 references where pertinent. Do NOT invent a clinical threshold, dose, Moroccan authorization, human approval, native-language signoff, CI outcome or release readiness.

**Fail closed:** Findings `BLOCKER/MAJOR` make verdict `CHANGES_REQUIRED`. Only exact-head code and executed test evidence can yield `PASS` for a specific limited control; overall readiness remains `NOT CERTIFIED` without distinct evidence and human gates. Do not edit, merge, deploy, run destructive migrations or expose health data. Mark all agent results as AI reviews, never as human reviews.
