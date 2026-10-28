# IAMINA W02/D10 — staging W01-compatible, 28 octobre 2026

## Goal
Certifier sur Preview (pas Production) l'ancre serveur Option A en respectant le schéma W01/D2. Périmètre d'abord CI isolée PostgreSQL 16 + Chrome, ensuite Preview exacte, uniquement lecture tant que Neon indépendant n'est pas disponible.

## Préparation
Base Git W01/D2 `84ac2ccc30957be00b29c9b4445406310dd92668` ; composants synthétiques W02 `86738a4d06e4bd09f45fafd1c56ec56fbb611300` copiés sans écraser le BFF, l'AuthService, les routes ou les composants UI W01. Migration W02 devient `core.0024_w02_vault_revision_anchor` dépendant de `0023_d2_in_app_notice`, et non la `0020` divergente. Le garde patient `encrypted_web_patient_vault_unavailable` reste inchangé.

**Blocage externe :** Neon `noisy-truth-00115950` refuse une branche dédiée supplémentaire (`branches limit exceeded`). Ne pas effacer de branche existante, toucher à Production ou appliquer de migration sur le parent synthetic-only partagé sans vérification et autorisation appropriée. W02 REST Preview reste OFF par défaut. Cette branche est créée pour permettre le build/health/deny E2E sans patient ni écriture réelle.

## Critère de succès
Tests CI Python PG et Flutter Chrome exact-SHA ; Vercel two-project Preview READY ; vérification identité SQL sur base indépendante avant tout test d'écriture ; tests A→B→A, antirollback, cleanup et SQL zéro ; audit sécurité indépendant avant GO patient. Ne pas prétendre complet sans preuve. Fichier canonique de reprise.
