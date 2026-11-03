# IAMINA B / D10 — Préflight parallèle Web 2026-11-03

Base main@6adf3fbeecb0f6645f9c7a9e3934177ef9eca6c7. D18 continues separately as owner of the encrypted IndexedDB/SQLite Web vault and migration. Do NOT duplicate the crypto stack or activate the optional lock before D18 security acceptance.

Added two synthetic Flutter safety tests only: (1) the patient logs out while a fresh WebAuthn-like opt-out verification is pending; the late assertion must reject, no owner skip preference written, lock remains closed; (2) fresh anonymous session cannot opt out without verified owner scope.

No runtime change, no privacy/clinical release. Existing AppLockService already has per-owner opt-out and remote recovery, but that is not proof of the encrypted patient Web vault or trusted preferences. **Risk requiring security review**: owner choice is stored as a local preference. Tampered browser profile, invalidated credentials and old protected-state markers require independent anti-forgery and D18 owner/key binding evidence. Never implement a blind isUnlocked=true workaround.

Static source assertions only: **Flutter tests/Chrome/WebAuthn hardware were NOT run**. This commit is deliberately unreferenced (no branch update, PR, CI or Vercel) to prevent automated deployment without explicit authorization.

Next: execute targeted Flutter tests in a trusted runner, record A→logout→B→A and device/offline browser QA, sign off D18-dependent Web vault guarantees and independent security/privacy.
