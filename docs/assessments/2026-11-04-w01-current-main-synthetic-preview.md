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
