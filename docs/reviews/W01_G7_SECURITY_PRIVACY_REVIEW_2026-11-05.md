# IAMINA W01 — G7 Security & Privacy Independent Review Packet — 05/11/2026

> **STATUS: REVIEW REQUIRED / NOT CERTIFIED.** This document packages observed controls and unresolved issues for a genuinely independent reviewer. It is not a sign-off or clinical-production approval.

## Decision and boundary

- **Goal:** independently verify security and privacy for IAMINA W01 Web → API → synthetic PostgreSQL, with authenticated patient A/B isolation, token invalidation, CSRF/CORS, log privacy, and safe rollback.
- **Success:** a reviewer who did not implement the changes independently reproduces the critical negatives and positives on the precise candidate SHA, signs off or requests changes with evidence. For healthcare Production, a separate explicit release and clinical/privacy governance review is required.
- **Evidence:** GitHub CI logs, backend HTTP PostgreSQL checks, exact Vercel Preview SHA, synthetic Neon measurements, negative auth/proxy tests, plus independent GitHub review or signed report.
- **Exclusions:** no real patient data, no Production DB changes, no Vercel production deployment, no merge, no pricing change.
- **G2:** explicitly CANCELLED/WAIVED by the owner, not PASSED. The residual Production Neon branch/network risks remain recorded and are not nullified by this G7 checklist.

## Pinned evidence and scope

- Candidate application SHA: `14a97bfa4fc74a8869ff7c7de16b9cf800b4ab70` (the Vercel Web/API Preview build). W01 documentation-only successor `1e69c482d8b818a44df8ee58ab3d53ef8279abc1` ran **17/17 completed SUCCESS** on GitHub.
- PR: https://github.com/hraaaaf/IAMINA-MVP/pull/1273 (Draft, not merged). Main CI: https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42083726919 ; W01 architecture: https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42083727046 ; D7 FUE: https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42083726801 .
- API Preview `dpl_6Zc8R98hqfW661GXHD51T7cNsEbJ` and Web Preview `dpl_DwF8G2ZE3sUF7TehcsSwTkEz7qFi`, READY at the pinned candidate SHA. Safari A→B→A and isolation were acknowledged by the owner; independent instrumented trace not supplied.
- Synthetic DB is Neon `noisy-truth-00115950`/`br-sweet-frog-b9ok6ptp` with the expected runtime host `ep-old-art-b9sy0oo4.c-7.eu-central-1.aws.neon.tech` (branch and host read back and verified).

## Source-level controls observed (reviewer must validate, not just trust)

| Area | Observed code/tests | Independent test required |
| --- | --- | --- |
| Native auth, logout | `backend/core/native_auth.py`, `backend/core/api/v1/auth.py`: timestamped signed token bound to revocation version; logout verifies bearer before increment. | Old token A must receive 401 after logout, new A works, B unaffected; tampered A 401. |
| Ownership | `backend/diabetes/api/v1/logs.py` has operation-level bearer/session auth and patient-filtered CRUD; `backend/core/tests/test_w01_native_logout_http.py` exercises cross-account GET/PATCH/DELETE as 404. | Repeat A→B→A against hosted synthetic API, then test IDOR over all personal-resource routers, not only logs. |
| Cookie + bearer conflict | `backend/diabetes/api/v1/security.py`, `backend/amina/vercel_session_auth.py` reject conflicting identities and invalid Authorization fallback. | Inject valid cookie for B plus A bearer; expect 401 and no data leakage. |
| CSRF | `backend/amina/middleware/csrf_exempt_api.py` exempts bearer requests and a specific bootstrap path. | Verify session-cookie writes without valid CSRF are rejected, and bearer-only authenticated writes are permitted as designed. |
| Preview registration | `backend/core/api/v1/auth.py` rejects `POST /auth/register` in hosted Preview without explicit server opt-in. | Direct HTTP 403 and zero account/profile delta. |
| Web same-origin bridge | `frontend/api/index.js` rejects unexpected env/project/targets/paths, strips cookies, requires an OIDC token, does not follow redirects, limits response to 25 MiB. | Probe no OIDC, destination tampering, redirects, unsupported method/path; verify token never reaches browser. |
| TLS/headers | `backend/amina/settings.py` enables secure session/CSRF cookies, SSL redirect, HSTS, nosniff and DENY framing when DEBUG=False; Vercel DEBUG=False (Preview and Production env). | Inspect deployed response headers over HTTPS without exposing auth state or secrets. |
| Abuse throttling | `backend/core/auth_abuse.py` applies persistent DB buckets for login/register/password reset, with keyed-hash identifiers. | Perform bounded synthetic 429 test; confirm rate-limit bypass is impossible in the **actual** Vercel ingress configuration. |

## Findings to resolve or expressly accept

1. **G6 remains partial (HIGH for recovery assurance).** A snapshot from 21/10 restored into the sandbox, but the restore tool unexpectedly swapped the default branch and compute. This was reversed with readback proof. On 05/11 a current-state **clone** was independently read on an auxiliary endpoint and matched source: 46 public tables, 2 users, 2 profiles, 78 events, 76 auth-abuse buckets and table-name MD5 `4e8d7f3896f72acc964c7a8d54b3d19c`. The original default branch and host stayed unchanged during the clone read. This does **not** prove off-project backup recovery or full-row integrity, and a new snapshot was rejected `HTTP 422 snapshots limit exceeded`.
2. **Token lifetime (REVIEW).** `backend/core/native_auth.py` defaults to 30-day bearer validity unless configured otherwise; logout revokes by per-profile version. Reviewer should evaluate session duration/secure client storage and revocation against the healthcare threat model. No exploit asserted.
3. **Client IP provenance (CONDITIONAL).** `backend/core/auth_abuse.py` consumes the leftmost `X-Forwarded-For`. Vercel's official docs explicitly say its standard ingress overwrites this header to prevent spoofing: https://vercel.com/docs/headers/request-headers . MDN warns that outside trusted proxy setups an untrusted leftmost value could bypass IP rate limits: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Forwarded-For . **No hosted vulnerability demonstrated**; reassess before custom proxies, host migration or bypassing Vercel ingress.
4. **Independent sign-off (BLOCKING).** GitHub PR #1273 had **zero reviews** at the latest check. CI green and owner Safari confirmation do not constitute independent security/privacy sign-off.
5. **Clinical governance (SEPARATE).** G2 was removed from the W01 work plan by the owner. This is not proof of Production protection, legal compliance, medical safety, retention controls or data-subject-rights readiness.

## Suggested independent reviewer protocol (read-only / synthetic)

- [ ] Review the code diff against `main` at the SHA submitted, not a moving branch.
- [ ] Confirm all patient-specific API routers enforce ownership and audit any resource enumeration, not just glucose journal.
- [ ] Reproduce bearer invalidity, logout revocation, cookie/bearer conflict, registration block, abuse 429 and CSRF/CORS fail-closed on synthetic PostgreSQL.
- [ ] Verify frontend OIDC bridge protection and that logs/traces contain no bearer/cookie/PHI; inspect trace retention and redaction policies.
- [ ] Confirm actual Preview API is bound to synthetic DB; protect source against accidental switch during G6. The clone is **not** a substitute for disaster recovery.
- [ ] Give explicit written PASS/CHANGES_REQUIRED verdict with reviewer identity, date, SHA, evidence URLs and residual risks. No self-approval.

## Current decision

**G7 OPEN / NO SIGN-OFF. G6 PARTIAL. G2 OWNER-WAIVED, NOT SECURE.** PR stays Draft. Do not merge or deploy to Production based on this evidence pack alone. Next exact: request a real independent reviewer after a named reviewer is available; perform safe current backup/restoration certification separately.

Canonical W01 continuation: `docs/assessments/2026-11-04-w01-current-main-synthetic-preview.md`; audit log: https://app.notion.com/p/3fc77c66336281ab8bfcf0c6b0060e2f .


## Addendum de gouvernance et preuve CI — 05/11/2026 (remplace les priorités antérieures)

**Le propriétaire a confirmé que l'application est encore en développement et n'a pas de données de patients réels.** La sauvegarde/restauration complète **G6 est donc REPORTÉE au gate de préproduction réelle**, non supprimée et **non bloquante pour le développement W01**. Les risques d'absence de sauvegarde indépendante restent valables pour un futur lancement patient. **G2 est explicitement ANNULÉ/WAIVED** par le propriétaire pour ce chantier, jamais déclaré PASS ni protection de Production obtenue. Ne pas rouvrir G2 ni manipuler Neon G6 sans nouveau besoin justifié.

Le candidat GitHub `31f12e94a6301d50dcb1ee5e1335e02b9eadcf48` dispose de **17/17 workflows COMPLETED/SUCCESS** vérifiés : [CI générale #42111037305](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42111037305) (Ruff+pytest, PostgreSQL et Frontend SUCCESS), [UI Chrome #42111037412](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42111037412) (3 jobs SUCCESS 390×844/768×1024/1280×900 ; trois artifacts non expirés), [D11 Web PG16 FR/AR #42111037450](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42111037450) SUCCESS, [Developer portability #42111037312](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42111037312) SUCCESS. Correctif Chrome limité au harness, sans changement UI ni relâchement des assertions de capture.

**G7 demeure OPEN** : GitHub #1273 n'a **aucune review enregistrée** au dernier contrôle. Un reviewer indépendant doit produire un verdict PASS/CHANGES_REQUIRED à la SHA examinée ; le mainteneur/auteur et cet agent ne peuvent pas se substituer à cette revue. **La certification technique de la CI ne vaut pas sécurité/privacy clinique ni autorisation de Production.** Previews existantes sur le SHA runtime `14a97bfa...`, non sur `31f12e94a6301d50dcb1ee5e1335e02b9eadcf48`. PR Draft, aucun merge ni nouveau déploiement.

**Next :** faire examiner le dossier par une personne indépendante identifiable ; documenter le verdict et les éventuelles corrections. Le présent addendum est documentaire et crée un nouveau commit, dont la CI doit être recontrôlée séparément.
