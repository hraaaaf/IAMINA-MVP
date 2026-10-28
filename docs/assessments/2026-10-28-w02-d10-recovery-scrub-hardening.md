# IAMINA W02/D10 — security hardening of isolated Option A synthetic restoration

Date: 2026-10-28. Source: W02/D10 secure preview cb7bd373e44daa79c78899c230b4a3832712c5fc.

## BEFORE — proven source defect
The synthetic Option A session returned a decrypted Uint8Array from store.restore(), then checked the account again after an await. If auth changed at that boundary, it threw without zeroing the decrypted array. Likewise, a malformed returned envelope could cause envelopeSha256() to throw before cleanup. The synthetic authority client accepted inconsistent uninitialized / ready metadata.

## Goal / success / evidence
- Goal: on account switch, invalid decrypted-envelope digest or contradictory revision state, reject and scrub acquired plaintext.
- Success: adversarial tests inject account switch at decrypt-return boundary, malformed envelope digest, poisoned server state; all reject and inspect the original returned bytes for zeroization. Existing create/commit/restore, rollback, owner and crash-recovery tests remain green.
- Technical scope: only scripts/fixtures/iamina_w02_option_a_client.mjs (synthetic, not patient runtime) plus tests, isolated workflow and this assessment.
- Secure boundary: real Web patient vault still fails closed with encrypted_web_patient_vault_unavailable. Guest SQLite WASM remains volatile in RAM.
- No clinical data, no Vercel deployment, no Neon migration, no new account, no key persistence.
- Proof: Node 22 + static guard GitHub Actions on exact commit; record actual result only after checking.
- Residual risk: JS garbage collector cannot guarantee zeroing every engine copy; key custody, Django core.0024 Neon QA migration, Flutter auth-epoch binding, encrypted SQLite executor, real recovery and W01 hosted FUE remain unproven. This does NOT certify clinical encryption.

Status: CANDIDATE / NOT_VERIFIED pending CI. D9 OPEN, patient NO-GO.
