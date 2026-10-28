# IAMINA W02/D10 — staging W01-compatible, 28 octobre 2026

## Goal
Certifier sur Preview (pas Production) l'ancre serveur Option A en respectant le schéma W01/D2. Périmètre d'abord CI isolée PostgreSQL 16 + Chrome, ensuite Preview exacte, uniquement lecture tant que Neon indépendant n'est pas disponible.

## Préparation
Base Git W01/D2 `84ac2ccc30957be00b29c9b4445406310dd92668` ; composants synthétiques W02 `86738a4d06e4bd09f45fafd1c56ec56fbb611300` copiés sans écraser le BFF, l'AuthService, les routes ou les composants UI W01. Migration W02 devient `core.0024_w02_vault_revision_anchor` dépendant de `0023_d2_in_app_notice`, et non la `0020` divergente. Le garde patient `encrypted_web_patient_vault_unavailable` reste inchangé.

**Blocage externe :** Neon `noisy-truth-00115950` refuse une branche dédiée supplémentaire (`branches limit exceeded`). Ne pas effacer de branche existante, toucher à Production ou appliquer de migration sur le parent synthetic-only partagé sans vérification et autorisation appropriée. W02 REST Preview reste OFF par défaut. Cette branche est créée pour permettre le build/health/deny E2E sans patient ni écriture réelle.

## Critère de succès
Tests CI Python PG et Flutter Chrome exact-SHA ; Vercel two-project Preview READY ; vérification identité SQL sur base indépendante avant tout test d'écriture ; tests A→B→A, antirollback, cleanup et SQL zéro ; audit sécurité indépendant avant GO patient. Ne pas prétendre complet sans preuve. Fichier canonique de reprise.

## Sécurité vérifiée : écart W01 Web

La base W01/D2 utilisait encore `driftDatabase(web: DriftWebOptions(...))` dans `AppDatabase.forPatientVault`. Le test W02 a correctement échoué au contrat de protection. Correctif **uniquement sur staging** : helper `_w02ProtectedPatientVaultExecutor` rejette `kIsWeb` avec `encrypted_web_patient_vault_unavailable` avant création de la base patient. Chemin Native inchangé. **Attention :** `AppDatabase.defaults()` reste un chemin legacy Web pouvant créer du SQLite navigateur non chiffré. L'ensemble de l'app n'est pas certifié, et aucune donnée patient réelle ne doit passer par ce chemin. Ce staging permet uniquement preuve de build, deny et intégrations synthétiques ; pas d'activation Web patient. Go conditionné à inventaire des consommateurs de `defaults()` et suppression de tout stockage clinique plaintext.


## Deployment Preview attesté — 28/10/2026 (après code SHA 1e2a2409)

- **Code/build SHA :** `1e2a24092f7f58d690f575709e5aed1b4216c3df`, staging fork uniquement, branch `feat/w02-d10-option-a-w01-preview-20261028`. `main` / W01 integration / W02 initial non fusionnés.
- **API Vercel Preview :** `iamina-certified`, deployment `dpl_5WYwKTfkXQG6ZiUErejXHAzEoHqM`, READY, URL `https://iamina-certified-b74eac8ia-achraf-benmoussa-s-projects.vercel.app`. Protection SSO conservée. W02 flag absent → *OFF*. Aucune migration Neon.
- **Web Vercel Preview :** `iamina-review`, deployment `dpl_23hdDJqMQWmdFS8GTMEo8kLuRPnv`, READY, URL `https://iamina-review-abtkl3ybg-achraf-benmoussa-s-projects.vercel.app`. Projet et SHA exacts vérifiés. Variable `IAMINA_REVIEW_PREVIEW_API_BASE_URL` strictement limitée à cette branche Preview et à cet exact déploiement API. Aucune activation du login synthétique/inscription distante.
- **SQL cible indépendante et lecture seule :** Neon projet `noisy-truth-00115950`, branche `br-sweet-frog-b9ok6ptp`, base `iamina925_empty`, rôle `iamina_preview_app`, `auth_user=0`, `to_regclass('public.core_w02vaultrevisionanchor') IS NULL` avant/après déploiement. Aucun schéma ni compte patient modifié. Neon `create_branch` retourne `branches limit exceeded`. Ne pas supprimer/repurposer une branche Neon ancienne sans approbation.
- **CI Postgres 16 (éphémère GitHub Actions) :** [#40731783684](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40731783684) SUCCESS, 8/8 Node, 10/10 Python PostgreSQL, `makemigrations --check --dry-run` = No changes detected, `core.0024` appliquée à la DB CI seulement.
- **CI Chrome :** run [#40732061792](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40732061792) QUEUED au dernier contrôle. Un run précédent [#40731783604](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40731783604) a échoué correctement : l'ancien W01 `forPatientVault` était un chemin IndexedDB non chiffré. Correctif sur staging : `encrypted_web_patient_vault_unavailable` à l'ouverture Web de `forPatientVault` seulement. Nouvelle preuve Chrome non encore obtenue.
- **Protection restante :** `AppDatabase.defaults()` Web reste un chemin legacy non chiffré et n'est pas certifié pour données patients ; produit D10 patient **NO-GO**. Les fixtures JS et Drift WASM sont test-only. Ne pas confondre READY Vercel et E2E clinique.

**Goal atteint :** deux artefacts Preview exact-SHA compilés/READY et migration compatible vérifiée en CI, pas Production. **Goal NON atteint :** E2E Web → BFF → API → Neon sur DB indépendante avec cleanup SQL indépendant, clé et durable recovery, absence de chemin plaintext global, tests app-lock BEFORE/AFTER, audit sécurité indépendant.

**Next exact :** résoudre quota Neon via décision humaine sur archivage ou capacité ; créer branche QA neuve, vérifier quatre identifiants et les privilèges, y appliquer `core.0024` sur QA uniquement, autoriser explicitement `IAMINA_W02_REVISION_ANCHOR_ENABLED=true` uniquement sur nouvelle branche Vercel et exécuter E2E A→B→A/crash puis nettoyage SQL zéro. Si quota non résolu, poursuivre Chrome CI et code sécurité sans données patients. Aucun merge ni Production GO.
