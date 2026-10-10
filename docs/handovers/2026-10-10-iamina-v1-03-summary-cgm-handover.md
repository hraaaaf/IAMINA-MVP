# IAMINA V1-03 — Summary + CGM Safety Handover — 2026-10-10

**Goal:** local deterministic patient summary and no unverified normative CGM promotion in summary or companion. **Status:** PR #922 DRAFT/UNMERGED, technical code HEAD proven (see chronology below); docs SHA awaiting exact-head CI, release NOT AUTHORIZED.

## 2026-10-10 — V1-03 external text egress last-hop verified

- **Code HEAD:** `8292a130a674e132f011aea3d1d819547fba0571`; exact [CI #38037493525](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38037493525) **SUCCESS** (SQLite 2791 pass/5 skip/3 xfail; PG 2795 pass/1 skip/3 xfail; 125 subtests, anti-bypass+Ruff green), [migrations #38037493457](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38037493457) **SUCCESS**, [Companion #38037493521](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38037493521) **SUCCESS**. Flutter job skipped. PR #922 DRAFT/unmerged. `main@13b7cce` unaffected.
- **Change:** external provider text boundary `llm.factory::_execute_external_complete` now permits only exact static nonpatient generic pair from `core/external_text_v1.py` before network. Six synthetic adversarial patient prompt variants denied with zero provider calls despite mocked-approved provider+FinOps. Regex anonymization is not a release-safe anonymity guarantee.
- **Still open:** chat/stream/narrator build patient-derived prompts internally but provider text gateway denies them. Prove safe local UX and global AI optout; shadow `complete_text` adapter is a separate OFF-by-default staff-gated opaque-token route, evaluate separately; audit image/audio. `ai_provider=fallback` UI may misleadingly mark intentional local output as degraded. Qualified clinician/privacy/native language/RTL/accessibility + visual BEFORE/AFTER and legal pre-patient gate remain uncompleted. 29 approved decisions, 0 fully delivered.
- **Next:** CI of this subsequent docs-only HEAD; evaluate shadow/other egress and optout locally with synthetic fixtures; update Notion, correct defects, then seek independent human review. No merge, Vercel, real patients, pilot release.

## 2026-10-10 — Verified new code slice / handover update

- Code HEAD `c2effc096f86eb08e7c73118e17042fec3106ba2`, [CI #38036057381](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38036057381) SUCCESS (SQLite 2785 passed, PG 2789 passed; 125 subtests; dedicated Flutter skipped), [migration #38036057344](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38036057344) SUCCESS, [Companion #38036057367](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38036057367) SUCCESS. PR remains DRAFT/unmerged.
- Doctor Brief legacy generated-patient-data LLM route replaced by local-only descriptive copy; synthetic auth/no-consent/patient-isolation/zero-gateway/locale and CGM negative tests. Success log no longer contains patient ID + doctor brief content.
- Earlier [CI #38035782616](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38035782616) was genuinely red; obsolete tests/mocks corrected, scanner unchanged.
- Remaining: chat/stream and narrator patient-derived prompts and final provider egress allowlist, global AI opt-out, `ai_provider=fallback` UI truth and screenshots, qualified privacy/clinical/native language reviewers. This update itself creates a new SHA whose CI must be proved.
- Next exact: verify docs HEAD CI; then audit synthetic provider-bound payloads in chat/stream/narrator without network, and close only bounded proof. No merge, patient release or Vercel authorization.

## References
- Repository: `hraaaaf/IAMINA-MVP`; base `main@13b7cce12c86daf60119fb703f22e8c6c192cf8d`.
- Branch: `security/v1-03-summary-local-only-20261010`.
- PR: https://github.com/hraaaaf/IAMINA-MVP/pull/922
- Last proven technical code HEAD: `8ca3ac69657b5c2c7014286514af8231292f82e2`.
- CI: https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38034929969 SUCCESS (SQLite 2780 passed/5 skipped/3 xfailed; PG 2784 passed/1 skipped/3 xfailed; dedicated Flutter job skipped). Migration https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38034930096 SUCCESS. Companion real chat https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38034930097 SUCCESS.
- Main source of status: `docs/ROADMAP.md`; source of scope: `docs/assessments/2026-10-10-v1-03-summary-cgm-safety-audit.md`.
- Notion master: https://app.notion.com/p/3f477c66336281b28c78eb11c22f5ee6 (last update attempt for final CI was refused by safety controls; do not assert it was saved).

## Done on technical parent
- No model formatter on `run_clinical_analysis` / `/ai/summary`; legacy summary helper does not forward patient pivot.
- Negative synthetic tests for local-only provider denial, insufficient/empty summary, unverified CGM rows and companion context.
- Summaries present descriptive mean without labeling a 1-row result as continuous CGM TAR/TBR.
- Technical PostgreSQL+SQLite, security/lint and exact-parent screenshot E2E workflows succeeded.

## Open and blocked
- **This handover / roadmap update creates a NEW HEAD**. Prove CI and the actual PR HEAD before a confidence claim.
- Potential misleading degraded banner from `ai_provider=fallback`; no BEFORE/AFTER proof.
- Other LLM egress routes, final provider-bound payload, consent/opt-out/locale/security tests and clinical/linguistic review remain open.
- Existing V1-01 #920, V1-02 #921 and 29-decision checklist unchanged (29 approved, 0 fully delivered).
- No Vercel deploy, no patient rollout, no merge without required evidence and review.

## Next exact / sequence
Fetch HEAD and exact CI after this documentation commit; diagnose if red, otherwise inspect critical skips and collect technical evidence. Test remaining model routes with synthetic fixtures and enforce strict V1-03 zero-patient-context policy. Verify UI target/render semantics. Obtain required independent clinical/privacy/native reviewers and release certifier; only then consider merge, post-merge, handover and V1-04 follow-up. No human gate is waived.
