# IAMINA D18 Web — travaux parallèles des étapes 2 à 6

**Décision :** D18, chiffrement au repos de la totalité du coffre clinique Web par patient.  
**Date :** 2026-11-03. **Portée :** Web uniquement. **État :** préparation exécutable, **non certifiée**.

## Règle de dépendances

Le développement et la préparation de tests sont parallélisables. Les **preuves d'acceptation**, le changement du runtime patient et tout cutover clinique sont **séquentiels** et bloqués tant que le connecteur de l'étape 1 n'est pas certifié. Aucun changement de `AppDatabase.forPatientVault`, aucune donnée réelle, aucune fusion ni Vercel sans décision propriétaire.

Source de vérité étape 1 : [PR #1207](https://github.com/hraaaaf/IAMINA-MVP/pull/1207), branche `feat/iamina-d18-web-progressive-profile-20261031`. HEAD de base de cette préparation : `ccf70d008a5288f16f66c3dde3c698db19cb0987`.

## Étape 2/6 — protections runtime et concurrence (préparable en parallèle)

**Goal :** garantir qu'un seul propriétaire authentifié peut écrire un namespace physique chiffré et qu'une déconnexion ou rotation d'époque ne conserve aucun accès SQL.

**Préparation implémentée sur branche isolée :** `tools/d18_unpublished_lock_probe.js`. Test navigateur Chromium, sur namespace synthétique, demandant dix assertions : ouverture A, verrou A physiquement tenu, deuxième écrivain A refusé, ouverture concurrente lecture A refusée, ouverture indépendante B, verrou B tenu, tentative de scope/destination falsifiée refusée, verrou A libéré après terminaison, verrou B encore tenu, verrou B libéré. Fichier JS poussé, **exécution E2E pas encore effectuée** ; il faudra le raccorder à un workflow de certification une fois la CI étape 1 stabilisée. Ne pas réduire les motifs stricts de refus de l'étape 1.

**Autres preuves requises :** changement d'AuthEpoch pendant ouverture et pendant session, logout du dernier propriétaire et déconnexion d'un worker actif, différence entre verrou du nouveau chiffré et **tous les anciens writers plaintext** lors de la future migration. Les Web Locks ne prouvent pas la protection contre un script XSS du même origin.

## Étape 3/6 — migration sûre (préparable, exécution clinique interdite)

**Goal :** déplacer un coffre entier déjà attribué à un patient de `sharedIndexedDb` en clair vers une nouvelle destination `_d18_cipher_v1`, sans modifier ni supprimer la source.

**Préparer :** fixture synthétique reflétant schemaVersion=12, tables dynamiques, indexes, views, triggers, sqlite_sequence, BLOB, `PRAGMA integrity_check`, `PRAGMA foreign_key_check`, sommes de lignes et empreintes/canonicalisation par table ; comparaison source → destination chiffrée après fermeture/réouverture indépendante. Brancher un protocole journalisé/idempotent : `QUALIFIED_SOURCE → ENCRYPTED_DEST_STAGED → VERIFIED → CUTOVER_APPROVED` ; jamais d'état « approved » automatique.

**Tests négatifs :** coupure navigateur à chaque transition, destination existante, mauvaise clé, restauration sans original, deux onglets concurrents, mauvais patient, mutation de source pendant copie, stockage partiellement écrit ; source originale doit toujours être accessible après échec. Ne jamais utiliser l'export JSON partiel `LocalBackup` comme migration complète.

## Étape 4/6 — identité, récupération, restauration

**Goal :** A → logout → B → logout → A sans fuite, sans auto-unlock, sans auto-enrollment sur base existante ; récupération avec passphrase/code hors ligne, et **copie chiffrée indépendante** en cas d'effacement du navigateur.

**Préparer :** test manuel + robotisé de fermeture de worker, invalidation AuthEpoch, erreur clé B sur A et code recovery ; restauration depuis backup chiffré dans profil vierge avec intégrité byte/table et isolation ; code seul ne recrée jamais des données effacées.

## Étape 5/6 — compatibilité Safari/iPhone et sécurité du navigateur

**Goal :** preuve sur appareils réels des comportements Web Locks, IndexedDB, persistance, quota/éviction, fermeture d'onglet, arrière-plan, relance, offline, protection contre plaintext fallback.

**Préparer :** grille iPhone Safari réel + WebKit + Chrome desktop, à confirmer par versions supportées ; automatisation Playwright/WebKit ne remplace pas une vraie recette iOS. Aucune donnée patient réelle tant que chiffrement clinique non approuvé.

## Étape 6/6 — revue finale et autorisation

**Goal :** revue croisée sécurité/clinique/architecture + diff code, build WASM reproductible et SHA, origine fiable du cipher, CSP/XSS, clés JS, logs/artefacts sans secrets, gestion crash/rekey, preuve du plan retour arrière ; UI BEFORE/AFTER si impact visuel ; CI complète sur HEAD exact, vérification des validations manuelles.

**Stop conditions :** pas de certification basée sur scan d'absence de header seul, pas de confiance aveugle aux métadonnées de lease, pas de mélange de statut POC et chiffrement clinique, aucune migration/suppression de la source avant gate humain, aucun merge/deploiement Vercel sans accord explicite.

## Suivi

- Étape 1 : CI worker/SQLite/UX/WASM du commit `ccf70d00` observées vertes ; CI générale en cours au relevé initial de cette préparation, donc état **non clos**.
- Étape 2 : **test navigateur préparé mais non exécuté**, aucune certification.
- Étapes 3–6 : **contrats et tests définis**, aucune implémentation ou certification clinique revendiquée.
- **Next exact :** vérifier l'issue de la CI D18 étape 1 en parallèle ; puis raccorder et exécuter la sonde multi-onglets sur le moteur compilé. Si la CI étape 1 reste in progress, poursuivre la préparation d'injections de défaut de migration sans changer le runtime patient.
