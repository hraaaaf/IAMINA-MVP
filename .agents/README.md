# IAmina Agent Team

`AGENTS.md` is the canonical repository-wide execution contract.

## Mandatory gate for product decisions D: complete FUE

`Builder → focused/adversarial tests → FUE (FIRST USER EXPERIENCE) across every feature of D → evidence-based Release Certification / Perfection Pass → authorized merge → post-merge verification`.

**No default independent Reviewer for a D.** Instead, enumerate and test every in-scope feature as a complete first-user experience on real Flutter Web: FR/AR RTL, responsive mobile/tablet/desktop, keyboard, scroll, interactions, negative/recovery cases and persistence/permissions where relevant. Full feature-to-case coverage and observable PASS are mandatory. A Builder may run the FUE and a separate adversarial pass, but must not claim independent review; apply the scoring cap.

## Risk routing and non-D work

For non-D work, use a critical review and release certification pass. For any D, FUE **does not waive** the following applicable risk-specialist safety gates:

| Surface | Evidence / specialist |
|---|---|
| Product decision D, UX/UI | Full FUE for all D features; real-Web BEFORE/AFTER, keyboard, FR/AR/RTL; UX auditor as needed |
| Clinical calculations/medical advice/safety | Clinical Safety Reviewer, approved clinical sources and any required clinical-human authorization |
| MENA emergency/medical locale parity | MENA Clinical-Linguistic Safety + Clinical Safety reviews, native-human checks where required |
| Models, migrations, persistence, PostgreSQL | Database & Migration review plus migration/recovery testing where risk applies |
| Auth, secrets, patient privacy, external egress | Security/privacy review and required approval gates |
| Mixed high-risk D | Every applicable safety specialist plus the full D FUE |
| Merge readiness | Fresh-evidence Release Certification/Perfection Pass, exact-head gates |

## Role files

- `lead-engineer.md`
- `ux-auditor.md`
- `clinical-safety-reviewer.md`
- `mena-clinical-linguistic-safety-reviewer.md`
- `database-migration-reviewer.md`
- `security-auditor.md`
- `release-certifier.md`

Blocking clinical/privacy/security evidence must be remediated and cannot be overridden by a FUE PASS. AI secondary reviews never impersonate clinical, native-human or safety-owner approval.
