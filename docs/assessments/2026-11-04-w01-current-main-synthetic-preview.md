# IAMINA W01 — Preview synthétique sur main actuel — 04/11/2026

## Décision et périmètre

**Goal :** reproduire la version Web actuelle pour tester W01 Web → API → Neon synthétique, sans confondre la vieille branche du 17/10 avec la Production. **Succès :** builds Preview READY sur SHA runtime connu, URL API exacte embarquée, healthcheck et E2E synthétiques, identité DB et non-interférence vérifiées. **Preuves :** artefacts Vercel, réponses HTTP, logs et tests sur SHA exact. **État : NON CERTIFIÉ avant ces preuves.**

**Base GitHub vérifiée :** branche `preview/w01-current-main-synthetic-20261104` créée depuis `main@d7d650a082300486764019c8238f591057210d54` (04/11). La production Web actuellement publiée est `main@92f61c34522950c62f90c82dbcbc522c9cdd9c4a`, 2 commits derrière ce HEAD (modifications documentaires). Les protections W01 sont **déjà présentes dans main**, dans `frontend/vercel_build.sh` : contrôle ID projet, allowlist URL API Preview, `IAMINA_REMOTE_ACCOUNT_ENROLLMENT=false` et rejet de configuration manquante. `frontend/vercel.json` et `backend/vercel.json` désactivent le déploiement Git automatique. Aucun cherry-pick d'une ancienne branche nécessaire.

**API Preview** : projet `iamina-certified` `prj_Pn9FnyconF3h2w9gOU74iV98kJoU`, déploiement `dpl_5o2Fkjq5sp39nTKk6hkMdxjo16bG`, `https://iamina-certified-96wlik6wo-achraf-benmoussa-s-projects.vercel.app`, Git SHA `d7d650a082300486764019c8238f591057210d54`, target Preview (non Production).

**Web Preview** : projet `iamina-review` `prj_AYaUi32KTDHak8I7dmdQpDrqd8SI`, déploiement `dpl_FvycJYz9iNLRPmA6Wy1LWJDabRtS`, `https://iamina-review-32d3hrble-achraf-benmoussa-s-projects.vercel.app`, même Git SHA, target Preview. Variable `IAMINA_REVIEW_PREVIEW_API_BASE_URL` branch-scoped uniquement sur `preview/w01-current-main-synthetic-20261104` et fixée sur l'URL exacte API ci-dessus (Vercel env ID `JE9CVjqNmNIC75HI`).

**Garde-fous :** GO utilisateur pour Preview uniquement, aucune modification Neon Production, aucun déploiement Production, aucun patient, aucun merge. La branche de déploiement et la branche de documentation peuvent diverger après ce fichier : la certification doit viser **le SHA réellement déployé** `d7d650a...`, pas la tête documentaire.

## Tests à effectuer

- [ ] Vercel Web et API READY ; inspecter les logs de compilation.
- [ ] HTTP API Preview `/api/v1/health` = 200 et `db=ok` ; cache documenté sans extrapolation.
- [ ] HTTP Web Preview = shell Flutter ; bundle contient **uniquement** l'URL API Preview autorisée.
- [ ] Browser E2E synthétique, SSO/bypass CI contrôlé, API/DB fingerprint non secret = Neon sandbox.
- [ ] API rejette accès non autorisés (401/403), CORS/CSRF, résilience panne.
- [ ] 39 tables métier synthétiques restent à zéro en fin de test ; aucune requête/mutation Production.
- [ ] G6 restauration distante isolée, G2 protection Production, G7 revue/CI et closeout.

**Verdict :** W01 NO-GO jusqu'à preuves complètes.
## W01 — Correctif connexion A/B, 04/11/2026 — CANDIDAT NON DÉPLOYÉ

**BEFORE observé sur iPhone Safari :** écran d'activation locale sans entrée compte. Cause : `IAMINA_REMOTE_ACCOUNT_ENROLLMENT=false` dans Web Preview bloquait aussi le choix de connexion.

**Goal :** permettre le login des deux comptes synthétiques existants via API Preview, sans autoriser leur création, sans changer Production ni l'isolation local-first.

**Implémentation candidate :** nouveau flag `IAMINA_REMOTE_ACCOUNT_SIGN_IN=true` sur Preview et Production, mais Preview conserve `IAMINA_REMOTE_ACCOUNT_ENROLLMENT=false`. La séparation conserve le comportement Production antérieur. Le point d'entrée local affiche « Se connecter avec un compte existant » en Preview ; écrans FR/AR masquent inscription, démo et réinitialisation de mot de passe en mode synthétique. `AuthService.registerWithEmail` refuse toujours l'inscription sur ce build. Le flag historique `IAMINA_REMOTE_ACCOUNT_LOGIN_ENABLED` qui forcerait le même domaine Web pour les appels Chopper n'est **pas activé** : les deux projets Vercel Web/API ont des domaines distincts.

**Succès requis / Proof non acquise :** CI exécutée sur HEAD candidat (3 jobs applicatifs effectivement run), tests Flutter ciblés avec flags Preview, capture AFTER sur même iPhone/390/768/1280, vérification du POST /api/v1/auth/login contre **l'URL API Preview exacte**, CORS/CSRF, contrôle de l'inscription aussi au niveau API, account A/logout/B et rejet cross-patient, fingerprint Neon runtime et non-interférence Production, revue indépendante. **Aucun nouveau déploiement Vercel ni merge autorisé par la modification de code : Preview requiert un GO de déploiement distinct.** W01 demeure NON CERTIFIÉ.

### W01 — garde serveur contre inscription directe en Preview (candidat non déployé)

Audit adversarial : la limitation du formulaire et le refus `AuthService.registerWithEmail` ne suffisent pas, car `POST /api/v1/auth/register` reste accessible directement. Correctif backend proposé sur la même branche : rejet 403 **avant toute requête ou création d'utilisateur** lorsque `VERCEL_ENV=preview` ou `IAMINA_ENV=preview`, sauf opt-in explicite serveur `IAMINA_PREVIEW_ALLOW_REGISTRATION=true` pour tests positifs distincts. En Production, comportement inchangé. Tests négatifs et non-régression ajoutés. **Pas encore prouvé sur l'API déployée** : le SHA runtime existant `d7d650a` n'inclut pas cette protection ; elle dépend d'un déploiement Preview autorisé, puis d'un HTTP 403 observé. Ne pas prétendre qu'une Preview en cours refuse déjà l'inscription.


## W01 — Validation partielle des déploiements sur SHA 53f22063 — 04/11/2026

**GO explicite** donné au déploiement Vercel Preview Web+API uniquement. **Runtime exact (les deux services) :** `53f22063677e4dfed88f2d701b2476cb2d816511`. PR Draft #1273 conservée, aucun merge ni déploiement Production.

**Preuve CI :** [GitHub Actions #41907096322](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41907096322) SUCCESS avec exécution effective des jobs `Backend — ruff + pytest`, `Backend — PostgreSQL source-of-truth` et `Frontend — analyze + tests + PWA build` (tous SUCCESS, aucun de ces trois jobs SKIPPED). Les autres workflows du SHA étaient terminés SUCCESS à la vérification.

**Déploiements finaux Preview :**
- API `iamina-certified` `dpl_9ryTimFJ6JwsfbW66NXno2gWYcZB` : **READY**, `https://iamina-certified-hmmwtj2iu-achraf-benmoussa-s-projects.vercel.app`. GET `/api/v1/health` = **HTTP 200** avec JSON `status=ok`, `db=ok`, `cache=unavailable`. `db=ok` n'est pas un fingerprint Neon.
- Web `iamina-review` `dpl_A9uyN2wAcc1joMBVBLzv2xeM2GDo` : **READY**, URL immuable `https://iamina-review-i9gfvhyzj-achraf-benmoussa-s-projects.vercel.app`; **URL recommandée pour le test navigateur**, alias de branche stable `https://iamina-review-git-preview-w0-f972e4-achraf-benmoussa-s-projects.vercel.app/`. GET Web immuable et alias = **HTTP 200**, HTML d'amorçage Flutter.
- Bundle Web `main.dart.js` sur l'alias : **HTTP 200**, 5 012 304 caractères décodés. Contient l'URL exacte de l'API finale et le texte FR « Se connecter avec un compte existant » ; ne contient ni l'URL API précédente `iamina-certified-3gqy8a21h` ni l'alias stable `https://iamina-certified.vercel.app`. Preuve de compilation seulement : pas une capture écran ni preuve de clic/login.
- Paramètre Web `IAMINA_REVIEW_PREVIEW_API_BASE_URL` ID `JE9CVjqNmNIC75HI` limité à la branche W01 et pointé sur l'API finale.
- Corrections API CORS/CSRF limitées à Preview branche W01 : `CORS_ALLOWED_ORIGINS` ID `7M70as7ulBORDTvY`, `CSRF_TRUSTED_ORIGINS` ID `9kdr7qm4PtxA61AX`; elles autorisent l'alias Web stable de branche et la **première** URL immuable Web `iamina-review-4985w4l2f`, mais **pas** la nouvelle URL immuable `iamina-review-i9gfvhyzj`. Pour tout E2E navigateur, impérativement utiliser l'alias stable ; ne pas déclarer que CORS/CSRF fonctionnent sans mesure navigateur.

**Neon, lecture seule :** projet sandbox `noisy-truth-00115950`, branche `br-sweet-frog-b9ok6ptp`, deux comptes `w01-a@example.invalid` ID 15 et `w01-b@example.invalid` ID 16 (existence vérifiée ; mots de passe non vérifiés). Avant/après les vérifications HTTP : `auth_user=2`, `core_basepatientprofile=2`, `core_observabilityevent=66`, `core_authabusebucket=69`. Ces quatre compteurs n'ont pas varié, mais le critère « 39 tables métier à zéro » reste non prouvé et incorrect sans baseline exacte ; la base n'est pas vide.

**Production :** dernières entrées de déploiement Vercel Production inchangées (Web `dpl_CkvF3r9mUMvZe6Mpwp4e5grRoZ7c` `92f61c3` ; API `dpl_9Ur3Qprx46kwGArAX4FfKHLS2cLL` `9570e4c`). Aucune mutation Production n'a été demandée.

**Tests manuels nécessaires sur l'alias stable Web :**
- [ ] Sur iPhone Safari, voir le choix « Se connecter avec un compte existant » et conserver « Continuer sans compte ».
- [ ] Choisir connexion, vérifier les champs email/mot de passe, absence des actions Inscription/Démo/Reset dans cette Preview.
- [ ] Login compte A puis logout, login compte B, vérifier séparation du coffre patient et absence de données A.
- [ ] Vérifier Network vers **l'API finale exacte**, CORS/CSRF et réponses réelles.
- [ ] Vérifier refus backend HTTP 403 à `POST /api/v1/auth/register` sans mutation, origine Web autorisée, accès non authentifié 401/403.
- [ ] Fingerprint non secret de Neon du **runtime API**, tests G2/G6/G7, revue indépendante.
- [ ] Comparer rendu AFTER vs BEFORE iPhone 390 px, tablette 768 px et desktop 1280 px ; score visuel seulement après captures.

**Verdict : W01 PARTIEL / NO-GO certification.** Déploiements et health prouvés, **E2E Web→API→Neon et isolation complète NON certifiés**. La branche de Production Neon nommée `production` avait encore `protected=false` au dernier audit read-only : G2 ouvert. Aucun nouveau déploiement, merge ou changement Production sans autorisation.

## W01 — Incident login A et correctif candidat same-origin (04/11/2026)

**BEFORE vérifié :** Safari reçoit `status=ok, db=ok, cache=unavailable` de l'API Preview (HTTP 200 log Vercel). Le Web affiche à tort « e-mail ou mot de passe incorrect » sur toute exception ; aucune trace `POST /api/v1/auth/login` dans les logs disponibles pendant les essais. Ceci n'est **pas** la preuve d'un mauvais mot de passe. Les domaines Web/API ont chacun SSO : le transport navigateur cross-origin est l'hypothèse principale, non prouvée sans Network trace.

**GOAL correctif :** faire passer les requêtes Preview `/api/v1/*` par le domaine Web stable W01, puis une fonction serveur→API immuable avec OIDC Vercel `x-vercel-trusted-oidc-idp-token` (jeton injecté côté runtime seulement) et règle Trusted Sources `Preview Web → Preview API`. **Ne jamais exposer le jeton dans Flutter, forwarder cookies navigateur, appeler Production, ou désactiver SSO.** Fonction fail-closed si projet/VERCEL_ENV/API origine/OIDC ne concordent pas ; redirects et chemins suspects refusés ; réponses limitées à 25 Mio. Cette fonction est une **exception Preview W01** à l'architecture Web statique, à soumettre à revue de sécurité indépendante G7.

**Code candidat :** `frontend/api/index.js`, `frontend/vercel.json`, `frontend/vercel_build.sh`, `frontend/test_node/w01_proxy.test.js` + CI W01 et garde statique. Premier commit `4a8c2cd8e38c5b6ac0c8a4dfb1ddd480c459824d` ; HEAD final de branche postérieur. **5 tests Node sur 5 PASS localement**, mais pas de preuve hosted et pas de CI finale au moment de cette rédaction. Les tests Node sont placés hors du répertoire des fonctions publiées.

**Gate de sécurité et d'exécution :** OIDC activé/confirmé pour Web Preview et API Trusted Sources explicitement limitée au couple projet+environnement Preview→Preview ; autorisation de déploiement Vercel Preview distincte requise avant tout déploiement. Les déploiements existants Web/API sont toujours sur runtime `53f22063`, donc **le correctif n'est pas accessible sur Safari**. Pas de Production, merge ni écriture Neon. Tests nécessaires après GO : CI finale, résultat réel `POST /api/v1/auth/login`, A/logout/B, refus cross-patient, fingerprint, G2/G6/G7. **W01 NO-GO.**


## W01 — GO OIDC + déploiement Preview de diagnostic, 04/11/2026

**Décision autorisée :** « Green » confirme le GO pour sécuriser le trajet OIDC Web Preview → API Preview et déployer **Web Preview uniquement** après la CI, sans toucher à Production, Neon Production ni merger PR #1273.

**Goal exact :** un login compte A puis B depuis Safari Web sur API/Neon strictement synthétiques. **Succès attendu :** `GET /api/v1/health` sur le **domaine Web Preview** retourne HTTP 200/DB ok via le relais, puis login A/logout/login B et isolation patient validés. **Preuves actuelles :** le relais est testé en CI, mais aucun HTTP hébergé du relais ni login réussi n'a été capturé.

**CI sur SHA code `5cf30263cf2169ef1c8b268a628a63ca7da117ab` :** 13 workflows retournés `COMPLETED/SUCCESS` à la dernière vérification, notamment [CI générale #41919533856](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41919533856) et [W01 architecture #41919533832](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41919533832). Les 3 jobs applicatifs de CI et les 2 jobs W01 ont réellement été exécutés.

**Config OIDC du Web Vercel** `prj_AYaUi32KTDHak8I7dmdQpDrqd8SI` : mise à jour `oidcTokenConfig={enabled:true,issuerMode:team}` acceptée par l'API Vercel ; SSO du site Preview encore actif. Cette préférence est **au niveau projet** et non un secret transmis au frontend ; aucun deploy Production n'a été lancé, mais ne pas qualifier cette modification de « zéro configuration projet partagée ».

**Trusted Sources API Vercel** `prj_Pn9FnyconF3h2w9gOU74iV98kJoU` : tentative d'ajouter Web IAMINA avec `from=preview → to=preview` et tentative d'initialisation minimale ont **toutes deux échoué** : `404 Deployment Protection Trusted Sources not found`. Autorisation cross-project **non établie**. Ne pas désactiver SSO, ni exposer un bypass secret au navigateur, ni appeler l'API Production. Il faut vérifier la disponibilité de Trusted Sources dans le compte Vercel/accès Security du projet, éventuellement avec assistance humaine autorisée.

**Vercel Web Preview de diagnostic :** `dpl_FbthU6wWtg6iuXwy6hdjoPbetJXq`, **READY**, target Preview, Git SHA exact `5cf30263cf2169ef1c8b268a628a63ca7da117ab`. URL immuable `https://iamina-review-477cq6obv-achraf-benmoussa-s-projects.vercel.app` ; URL Safari recommandée (alias branch) `https://iamina-review-git-preview-w0-f972e4-achraf-benmoussa-s-projects.vercel.app/`. API Preview `dpl_9ryTimFJ6JwsfbW66NXno2gWYcZB` reste READY sur `53f22063`. Aucun déploiement Production/API nouveau, aucune écriture Neon.

**Test humain minimal à faire maintenant** : ouvrir en Safari avec session SSO Vercel `https://iamina-review-git-preview-w0-f972e4-achraf-benmoussa-s-projects.vercel.app/api/v1/health` et communiquer seulement la réponse visible (200 JSON / 403 / 502 / 503 / SSO login). Aucun identifiant, cookie, jeton ou patient. Si HTTP 200 : poursuivre tests A/logout/B et empreinte Neon ; sinon diagnostiquer runtime Web puis gate Trusted Sources API. Ne pas annoncer « corrigé » en l'absence de preuve.

**Verdict : W01 NO-GO — build et CI verts mais chaîne Web→API→Neon non certifiée.** La tête documentaire ultérieure peut être différente du SHA déployé ; toujours distinguer les deux.


## W01 — Health same-origin Safari 200, logs croisés — 04/11/2026

**Goal testé :** établir si l'alias **Web Preview** peut transmettre `GET /api/v1/health` à l'API Preview protégée, sans navigateur cross-origin ni modification Production.

**Preuve humaine :** l'utilisateur a ouvert dans Safari `https://iamina-review-git-preview-w0-f972e4-achraf-benmoussa-s-projects.vercel.app/api/v1/health` et confirmé le JSON `status=ok`, `db=ok` (le cache reste `unavailable`). La provenance précise de cette URL est le lien Web same-origin fourni en test ; ceci n'est pas une authentification de patient.

**Contre-épreuve Vercel :** journal du déploiement API Preview `dpl_9ryTimFJ6JwsfbW66NXno2gWYcZB` : `2026-11-04T22:08:25.433Z GET /api/v1/health`, HTTP **200**, URL Django enregistrée `/api/v1/health?utm_source=chatgpt.com&path=health`, domaine API immuable `iamina-certified-hmmwtj2iu-achraf-benmoussa-s-projects.vercel.app`. Le paramètre `path=health` est cohérent avec le paramètre capturé par le rewrite du proxy, mais n'est pas à lui seul une preuve d'identité de la base. La recherche de logs du Web `dpl_FbthU6wWtg6iuXwy6hdjoPbetJXq` sur `/api/v1/health` ne renvoie aucune ligne de console ; un proxy sans logging n'a pas nécessairement de ligne dans cette interface.

**Déploiement audité :** Web `dpl_FbthU6wWtg6iuXwy6hdjoPbetJXq`, **READY**, SHA runtime `5cf30263cf2169ef1c8b268a628a63ca7da117ab`. API **READY**, runtime `53f22063677e4dfed88f2d701b2476cb2d816511`. Tête documentaire PR au moment du contrôle `7aa89ae65a8e7f99a339b728f9d7ecd7fa4faf4b`, Draft. CI générale précédente sur SHA runtime vert ; CI sur tête documentaire `#41921702472` SUCCESS, W01 static `#41921702400` SUCCESS ; autres workflows en cours à l'instant du contrôle, ne pas extrapoler.

**Post-login non exécuté :** aucun `POST /api/v1/auth/login` n'est visible dans les logs API ni Web de la fenêtre `2026-11-04 21:24–22:09 UTC`. Les deux comptes synthétiques A/B restent actifs en Neon sandbox, dernières connexions respectives `2026-11-01T02:19:58Z` et `2026-11-01T00:28:46Z`; pas de preuve d'un nouveau login. Contrôle read-only Neon : `auth_user=2`, `core_basepatientprofile=2`, `core_observabilityevent=66`, `core_authabusebucket=69`, identiques à la baseline précédente. Aucune mutation Neon dans ce diagnostic.

**Nuance de sécurité :** `Trusted Sources` du projet API reste non configurable via la méthode testée (`404 Deployment Protection Trusted Sources not found`), **mais cette erreur administrative n'empêche manifestement pas le GET health via le relais actuel**. Ne pas en déduire que les POST authentifiés réussissent, ni que le contrôle Production est certifié. Le `DATABASE_URL` de Preview possède un identifiant de variable distinct du `DATABASE_URL` Production, mais sa valeur est sensible/masquée ; **empreinte runtime API→branche Neon sandbox non certifiée**.

**Décision :** connectivity gate `GET health` **PASS avec preuve user + log API**, le lot W01 complet demeure **NO-GO**. **Next exact :** sur ce même alias Web, un login du seul compte **synthétique A** puis observation de l'écran (ne pas communiquer mot de passe, cookies ou jetons). Si refus, corréler immédiatement `POST /api/v1/auth/login` dans les logs Web et API et distinguer Django 401 / 403 SSO / 5xx / transport. Si login A réussi, faire logout puis B, isolation et vérification de la DB runtime avant toute certification.
