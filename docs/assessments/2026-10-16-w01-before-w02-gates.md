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
| W01-G1 | Deux projets Vercel séparés, `iamina-review` root `frontend/` et `iamina-certified` root `backend/`, branches Git et auto-deploy contrôlés | Paramètres projet effectifs, non secrets, inspectés/capturés avec IDs et commit | **PARTIEL :** intégration GitHub du dépôt exact confirmée pour les deux projets Vercel, 2 domaines vérifiés, mais Root Directory et branche Git de production effective restent NON OBSERVABLES via `get_project`; builds READY sans candidate alignée |
| W01-G2 | Neon prod vs preview/dev **physiquement isolés**, projet/branche/DB identifiés, branche prod protégée, droits/réseau revus | Métadonnées Neon, fingerprints non sensibles, preuve de non-interférence avec fixtures synthétiques | **BLOQUÉ :** IAMINA une seule branche `production` non protégée ; projet Neon synthétique séparé existe, **42 tables publiques détectées en lecture seule** sur sa DB `iamina925_empty` au 16/10 (le nom 'empty' ne certifie pas sa vacuité) ; contenu/non-interférence et raccordement Vercel→test non prouvés, ne pas migrer sans validation de l'état sandbox |
| W01-G3 | Mappings secrets par environnement : base API uniquement, pas de SQL frontend ; `IAMINA_ENV`/CORS/CSRF/TLS/pooler cohérents avec la cible | Liste non secrète de clés, contrôle de config, preuve du mode preview et distinctions prod (jamais la DSN/log de clés) | **PARTIEL avec écart bloquant :** `DATABASE_URL` prod/preview séparément déclarées côté API (fingerprints inconnus), aucune variable Web renvoyée, `IAMINA_ENV` ABSENTE de l'inventaire des clés Vercel. En son absence, le code utilise `development` même si `VERCEL_ENV=production` ; runtime réel non prouvé |
| W01-G4 | Deux artefacts Web/API correspondant à une candidate compatible ; service Django en environnement isolé utilise vraiment Neon de test | IDs de déploiement, SHA Git des artefacts, probe sans patient vers base synthétique avec identification environnement et résultat contrôlé | **NON VÉRIFIÉ :** builds Vercel observés issus de deux SHA anciens ; Chrome→Django→PG16 localhost PASS seulement |
| W01-G5 | E2E Web sur les deux projets réellement hébergés, HTTPS/CORS/CSRF/401/panne API avec données exclusivement synthétiques ; tests navigateurs multi-viewport sur l'interface si impact UI | Run reproductible, traces assainies et captures Chrome si visuel, origine exacte front/backend | **NON VÉRIFIÉ à distance.** Aucun déploiement préemptif autorisé |
| W01-G6 | Migrations/reversibilité et sauvegarde/restauration exercées **sur test isolé** ; aucune opération sur branche IAMINA production | CI + preuve de restauration et rollback/détection de dérive + absence de fuite | **PARTIEL VALIDÉ LOCAL** : [#1106](https://github.com/hraaaaf/IAMINA-MVP/pull/1106), CI prémerge PostgreSQL16 [#38926248888](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38926248888) SUCCESS, dump/restore/migration-check/rollback transactionnel jetable ; **Neon distant reste NON PROUVÉ**. Migration Django locale 0034 réelle inversée/réappliquée sur base restaurée via [PR #1109](https://github.com/hraaaaf/IAMINA-MVP/pull/1109), fusionnée `main@d533b68d55d6e0804f3820e7736802b64bc8b638` ; [W01 #38932909084](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38932909084), [migrations #38932909073](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38932909073), [générale #38932909231](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38932909231) SUCCESS sur HEAD exact `c2940ee1fbb1fa166dee325aeb400d1e8502b4fd`. Preuve logs : 0035→0033→0035, cinq colonnes contrôlées, base source et canari intacts ; CI postmerge sur SHA fusionné : [W01 #38933438458](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38933438458), [générale #38933438326](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38933438326), [migration #38933438330](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38933438330) **SUCCESS**. CI postmerge [#38926794725](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38926794725) W01, [#38926794793](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38926794793) générale et [#38926794826](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38926794826) migrations **SUCCESS** sur SHA fusionné |
| W01-G7 | Validation reproductible, garde anti-déploiement, source + CI pré/postmerge exact SHA + mise à jour Notion et roadmap de clôture | Code/paramètres non secrets + tests + liens run + merge/postmerge + documents canoniques cohérents | **EN COURS** ; interdiction de déclarer W01 CLOSED en avance |

[Preuve HTTP distante non intrusive](2026-10-16-w01-hosted-readonly-smoke.md) : `iamina-review.vercel.app/` 200, `iamina-certified.vercel.app/api/v1/health` 200 (`db=ok`) mais preview API indépendante à chemin santé attendu 404 ; aucune identité Neon validée. **G4/G5 restent NON PROUVÉS.**

[Inspection des paramètres Vercel 16/10/2026](2026-10-16-w01-hosted-readonly-smoke.md#inspection-vercel-connectée-du-16102026-g1g3-lecture-seule) : GitHub link des deux projets OUI, Root Directory/branche production NON EXPOSÉES, `IAMINA_ENV` non déclarée, aucun déploiement/Neon modifié.

**Nouveau test en cours, W01-G6 local seulement :** sur la base PostgreSQL 16 *restaurée et jetable*, Django migre réellement le schéma `diabetes 0035 → 0033 → 0035`. Avant retour arrière, refus si la sandbox contient une seule ligne de profil/journal ; preuves exigées : cinq colonnes de la migration 0034 retirées puis recréées, source intacte et canari fictif conservé. CI sur SHA PR à confirmer. Aucun accès à Neon. 

**Ne pas substituer** un test navigateur de deux coffres locaux (W02) à un test Vercel→Neon réel (W01).

## Chemin critique / blocages humains réels

1. **Lecture W01-G1 et G3 :** inspecter paramètres Vercel `Root Directory`, branche Git de prod et correspondance des environnements, sans changer de secret ni déployer. L'API connectée n'expose pas la Root Directory effective ; une capture dashboard ou un accès compatible est indispensable.
2. **Isolement W01-G2 :** définir/configurer des ressources **sans données patient** preview/dev ; protection de la branche IAMINA production et paramètres réseau à arbitrer avec le propriétaire, aucune modification prod spontanée.
3. **Accès déploiement W01-G4/G5 :** un déploiement Vercel de test **nécessite une autorisation explicite** ; aucune autorisation donnée ici ne vaut permission de stage.
4. **Exécuter G4-G6** sur sandbox synthétique isolée → corriger → tests → preuves exactes.
5. **Clore G7**, puis et seulement puis reprendre W02 depuis sa PR préservée, revoir son code face à `main` et relancer ses tests.

**Maintenir production patient = NO-GO** jusqu'aux W02/W14 et à une décision de déploiement séparée.
