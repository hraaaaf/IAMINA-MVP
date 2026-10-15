# ADR-W01-01 — Deux projets Vercel, API Django, PostgreSQL Neon et frontière local-first Web
> **Statut : PROPOSÉ / CONTRAT DE CONCEPTION, non mise en production ni approbation données patients.** 2026-10-15, base auditée `main@2281f1c6d8138c53d8b76cd25d459781cf376b99`. Pilotage et avancement : [roadmap unique](../ROADMAP.md), W01 ; [audit W00](../assessments/2026-10-15-w00-web-inventory.md). Ne pas remplacer les contrats existants avant preuve et gate humain.

## Goal / succès / preuve
**Goal :** définir la cible IAMINA Web-only, avec un frontend Flutter Web/PWA dans un projet Vercel, une API Django/django-ninja dans un second, une base PostgreSQL hébergée chez Neon **hors Vercel**, sans compromettre le contrat patient local-first, la vie privée ou l'autorisation humaine. **Succès W01 complet :** mapping effectif des deux projets et racines ; modèle de données/identité/consentement et flux ; migrations et rollback ; build Web et API avec PostgreSQL synthétique en CI ; exercice navigateur réel Web → API → DB, panne API/offline, A→B→A, sans fuite/egress, sur commit exact ; revue sécurité/clinique adaptée. **Preuve actuelle de cette PR :** contrôle statique de configuration + tests de mutations + ADR. Pas de test distant ni de validation patient.

## As-built vérifié (ne pas le confondre avec la cible)
- Deux projets Vercel existent dans le compte connecté : `iamina-review` (ID `prj_AYaUi32KTDHak8I7dmdQpDrqd8SI`) et `iamina-certified` (ID `prj_Pn9FnyconF3h2w9gOU74iV98kJoU`). **La liste de projets ne certifie ni Root Directory actuel, ni sécurité, ni connectivité.**
- `frontend/vercel_build.sh` exige le projet review pour les builds Vercel et impose `https://iamina-certified.vercel.app` comme origine de l'API, ainsi que l'activation de l'inscription distante sur cette **surface de review**. Ce comportement est as-built, pas une politique de production patient. L'origine API et l'activation distante sont à rendre explicites par environnement avant W02/production ; tout `--dart-define` est du code visible navigateur, **jamais un secret**.
- `frontend/vercel.json` configure le build/output SPA ; `backend/vercel.json` cible `api/index.py`, WSGI Django, `maxDuration=60` et `regions=[cdg1]` ; le `vercel.json` racine cible un autre chemin frontend. **Choisir séparément les Root Directory des deux projets** ; ne pas présumer qu'une config du dossier racine est active dans le projet sous-dossier. Les trois configurations sont tenues sans auto-déploiement Git.
- Neon contient un projet `IAMINA` (ID `square-sun-82359137`), région `aws-eu-central-1`, et un projet de test distinct `iamina-925-empty-pg-test-20261015`. Inventaire Neon : une seule branche IAMINA nommée `production` ; aucune branche dev/preview observée dans le projet. Séparer tests synthétiques et périmètre production avant migrations. Cette découverte ne prouve ni le branchement exact `iamina-certified` → Neon IAMINA, ni l'isolation dev/production ; **ne pas modifier ni inspecter les données**. Vercel `cdg1` vs Neon Francfort : mesurer RTT et vérifier résidence/processeurs, ne pas changer arbitrairement.
- `backend/amina/settings.py` lit `DATABASE_URL` avec `conn_max_age=600` **en runtime générique**. Vérification W01-B : `backend/amina/wsgi.py` sélectionne **`amina.vercel_settings` si `VERCEL=1`** ; ce module exige PostgreSQL et `DEBUG=False` et **reconfigure `CONN_MAX_AGE=0`** pour les fonctions Vercel. CORS HTTPS/origins et CSRF dédiés sont également contrôlés. L'incompatibilité supposée du `conn_max_age=600` avec Vercel ne doit donc **pas** être déclarée comme défaut constaté. Reste à prouver le pooler Neon, le SSL, les connexions/transactions et le découplage pooler/direct en vraie exécution, sur DB synthétique séparée.
- `frontend/lib/data/drift/database.dart` stocke la clinique dans des coffres SQLite/IndexedDB nommés par portée patient via Drift Web. `frontend/web/iamina_service_worker.js` **désactive l'offline shell sur les hôtes review Vercel**, afin d'éviter le cache de build périmé ; tout essai offline doit explicitement choisir un environnement qui fournit le vrai service worker. WebAuthn app-lock est en place, **mais cela ne démontre pas le chiffrement du contenu clinique IndexedDB au repos**.
- `docs/LOCAL_FIRST_RUNTIME_BOUNDARY.md` : première inscription/reconnexion/lecture clinique locale sans réseau, Vercel/Neon uniquement dev/cert dans l'état actuel. Aucun changement patient-prod implicite par la présente ADR.

## Topologie proposée et trust boundaries

```text
Navigateur du patient (Flutter Web/PWA)
  ├─ UI, consentements locaux, WebAuthn UI, coffre IndexedDB patient-scoped
  │  └─ fonctions cliniques locales autorisées, offline lorsque prouvé
  └─ HTTPS fetch explicite et authentifié [optionnel/consenti, W02]
          ↓ CORS/origin/CSRF/bearer/privacy boundary
Projet Vercel API  « iamina-certified » (DEV/CERT ACTUEL)
  └─ Fonction Python WSGI Django/django-ninja, authz objet,
     consentement serveur, règles déterministes, egress contrôlé
          ↓ TLS/PostgreSQL, compte DB du backend seulement
Neon « IAMINA » (PG 16, externe à Vercel, statut actuel non patient-prod)
  ├─ branche/base DEV/CERT, données synthétiques
  └─ futures branches séparées sous gate données patient
```

**Deux projets Vercel, pas trois ; PostgreSQL n'est pas un moteur persistant « dans le second projet Vercel ».** Le frontend n'a jamais de `DATABASE_URL`, URL Neon ni privilèges SQL. L'API ne doit jamais servir depuis le projet frontend par inadvertance. Frontend CDN statique et fonctions API indépendants, domaines exacts autorisés ; pas de wildcard en production.

## Contrats obligatoires et arbitrages (sans activation)
1. **Séparation projets / CI.** Projet frontend Root Directory `frontend/`, backend Root Directory `backend/` à confirmer par configuration distante ; configs `frontend/vercel.json`, `backend/vercel.json` respectives ; aucun projet ne lit par défaut `vercel.json` racine. Contrôle statique CI de ces trois fichiers. Tout déploiement (même preview) nécessite autorisation explicite du propriétaire ; `git.deploymentEnabled=false` dans chaque manifeste, et contrôle indépendant des paramètres distants avant future activation.
2. **Auth + session W02.** L'inscription locale et le bearer distant sont séparés. Serveur Django propriétaire de son identité distante ; toute donnée synchronisée requiert consentement exprès, preuve fraîche du propriétaire, authz objet, revocation et époque de session. Menaces : XSS et extraction de token, CSRF cookie, vol d'appareil, mauvais compte, cache partagé, expiration du bearer, perte du stockage IndexedDB et restauration. Définir explicitement cookies/SameSite/CSRF/CORS versus bearer en origin séparée et prouver comportement Web.
3. **Coffre patient W02 — HUMAN GATE.** Contrat local-first existant maintenu en attendant arbitrage sécurité/données de santé. IndexedDB est local mais pas nécessairement chiffré; WebAuthn déverrouille l'interface, pas la base par magie. **Aucune promotion données réelles** sans solution de chiffrement/gestion des clés, sauvegarde/récupération et anti-cross-patient entièrement testée. Toute bascule `server-first` nécessite décision humaine explicite, migration/rollback et consentement nouvelle finalité.
4. **PostgreSQL Neon.** `DATABASE_URL` backend seul, pooled pour trafic serverless sous validation Django ; URL directe *distincte* pour migrations/backup, jamais exposée au frontend ni aux logs. Validation TLS, pool limits, connexions courtes, transactions, migrations idempotentes, restore-from-backup testée sur branche/dev synthétique et branche séparée par environnement. Ne pas exécuter `migrate` au démarrage des fonctions serverless ni sur preview contre la branche principale.
5. **Jobs CGM/OCR.** Les fonctions serverless Vercel ont durée maximale, taille bundle et état éphémère. Aucun worker permanent dans fonction HTTP. W11/W12 doivent auditer options queue/worker externe, accords fournisseurs, cadence, secret isolation, retry idempotent et coûts, **sans les présenter comme déjà installés**.
6. **Mode de panne.** 401 invalide la capacité distante seulement, jamais l'enrôlement local ; expiration, API off, Neon off, abandon requête, reconnexion et permutation A→B→A doivent conserver propriété des données, messages exacts, aucune synchronisation silencieuse vers un autre compte.
7. **Retour arrière.** Préserver dernier frontend Web sain, migrations forward/backward/backup DB évaluées indépendamment ; les artefacts Preview n'ont aucune autorité production ; en cas d'échec de migration/connexion, fonctionnalité distante fail-closed sans effacer les données locales.

## Preuves attendues avant statut COMPLET W01
| Gate | Preuve exigée | Etat dans cette PR |
|---|---|---|
| A1 manifests/root/build statiques, pas d'auto-déploiement | script stdlib CI avec scénarios négatifs | Implémenté/CI à vérifier |
| A2 projets Vercel et Neon existent | inventaire métadonnées du connecteur, sans secrets | Vérifié — existence seulement |
| A3 Root Directory + variables par environnement + connexion réelle au bon Neon | capture des paramètres non secrets, fingerprint test/branch **synthétique** | NON VÉRIFIÉ |
| A4 Django API ↔ PostgreSQL + migrations/drift rollback | CI PostgreSQL réelle et scénario requête écrit/lu synthétique, sans cloud patient | **PARTIEL : W01 CI PG16 + Django HTTP synthétique PASS ; migration/rollback du serveur distant non prouvés** |
| A5 Flutter Web réel ↔ API ↔ PG, 390/768/1280 et offline | test Chromium cross-origin avec A→B→A, auth/CORS et panne | NON VÉRIFIÉ |
| A6 coffre Web, cookies/tokens/CORS/CSRF et local-first | revue sécurité indépendante, scénarios négatifs et gate W02 | BLOQUANT W02 |
| A7 migration/réglementaire/processor + approbation de tout déploiement | gate humain avant dev preview/prod Vercel ou données patients | NON AUTORISÉ |

**Contrôle de mode applicatif (W01-B) :** `backend/amina/vercel_environment.py` n'active le mode prod IAmina que pour `VERCEL_ENV=production` **et** `IAMINA_ENV=production`. Le connecteur Vercel a montré `DEBUG=False` et l'existence de `DATABASE_URL` prod/preview, **mais pas de variable `IAMINA_ENV` déclarée** sur le projet backend. Son mode prod patient n'est donc **pas prouvé activé** ; activer sans SMTP/recovery, sécurité et W14 échouerait volontairement. Le service actuel reste dev/cert selon la frontière canonique. Frontend review compile `IAMINA_REMOTE_ACCOUNT_ENROLLMENT=true` ; ne pas promouvoir ce build comme surface patient sans gate W02. Projet Neon IAMINA : branche unique `production` non protégée, aucune branche de test isolée observée. Les deux déploiements Vercel marqués `target=production` ne portent pas le même SHA que le dernier `main`, ce qui empêche une preuve candidate Web/API cohérente.\n\n**Go/no-go pour cette PR :** accepter uniquement ADR + gardes statiques sans prétendre terminer W01. Ne pas débloquer W05/W11/W12 opérationnels avant W02 et gates ciblés.

## Références techniques officielles consultées
- [Vercel : monorepo et Root Directory](https://vercel.com/docs/monorepos)
- [Vercel : runtime Python/Django WSGI](https://vercel.com/docs/functions/runtimes/python)
- [Vercel : limites et durée des Functions](https://vercel.com/docs/functions/limitations)
- [Vercel : régions de fonctions](https://vercel.com/docs/functions/configuring-functions/region)
- [Neon : connexion PostgreSQL et pooling](https://neon.com/docs/get-started/connect-neon)
- [Neon : bonnes pratiques serverless pooled/direct](https://github.com/neondatabase/website/blob/main/content/docs/guides/serverless-connection-pooling.md)
- [Flutter : support Web](https://docs.flutter.dev/platform-integration/web)
- [Flutter : offline/service worker non généré par défaut](https://docs.flutter.dev/platform-integration/web/faq)

Dernière mise à jour documentaire : 2026-10-15. Réévaluer lorsque les configurations distantes et runtime réels seront testés.
