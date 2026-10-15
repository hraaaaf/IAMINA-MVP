---
name: iamina-council-coordinator
description: "Orchestrate a full-application fifteen-specialist IAMINA evidence audit with independent AI sub-agent contexts and a release-evidence matrix."
---
# IAMINA full-app council coordinator

Review **ALL** of IAMINA: Flutter web/iOS/Android, Django/Ninja, Postgres, Drift offline/backup/sync, diabetes safety, CGM, medication, nutrition, Darija/FR/EN/AR, companion AI, providers, security/privacy/consent, QA/CI, UX, PWA/Vercel and regulatory claims.

Read `AGENTS.md`, `docs/CONTRIBUTING.md`, `docs/ROADMAP.md`, `.agents/README.md`, `.skills/full-app-agent-council/SKILL.md`, then freeze exact `main` SHA and inventory repo.

Use the runtime's **actual sub-agent API** to start *fifteen separate context-isolated tasks* for `iamina-ia01-architecture` through `iamina-ia15-adversarial`. Run read-only in parallel where supported; enforce domain-specific source research, no patient data, shared SHA. Let IA15 reconstruct findings independently, not merely repeat specialist outputs. Wait only for genuinely running agent tasks, never fabricate subagent IDs, messages, execution, screenshots, test results or approvals. If sub-agent execution isn't available, mark `AGENT_NOT_RUN` and offer a separate operator/runtime; *a static script is not a sub-agent*.

Per-agent output: `agent id | session/run ID or NOT_RUN | exact SHA | scoped file inventory | external primary sources | findings | concrete tests/results | blockers | verdict`. Merge contradictions into a single risk register sorted BLOCKER → MAJOR → MINOR. Clinical/linguistic/regulatory specialist AI outputs are secondary research, never a qualified human clinical, native or regulatory approval.

**Required system proof:** GitHub CI on exact SHA plus observed production-independent evidence. No Vercel deploy without explicit user permission. No merge of security bypasses or production use with real patient data. Builder, reviewers and certifier must be distinct executions when the runtime can spawn them. If not, accurately state isolation unavailable and retain human gates.

**Completion:** fifteen evidenced agent runs (not merely fifteen profiles), no untriaged BLOCKER, exact-head technical checks, issue references, canonical handover and CI postmerge. Otherwise label `PARTIAL / HUMAN_GATE`.
