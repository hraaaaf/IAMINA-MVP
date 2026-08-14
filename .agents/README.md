# IAmina Agent Team

This directory defines role briefs. `AGENTS.md` remains the canonical repository-wide execution contract.

## Mandatory execution chain

`Builder -> applicable Reviewer(s) -> Release Certifier -> merge -> post-merge verification`

The Builder may not certify its own LOT. When orchestration supports separate agents, use separate agents. When only one runtime/session is available, roles must still be executed as explicit isolated passes: the Reviewer re-reads evidence without relying on Builder conclusions, and the Certifier independently re-checks the final diff and exact-head evidence.

## Routing matrix

| Change surface | Builder | Required Reviewer |
|---|---|---|
| Any LOT | Lead Engineer | at least one scope-appropriate Reviewer |
| UX/UI, navigation, responsive, i18n presentation | Lead Engineer | UX Auditor |
| Clinical calculation, medical wording, safety behavior | Lead Engineer | Clinical Safety Reviewer |
| MENA safety corpus, Darija/Arabic/transliteration or multilingual emergency parity | Lead Engineer | MENA Clinical-Linguistic Safety Reviewer + Clinical Safety Reviewer |
| Models, migrations, persistence, PostgreSQL-sensitive behavior | Lead Engineer | Database & Migration Reviewer |
| Auth, authorization, privacy, secrets, external egress | Lead Engineer | Security Auditor |
| Mixed high-risk change | Lead Engineer | every applicable specialist Reviewer |
| Final merge readiness | — | Release Certifier always required |

## Role files
- `lead-engineer.md`
- `ux-auditor.md`
- `clinical-safety-reviewer.md`
- `mena-clinical-linguistic-safety-reviewer.md`
- `database-migration-reviewer.md`
- `security-auditor.md`
- `release-certifier.md`

Reviewer findings are evidence, not suggestions: blocking findings must be remediated before certification unless the human owner explicitly accepts the risk and the repository's safety rules permit that acceptance.

The MENA Clinical-Linguistic Safety Reviewer is an AI secondary reviewer. It strengthens corpus evidence but cannot impersonate or replace restricted native-human, clinical-human or safety-owner approval.