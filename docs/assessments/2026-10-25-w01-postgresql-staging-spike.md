# W01 — PostgreSQL document staging spike — 25/10/2026

## Goal / observable success / proof
Goal: replace the *technical* Redis staging dependency in the **synthetic-only** document preview/confirmation path with existing PostgreSQL, without adding Upstash.
Success: tests prove scoped access, 3600-second **logical** TTL, single confirmation, transaction rollback, staged-row deletion, user cascade, and refusal to activate outside DEBUG.
Proof: `backend/diabetes/tests/test_w01_postgres_pending.py` plus GitHub PostgreSQL/backend CI on this isolated branch; the tests are necessary but not sufficient for a hosted GO.

## Privacy and retention hold — NO PATIENT DATA
The staging row contains extracted values, clinical notes, evidence and medication details. The full extracted `raw_text` is dropped before staging, but remaining fields **are still PHI**. Deleting rows after an hour does **NOT** delete old PostgreSQL WAL, snapshots, PITR restore points, or copies. A database TTL is a *logical access restriction*, not physically proven erasure within an hour. Neon sandbox currently retains 6 h history. No acceptable one-hour *destructive* retention mechanism for PHI backups is proven here. **Human privacy/security gate before enabling in Preview with anything other than controlled synthetic data or ever in Production.**

## Design
A Django model with patient ForeignKey CASCADE and UUID batch primary key; `expires_at` indexed. `stage_pending()` persists a redacted structured `PulperOutput`; `confirm_once()` uses `SELECT FOR UPDATE` and one surrounding SQL transaction for both persist and batch removal; `purge_patient()` removes only that user's rows. `prune_expired()` is opportunistic, **not** guaranteed 1h physical cleanup. A background sweeper/DB retention and cryptographic-erasure design would require another review, not assumed.

Integration is opt-in `W01_PG_PENDING_SYNTHETIC_ONLY=True` and **requires `DEBUG=True` plus an active pytest test case**. It is **explicitly denied whenever `VERCEL=1` or `VERCEL_ENV` targets development/preview/production**, even if DEBUG and the flag are mistakenly enabled. The API ingest route refuses the misconfigured flag **before upload read or AI/extraction egress**. These flags are a *safety fence*, **not evidence that a user/content is synthetic**. No Vercel activation is allowed without a new privacy/security design. Normal Redis path remains default, with the same fail-closed safety behavior. No migrations on Neon; no Vercel deploy; no client/PWA UI changes.

## Risks / outstanding gates
1. Proven PHI deletion or crypto-erasure across physical backups and restores (or approve an independent ephemeral store with explicit retention contract).
2. Race test on real PostgreSQL concurrent connections: the synthetic CI now requires observing the second SELECT FOR UPDATE while the first worker holds the row lock, and that worker must remain blocked before release. This tests transactional exclusion, but independent security review and real hosted tests remain necessary.
3. Test a nonempty synthetic restore on isolated Neon branch only under explicit permission.
4. SQL load/cost review, error and outage behavior, migration rollback, authorization correctness, distinct browsers, and independent security review.
5. Once accepted, only then integrate under W01 and run hosted A→B→A + normal account erasure and same-SHA CI. W01 release remains NO-GO; W03 stays paused.
