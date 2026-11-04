# 04/11/2026 — D10 Web / Option B — état vérifié après CI (prioritaire sur historique ci-dessous)

**Goal :** verrouillage secondaire facultatif par propriétaire sans déverrouillage différé après logout/changement de compte ni réduction de la protection des données médicales locales.

**Périmètre et statut :** [PR #1246](https://github.com/hraaaaf/IAMINA-MVP/pull/1246) OPEN / DRAFT. Branche `test/iamina-b-d10-lock-race-20261103`. Dernier code testé `e0d79d20551a2660feebf2455c80436b35ca9aa7`. Cette PR contient un préflight sécurité des transitions asynchrones `AppLockService` (unlock, configure, disable/enable, opt-out), **pas** la preuve de chiffrement/recovery du coffre Web D18 et **pas** l'activation clinique de l'option B.

**Preuves exact code HEAD :**
- [TD-014 local app-lock #41843496395](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41843496395) : COMPLETED/SUCCESS ; 65/65 tests ciblés PASS, étape de navigateur réel synthétique WebAuthn/offline PASS, build et capture BEFORE/AFTER terminés ; artefact #13329599375. Ce n'est pas un essai sur profil patient réel ni une certification de chiffrement.
- [CI générale #41843496122](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41843496122) : COMPLETED/SUCCESS ; frontend 976 PASS, **7 SKIPPED** explicitement non assimilés à coverage, backend/PostgreSQL jobs SUCCESS et build PWA SUCCESS.
- [P5-5 #41843496225](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41843496225) : COMPLETED/SUCCESS, banc synthétique; artefact #13330535554. Le passage de workflow ne certifie pas les tests physiques ni la sécurité clinique.

**Audit de conclusion :** les 3 runs sont verts sur le code `e0d79d20551a2660feebf2455c80436b35ca9aa7`. Cela prouve la conformité aux assertions exécutées, **pas** une validation sécurité/privacy indépendante. [#968](https://github.com/hraaaaf/IAMINA-MVP/issues/968) et [#1054](https://github.com/hraaaaf/IAMINA-MVP/issues/1054) demeurent OPEN ; la préférence localement persistée n'est pas un justificatif cryptographique d'autorisation. Le chiffrement/clé liée au patient et à l'appareil, les essais intégrés A→B→A/reload/offline/tamper, et l'avis expert sont toujours nécessaires. Ne pas confondre cette décision avec le lot D18.

**Décision de release :** NO-GO tant que D18 et la revue sécurité/privacy ne démontrent pas les garanties requises. Aucune fusion ni déploiement Vercel autorisé ou effectué pour ce préflight. Aucun patient réel.

**Next exact :** revue sécurité indépendante du changement `AppLockService` et du modèle d'identité ; compléter les preuves coffre D18, puis tests browser E2E synthétiques A→logout→B→A/offline/reload, certif exact-HEAD ; seulement après GO explicite, prévoir merge/post-merge et Preview autorisée. Documentation = commit séparé du code testé, ne pas déclarer la CI exacte du nouveau HEAD documentaire sans la contrôler.

---

# IAMINA B / D10 — Préflight parallèle Web 2026-11-03

Base main@6adf3fbeecb0f6645f9c7a9e3934177ef9eca6c7. D18 continues separately as owner of the encrypted IndexedDB/SQLite Web vault and migration. Do NOT duplicate the crypto stack or activate the optional lock before D18 security acceptance.

Added two synthetic Flutter safety tests only: (1) the patient logs out while a fresh WebAuthn-like opt-out verification is pending; the late assertion must reject, no owner skip preference written, lock remains closed; (2) fresh anonymous session cannot opt out without verified owner scope.

No runtime change, no privacy/clinical release. Existing AppLockService already has per-owner opt-out and remote recovery, but that is not proof of the encrypted patient Web vault or trusted preferences. **Risk requiring security review**: owner choice is stored as a local preference. Tampered browser profile, invalidated credentials and old protected-state markers require independent anti-forgery and D18 owner/key binding evidence. Never implement a blind isUnlocked=true workaround.

Static source assertions only: **Flutter tests/Chrome/WebAuthn hardware were NOT run**. This commit is deliberately unreferenced (no branch update, PR, CI or Vercel) to prevent automated deployment without explicit authorization.

Next: execute targeted Flutter tests in a trusted runner, record A→logout→B→A and device/offline browser QA, sign off D18-dependent Web vault guarantees and independent security/privacy.
