# W01-G6 — vraie réversibilité Django sur PG16 synthétique local

**16 octobre 2026 — scope uniquement LOCAL.** [PR #1109](https://github.com/hraaaaf/IAMINA-MVP/pull/1109) fusionnée sur `main@d533b68d55d6e0804f3820e7736802b64bc8b638`. **W01-G6 complet : NON VALIDÉ.**

## Goal et preuve observée

**Goal testé :** dans la CI GitHub avec PostgreSQL 16 Docker local et base source nommée `iamina_w01_ci`, sauvegarder le schéma Django migré, restaurer dans une autre DB jetable `iamina_w01_restore`, prouver un rollback transactionnel **et** une véritable migration Django en arrière puis en avant, sans aucune donnée patient.

**Pré-merge HEAD exact `c2940ee1fbb1fa166dee325aeb400d1e8502b4fd` :**

- [W01 PG16 #38932909084](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38932909084) **SUCCESS** : log `Unapplying diabetes.0035 ... OK`, `Unapplying diabetes.0034 ... OK`, `Applying diabetes.0034 ... OK`, `Applying diabetes.0035 ... OK`, `PASS W01-G6 disposable PG16 Django migration 0034 DOWN to 0033 and UP to 0035; source unchanged`. Cinq colonnes Django de la migration 0034 vérifiées présentes/absentes/restaurées, source inchangée et canari `W01_FAKE_DATA_ONLY` conservé.
- [Django drift #38932909073](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38932909073) **SUCCESS** et [CI générale #38932909231](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38932909231) **SUCCESS**.
- Le premier run [#38932548258](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38932548258) a échoué parce que le script cherchait le nom conventionnel `diabetes_diabetesprofile` ; le modèle utilise explicitement `db_table='diabetes_patientprofile'`. Correction vérifiée sur la CI verte finale, sans masquer la défaillance initiale.
- Les conditions bloquent l'usage hors GitHub CI, hors URL PostgreSQL locale exacte, si DB restore déjà existante, si des lignes de profil/journal apparaissent, ou si la source/schéma/canari diffère.
- **Postmerge** [W01 #38933438458](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38933438458), [migration #38933438330](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38933438330), [générale #38933438326](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38933438326)  : **tous SUCCESS** sur `main@d533b68d55d6e0804f3820e7736802b64bc8b638`, vérifiés individuellement.

## Frontière cloud actuelle

Neon IAMINA `square-sun-82359137` possède uniquement la branche `production`, non protégée au relevé en lecture seule ; aucune écriture n'y a été faite. Projet distinct de test Neon `noisy-truth-00115950`, branche `synthetic-only` : `SELECT` read-only effectué sur DB `iamina925_empty`, PG 16 (`server_version_num=160015`), **42 tables `public`** dénombrées. Le nom de la DB **ne prouve pas une base vierge** et les données n'ont pas été inspectées. Aucune restauration ni suppression ni migration n'a été tentée sur ce projet.

**Reste W01-G1–G7 :** racines/branches Git réelles Vercel, separation Neon dev/preview/prod, mappings secrets sans valeurs divulguées, déploiements synthétiques alignés, E2E Vercel→API→Neon, restauration distante et rollback applicatif. **W02 strictement GELÉ.** Aucun Vercel deploy/Neon mutation/patient.
