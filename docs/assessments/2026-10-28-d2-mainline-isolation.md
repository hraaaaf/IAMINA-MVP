# D2 Web — pré-merge / FUE evidence gate — 2026-10-28

## Evaluated candidate
- PR: #1163 (Draft), branch `feat/d2-web-mainline-isolated-20261028`.
- Evidence HEAD before this note: `dc184d29d09e7686d726d5ed1163e07402ec58e3`, base `main@8ada5aab8e8006bbbdc275eabbabf014a4714e0b`.
- 12/12 GitHub workflow **success** on that SHA, including general CI #40782645720, Django migration drift #40782645596 and UI browser screenshot #40782645615.
- CI job names confirmed: backend Ruff/pytest, PostgreSQL, frontend analysis/tests/PWA build. These outcomes support code-level checks but do **not** individually demonstrate all real-browser D2 states.
- This documentation commit changes HEAD. Its resulting CI and exact-HEAD proofs must be considered separately.

## Goal / expected success / proof
Goal: D2 is a consent-gated, patient-scoped, opt-in **in-app observation preview and voluntary saved inbox**; no unsolicited medical notification or browser push; J+7 display expiry, with a clearly distinguished physical purge operation.

Success: no unauthorized or stale A→B reads, no automatic dispatch, consent revoke removes derived rows, expiry enforced and physically purged under an approved schedule if strict storage erasure is claimed. Full FUE requires real browser evidence on all affected D2 features.

## Focused source inspection (same executor, not an independent sign-off)
- `backend/diabetes/api/v1/d2_inbox.py`: GET filters `patient=request.user, expires_at__gt=now`; save demands current consent, CSRF where cookie, sourced nonurgent deterministic preview and explicit acknowledgment, max 20, patient row lock, HMAC signature. Read/write/delete are patient scoped.
- `backend/core/api/v1/d2_preview_consent.py`: D2 opt-in requires current global AI consent and exact localized notice/hash; cookie CSRF enforced on mutation; revoke deletes D2 notices.
- `frontend/lib/services/d2_notification_policy.dart`: browser push disabled, fail-closed on patient/epoch/consent/evidence/clinical-authority conditions.
- `backend/core/management/commands/purge_d2_expired_notices.py`: dry-run default, explicit `--apply`, expiry `<= cutoff`, transactional bounded batches (1..1000), final remaining check. `backend/core/tests/test_d2_expired_notice_purge.py` includes dry run, exact boundary, A/B rows, invalid batch, idempotent rerun.
- **Limitation**: no activated scheduler; therefore J+7 **display expiration is implemented**, but guaranteed J+7 physical DB deletion is **NOT VERIFIED**. Backups and restore/reappearance are not covered by this command.

## Required D2 FUE matrix (runtime evidence on exact evaluated HEAD)
| D2 feature / first-user journey | Required observation | Current verdict |
| --- | --- | --- |
| Rappels vs Notifications entry and clear no-push wording | FR+AR/RTL, 390×844 / 768×1024 / 1280×900, touch/click and browser screenshot BEFORE/AFTER | NOT_RUN as full D2 matrix |
| Consent initial OFF, exact notice, positive grant | visible UI action + server state + keyboard focus/Tab/Shift+Tab | NOT_RUN |
| Consent revoke and navigation away/back | server revocation, saved entries gone, refresh/offline/error recovery | NOT_RUN |
| No consent / global AI opt-out / locked / stale auth epoch | deny paths visible and no patient info leakage | NOT_RUN as full browser FUE |
| Explicit save of governed nonurgent preview | one saved item, dedup and no automatic producer/send | NOT_RUN as real browser E2E |
| Inbox read, delete, empty, cap and 7-day stale expiry | persisted state across reload; expired hidden | NOT_RUN as real browser E2E |
| A→B→A account swap | independent patient-scoped Web→BFF→API→DB isolation, stale requests blocked | NOT_RUN; W01 protected hosted identity prerequisite |
| Accessibility and locale error states | keyboard, focus, screen-reader semantics, FR/EN/AR RTL | NOT_RUN as comprehensive run |
| J+7 physical purge & recovery | operation/schedule, database before/after, restore/backups policy | NOT_RUN operationally |

**Verdict: FUE_NO_GO.** This means evidence is incomplete, not that source tests failed. Generic visual workflows cannot be substituted for D2-specific journeys.

## Risk / adversarial pass
- **Clinical authority:** descriptive nonurgent source only; no generator dispatch path observed in inspected modules; needs risk-specific confirmation on full integrated runtime.
- **Privacy:** status/consent/inbox patient-scoped in inspected source; hosted account and browser vault isolation require proof.
- **Retention:** J+7 storage erasure claim prohibited until scheduler, monitoring, backup/restore handling and retention authorization established.
- **UX:** old visual examples exist in historical #1135 but no same-HEAD full state-and-locale target/render matrix. Visual-fidelity score capped at 7.5/10.
- **Governance:** current `AGENTS.md` requires complete FUE for every D. A separately staffed code reviewer is not a blanket D gate; risk-specific clinical/security/privacy human approvals remain relevant where applicable.

## Quality record (evidence-bounded)
- Goal: candidate D2 preview-only, patient-scoped, no dispatch.
- Success criterion: full browser FUE plus operational retention semantics evidenced.
- Evidence: exact source inspection and 12 successful workflow conclusions.
- EXECUTION_SCORE: 7.5/10 (provisional; incomplete FUE).
- ADVERSARIAL_SCORE: 7.5/10 (same executor; incomplete Web and physical-retention proof).
- Gap: 0.0.
- Applicable cap: required FUE evidence missing <=7.9; unobserved target/render visual proof <=7.5.
- RETAINED_SCORE: 7.5/10, **NOT_VERIFIED / FUE_NO_GO**.
- No release certification, no Ready-for-merge, no merge, no Vercel deployment.

## Next exact
1. Inspect CI test collection and screenshot artifacts, map existing evidence to D2 features.
2. Execute remaining D2-specific FR/EN/AR browser journeys at 390/768/1280 with keyboard/focus, offline and recovery.
3. Run authenticated **synthetic-only** A→B→A and retention database tests only against verified isolated identity/DB; stop before creation when fingerprints mismatch.
4. Decide whether operational J+7 erasure is in scope; if yes, approve scheduler/backup policy separately before activation.
5. Repeat exact-HEAD tests, dedicated critical/adversarial and release-certifier passes, FUE verdict and perfection pass. Merge only if all gates pass. No Vercel deployment without explicit owner GO.
