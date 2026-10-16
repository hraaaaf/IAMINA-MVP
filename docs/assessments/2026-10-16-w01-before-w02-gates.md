# IAMINA Web V2 — W01 avant W02 : contrat de passage

**Date : 16 octobre 2026. Décision explicite du propriétaire : ordre séquentiel strict W01 → W02.**

## Règle d'exécution

- **Chantier actif : W01 (architecture Web, API, Neon)**, toujours **EN COURS / NON CERTIFIÉ**.
- **W02 : GELÉ / NON DÉMARRABLE** jusqu'à preuve formelle que *tous* les critères propres à W01 ci-dessous sont satisfaits, revue et clôture canonique dans `docs/ROADMAP.md`, et CI postmerge verte sur le commit de clôture.
- PR W02 [#1104](https://github.com/hraaaaf/IAMINA-MVP/pull/1104) **fermée sans fusion**, branche préservée `test/w02-auth-stale-login-response-20261016`. Les travaux historiques #1097/#1101/#1102 déjà intégrés ne sont pas annulés ni présentés comme une clôture W02. Pas de nouvelle PR, correctif, benchmark ou fusion W02 entre-temps.
- **W14 et autorisation de release patient sont des gates ultérieurs**, et **ne conditionnent pas la clôture technique de W01**. Sinon W01 ne pourrait jamais précéder W02. Le mot « W01 fermé » ne signifie **jamais** « production patient autorisée ».

## Gate W01 : critères de clôture exacts

| ID | Résultat observable requis | Preuve acceptable | État au 16/10/2026 |
|---|---|---|---|
| W01-G1 | Deux projets Vercel séparés, `iamina-review` root `frontend/` et `iamina-certified` root `backend/`, branches Git et auto-deploy contrôlés | Paramètres projet effectifs, non secrets, inspectés/capturés avec IDs et commit | **NON VÉRIFIÉ :** existence + builds observés uniquement, Root Directory distante inaccessible avec la lecture connectée |
| W01-G2 | Neon prod vs preview/dev **physiquement isolés**, projet/branche/DB identifiés, branche prod protégée, droits/réseau revus | Métadonnées Neon, fingerprints non sensibles, preuve de non-interférence avec fixtures synthétiques | **BLOQUÉ :** IAMINA une seule branche `production` non protégée ; projet Neon synthétique séparé existe, pas de connexion Vercel→test prouvée |
| W01-G3 | Mappings secrets par environnement : base API uniquement, pas de SQL frontend ; `IAMINA_ENV`/CORS/CSRF/TLS/pooler cohérents avec la cible | Liste non secrète de clés, contrôle de config, preuve du mode preview et distinctions prod (jamais la DSN/log de clés) | **PARTIEL :** `DATABASE_URL` prod/preview déclarées, destinations inconnues ; `IAMINA_ENV` non observée |
| W01-G4 | Deux artefacts Web/API correspondant à une candidate compatible ; service Django en environnement isolé utilise vraiment Neon de test | IDs de déploiement, SHA Git des artefacts, probe sans patient vers base synthétique avec identification environnement et résultat contrôlé | **NON VÉRIFIÉ :** builds Vercel observés issus de deux SHA anciens ; Chrome→Django→PG16 localhost PASS seulement |
| W01-G5 | E2E Web sur les deux projets réellement hébergés, HTTPS/CORS/CSRF/401/panne API avec données exclusivement synthétiques ; tests navigateurs multi-viewport sur l'interface si impact UI | Run reproductible, traces assainies et captures Chrome si visuel, origine exacte front/backend | **NON VÉRIFIÉ à distance.** Aucun déploiement préemptif autorisé |
| W01-G6 | Migrations/reversibilité et sauvegarde/restauration exercées **sur test isolé** ; aucune opération sur branche IAMINA production | CI + preuve de restauration et rollback/détection de dérive + absence de fuite | **PARTIEL :** CI de dump/restore Django PG16 + rollback transactionnel **localhost synthétique** ajoutée, résultat CI en attente. Restent restauration Neon distante, migration inverse et rollback applicatif non prouvés |
| W01-G7 | Validation reproductible, garde anti-déploiement, source + CI pré/postmerge exact SHA + mise à jour Notion et roadmap de clôture | Code/paramètres non secrets + tests + liens run + merge/postmerge + documents canoniques cohérents | **EN COURS** ; interdiction de déclarer W01 CLOSED en avance |

**Ne pas substituer** un test navigateur de deux coffres locaux (W02) à un test Vercel→Neon réel (W01).

## Chemin critique / blocages humains réels

1. **Lecture W01-G1 et G3 :** inspecter paramètres Vercel `Root Directory`, branche Git de prod et correspondance des environnements, sans changer de secret ni déployer. L'API connectée n'expose pas la Root Directory effective ; une capture dashboard ou un accès compatible est indispensable.
2. **Isolement W01-G2 :** définir/configurer des ressources **sans données patient** preview/dev ; protection de la branche IAMINA production et paramètres réseau à arbitrer avec le propriétaire, aucune modification prod spontanée.
3. **Accès déploiement W01-G4/G5 :** un déploiement Vercel de test **nécessite une autorisation explicite** ; aucune autorisation donnée ici ne vaut permission de stage.
4. **Exécuter G4-G6** sur sandbox synthétique isolée → corriger → tests → preuves exactes.
5. **Clore G7**, puis et seulement puis reprendre W02 depuis sa PR préservée, revoir son code face à `main` et relancer ses tests.

**Maintenir production patient = NO-GO** jusqu'aux W02/W14 et à une décision de déploiement séparée.
