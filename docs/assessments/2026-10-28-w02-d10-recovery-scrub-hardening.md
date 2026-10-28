# IAMINA W02/D10 — security hardening of isolated Option A synthetic restoration

Date: 2026-10-28. Source: W02/D10 secure preview cb7bd373e44daa79c78899c230b4a3832712c5fc.

## BEFORE — proven source defect
The synthetic Option A session returned a decrypted Uint8Array from store.restore(), then checked the account again after an await. If auth changed at that boundary, it threw without zeroing the decrypted array. Likewise, a malformed returned envelope could cause envelopeSha256() to throw before cleanup. A second analogous path existed in finalizePendingSynthetic crash recovery, after restore decrypted the pending envelope. The synthetic authority client accepted inconsistent uninitialized / ready metadata.

## Goal / success / evidence
- Goal: on account switch, invalid decrypted-envelope digest or contradictory revision state, reject and scrub acquired plaintext.
- Success: adversarial tests inject account switch at decrypt-return boundary, malformed envelope digest, poisoned server state, and pending recovery digest/account-switch races; all reject and inspect the original returned bytes for zeroization. Existing create/commit/restore, rollback, owner and crash-recovery tests remain green.
- Technical scope: only scripts/fixtures/iamina_w02_option_a_client.mjs (synthetic, not patient runtime) plus tests, isolated workflow and this assessment.
- Secure boundary: real Web patient vault still fails closed with encrypted_web_patient_vault_unavailable. Guest SQLite WASM remains volatile in RAM.
- No clinical data, no Vercel deployment, no Neon migration, no new account, no key persistence.
- Proof: Node 22 + static guard GitHub Actions on exact commit; record actual result only after checking.
- Residual risk: JS garbage collector cannot guarantee zeroing every engine copy; key custody, Django core.0024 Neon QA migration, Flutter auth-epoch binding, encrypted SQLite executor, real recovery and W01 hosted FUE remain unproven. This does NOT certify clinical encryption.

Status: CANDIDATE / NOT_VERIFIED pending CI. D9 OPEN, patient NO-GO.


## Exact-head security CI evidence — 2026-10-28

**Code SHA:** 5bf1e597ae6cfa0799d1dce81a85febf89a3ac85. **CI** [#40768231956](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40768231956) **SUCCESS** on exact SHA; job `synthetic-crypto-adversarial` SUCCESS. GitHub job log proves **70/70 Node 22 tests PASS, 0 FAIL**, plus **5/5 Python Web plaintext fail-closed tests PASS**. The test suite covers normal decrypt, wrong owner, stale revisions/digests, crash with pending reservation, restore-time account switch and malformed envelope, plus newly added account revocation during remote finalization ACK.

**Security fix red-to-green:** `finalizePendingSynthetic()` now rechecks owner identity **before** remote finalize after async digest computation and **after** the server ACK; negative test revokes the owner at exactly the successful server ACK and proves the local caller returns `owner_session_changed`, not an authorized old-owner session. The server may have committed its pending revision before that revocation: this security check cannot undo committed remote state and never claims cross-system transaction atomicity.

**Boundary:** This suite runs on synthetic JavaScript modules only, not on a real hosted browser patient vault. No Neon QA migration, no Vercel deploy, no real user, no clinical vault activation, no independent cryptographic security certification. Web clinical vault remains fail-closed; D9 hosted FUE still NOT_RUN. **Sublot synthetic security CI GREEN, W02/D10 product NO-GO, D9 OPEN.**

**Next exact:** audit W01 hosted G1–G7 and encrypted Web storage/key custody + QA migration authorization, then execute D9 authenticated hosted A→B→A/new-device FUE, review and closeout before D10 product closure.
