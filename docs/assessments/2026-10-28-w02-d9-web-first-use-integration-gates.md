# IAMINA W02/D9 — Existing-account first use: W01/D2 + W02 guarded candidate

**Date:** 2026-10-28. **Scope:** D9 only. **Status:** CANDIDATE, NOT_VERIFIED, NO patient GO. No merge or Vercel deployment.
**Source:** D9 PR #1003 (ba5f639), based on historical D7 (2bcea824); re-applied on protected W02 source cb7bd373 derived from W01/D2.
**D9 goal:** A previously onboarded authenticated patient does not repeat first-use; no medical payload/AI consent may be inferred or borrowed between accounts or devices.

## Technical integration and evidence
- The old D9 migration core.0020 **collided** with W01/D2 core.0020–0023; W02 has its own core.0024_w02_vault_revision_anchor. D9 is now core.0025_d9_first_use_completed_at, depending strictly on W02 0024. Previous QA branch is NOT migrated (0024=0, 0025=0 by implication, no write authorized).
- D9 server owner proof API GET/POST /api/v1/profile/first-use and explicit timestamp, owner derived exclusively from authenticated request; never a diagnosis, consent event or local profile restoration. Existing accounts without explicit server marker remain unknown and require a safe recovery decision.
- On Web, AppDatabase.forPatientVault **continues to refuse** unencrypted clinical storage (encrypted_web_patient_vault_unavailable); guest uses volatile WASM RAM. These guards supersede any unsafe first-use auto-bypass.
- Original PR #1003 source patch dry-run on W02: 14 files apply; consent-screen conflict. Consent guard manually rebased into the current W01/D2 versioned consent screen, maintaining remote account requirement and refusal if no owner-scoped local profile.
- No remote clinical profile hydration is implemented merely by the boolean first-use marker. Never treat remote completion as restored profile, AI consent, or permission to sync.

## Required D9 complete FUE matrix (all must PASS to close)
| Feature / scenario | Expected | Evidence / current verdict |
| --- | --- | --- |
| Same account A, local vault with verified first-use, cold reload | Skip repeat onboarding; no lost data | Historical local Chrome/SQLite tests; **NOT_RUN** on current hosted SHA |
| New account A, no remote marker | Explicit first-use shown; no synthetic clinical seed | Backend/Flutter test candidates; **NOT_RUN** in hosted browser |
| Existing A on a new device, valid owner-bound server marker | Skip duplicate questions *without fabricating local medical profile*, allow explicit safe setup/recovery | **NOT_RUN** hosted; recovery UX unresolved |
| Existing account without historical marker | Do not infer from diabetes treatment or old consent; recovery path explicit | **NOT_RUN** hosted; product UX unresolved |
| A → logout → B → A and forged bearer | No cross-account profile/consent/cache; logout revocation enforced | Synthetic old tests; **NOT_RUN** hosted on new branch |
| Offline, stale response after account switch, multi-tab, reload | Fail closed, clear retry/sign-out UX, no cross-user write | **NOT_RUN** hosted |
| AI consent separately authorized | Remote first-use marker cannot enable AI/network egress | Source guard candidate; **NOT_RUN** hosted |
| UI/UX FR/AR RTL & keyboard/touch | BEFORE→mockup→AFTER, 390×844 / 768×1024 / 1280×900, full functional journey | **NOT_RUN**, no D9 paired captures |
| Django on isolated QA Neon | Apply core.0024 then core.0025 with Django, independent SQL; synthetic A/B and cleanup auth_user=0 | **NOT_RUN**, sandbox security gate blocks QA DDL |
| Complete exact-HEAD code/CI + postmerge | Regression tests and FUE all green, score >=9/10, perfection pass, postmerge | **NOT_RUN** |

**BLOCKERS:** W01 G1–G7 formal closure and merge; D9 server proof not yet deployed; W02 encrypted patient vault not operational on hosted Web; Neon QA migration denied by security controls; first-login/auth plus historical account treatment; no complete D9 FUE; no reviewer/score. **D9 NOT_VERIFIED** regardless of unit CI green. No Production/no real patient/no Vercel deploy.

**Next:** run exact-head Python/Flutter/backend PG CI of this candidate; fix failures; prepare hosted Web protected path without weakening fail-closed; carry out FUE only on authorized isolated QA, then independent security/privacy/adversarial scoring and conditional merge/postmerge. Do not advance to D10 closure merely because D9 candidate compiles.
