# V1 decision #11 — no synthetic rows in real empty patient session

**BEFORE audited in issue #969**: seedOfflineDemoAuditData returns unless BOTH auditAllowed and offlineDemo are true. main.dart derives auditAllowed from AuditAccessPolicy and passes kOfflineDemo. An audit/loopback preview is not authorization to seed a patient's clinical data.

**Goal and proof plan**: exercise actual empty Drift database under 3 combinations where either auditAllowed or offlineDemo is false. Assert zero glucose logs, zero local profile and zero reminders before/after. Also lock the guard and call-site wiring with a source contract. This is synthetic negative QA only, not proof of every analytics path or a real patient's device.

**Scope**: no code path, UI, backend, medical calculation, login or cloud modified. CI exact SHA needed. Separate CGM provenance and medical display gates remain, #1 and #25 last. No merge/Vercel absent explicit permission.