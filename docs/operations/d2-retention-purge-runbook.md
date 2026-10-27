# D2 — Physical J+7 expiry: operational gate

Status on 27 Oct 2026: **code prepared; scheduler NOT enabled; no Production deploy**. The separate preview Web connectivity proof is already PASS; this document concerns data retention only.

## Scope and privacy
Only `core_d2inappnotice` rows, created by an explicit patient save (no push, email, SMS, auto-messaging). Saved metadata expire at `created_at + 7 days`. Reads hide expired rows immediately. Hiding does **not** equal physical deletion. There is no per-row legal-hold facility for D2, and the versioned policy now explicitly marks the D2 dataset as seven-day rolling without supported legal holds. Clinical/privacy owner must approve this choice before real use.

## Candidate architecture
**Preferred for an eventual operational scheduler:** Neon branch-scoped Function Triggers with an hourly UTC schedule and independent success/overdue monitoring. These run with scale-to-zero, unlike `pg_cron` on sleeping computes. In contrast, Vercel Cron is Production-only and is **not appropriate for the currently isolated Preview**.

No Neon Function, trigger, privileged scheduler identity, external alarm, or public deletion endpoint was deployed by this PR. Do not treat the presence of the Django command as proof of an automatic schedule. Function endpoint authentication must be reviewed; a publicly spoofable trigger header is insufficient by itself.

## Existing bounded command

The command `python manage.py purge_d2_expired_notices` is read-only by default, reports aggregated JSON metrics (counts only, no patient IDs or clinical contents), and supports:

- `--max-overdue-minutes 90`: read-only watchdog; fails with `D2_RETENTION_OVERDUE` when expired rows are more than 90 minutes old.
- `--apply --batch-size 500 --max-deletes 10000`: physical delete bounded to `expires_at <= now()`. Hard fails **before writes** if the backlog is above the cap.
- Four mandatory exact target fields on a Neon/PostgreSQL application environment: `--expected-database`, `--expected-role`, `--expected-neon-project`, and `--expected-neon-branch`. Mismatch fails before writes with `D2_RETENTION_TARGET_MISMATCH`.

The only currently authorized reference target for synthetic Preview is:
database `iamina925_empty`, role `iamina_preview_app`, project `noisy-truth-00115950`, branch `br-sweet-frog-b9ok6ptp`. **These are never Production connection details.** Never include credentials in log output or repository files.

## Proof checklist before automatic activation

1. Approve patient-facing consent copy, D2 seven-day policy, absence of legal-hold exception, backup/restore tombstone behavior and operational owner.
2. Prove scoped deletion on a disposable Neon clone with synthetic expired and unexpired rows. Must retain all unexpired rows, remove only expired ones and show independently `expired_remaining=0`.
3. Prove default dry-run never mutates; wrong DB/branch/role, bad flags and too-large backlog all fail before deletion.
4. Confirm scheduled hourly triggers are **bound to the intended Neon branch**, with a real invocation and verified zero residual, even after compute suspension.
5. Set a separately monitored watchdog threshold of 90 minutes, operator alerts, missed-run escalation and retry policy. Daily manually checked dashboards alone do not guarantee deletion.
6. Prove restore/backup behavior and no introduction of automatic message delivery.
7. Obtain explicit release authorization. No silent Preview/Production scheduler activation and no merge until gates are met.

Expected target after J+7 under an hourly scheduler: physical deletion within roughly 60 minutes, provided scheduled execution succeeds and overdue monitoring remains operational. **An exact seven-day physical deletion SLA has not been certified**.

Sources checked 27 Oct 2026:
- Neon Function Triggers: https://neon.com/blog/your-neon-functions-can-now-run-on-a-schedule
- Vercel Cron Production-only: https://vercel.com/docs/cron-jobs/quickstart

## Current evidence / limitations

The PostgreSQL A/B consent and inbox test passed 21/21 assertions inside a disposable Neon branch and rolled back to zero, and original Preview also remained at zero. The positive hosted `POST /notification-inbox/save` and browser Web account transition are **still not independently observed**. GitHub Actions OIDC protected GET remains HTTP 401, with a separate authenticated Vercel manual identity/health PASS. CI on the new retention code must be verified at its exact SHA before signoff.
