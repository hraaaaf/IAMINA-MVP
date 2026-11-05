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


## W01 — Compte A authentifié, gate d'isolation A/B — 04/11/2026

**Goal :** A login réussi puis logout vérifié, B login avec données/carte d'identité séparées, retour A prouvant le cloisonnement du coffre local et de Neon sandbox. **Succès :** preuve des deux requêtes `POST /api/v1/auth/login` HTTP 200, déconnexion A sans fuite, marqueur **synthétique A uniquement** absent de B et retrouvable après reconnexion A ; zéro accès Production.

**Preuve A — trois sources :**
- **Retour Safari utilisateur :** compte A connecté, tableau de bord affiché sur la nouvelle Web Preview W01.
- **Runtime API Preview** `dpl_9ryTimFJ6JwsfbW66NXno2gWYcZB` : `2026-11-04T22:18:38.445Z POST /api/v1/auth/login?path=auth%2Flogin` **HTTP 200**, domaine API immuable, environnement Preview. Aucun `POST login` retrouvé dans les logs Web (le relais n'écrit pas nécessairement en console).
- **Neon sandbox read-only** `noisy-truth-00115950/br-sweet-frog-b9ok6ptp/iamina925_empty` : ID 15 `w01-a@example.invalid` actif, `last_login=2026-11-04T22:18:38.367Z` ; ID 16 `w01-b@example.invalid` actif, `last_login=2026-11-01T00:28:46.744Z` inchangé. La concordance sous-seconde constitue une preuve solide que le login A sur API Preview écrit sur cette branche synthétique.

**Baseline d'isolation avant marqueur :** un `core_basepatientprofile` propre à chacun des IDs 15/16 ; `diabetes_logentry`, `core_patientmodule` et `diabetes_labreport` : **0 ligne** pour chacun. Ces absences ne prouvent pas le cloisonnement en lecture. Compteurs globaux relevés après A : `auth_user=2`, `core_basepatientprofile=2`, `core_observabilityevent=67`, `core_authabusebucket=70`; hausses +1/+1 par rapport à la précédente baseline, sans extrapolation causale non vérifiée.

**Revue logout iPhone :** `frontend/lib/features/navigation/main_shell.dart` masque la sidebar sous 700px ; mais le bouton de déconnexion **existe** dans `frontend/lib/features/profile/profile_screen_presentation.dart`, section « zone de danger », et appelle `_confirmSignOut` de `profile_screen.dart`, qui exécute `AuthService.signOut()` et retourne `/login`. La revue initiale de `profile_screen.dart` seule avait produit un faux signal « bouton absent » : **corrigé après lecture du fichier de présentation**. Aucun changement UI nécessaire. Les tests D11 de logout dans `frontend/test/features/navigation/d11_main_shell_real_logout_test.dart` couvrent 768/1280, pas l'interface iPhone réelle ; test mobile sur Safari **ouvert**.

**Étape humaine ciblée sur Safari, compte A encore ouvert :** ouvrir `+ Ajouter` puis saisir une **mesure fictive** de glycémie `112 mg/dL` (jamais donnée réelle), sauvegarder et constater la ligne dans Journal ; aller dans Profil → section « zone de danger » → Déconnexion, confirmer et vérifier le retour Login ; ouvrir B `w01-b@example.invalid`, vérifier que la ligne `112 mg/dL` A est absente et que son profil est indépendant. Bonus de preuve : se déconnecter de B et reconnecter A puis vérifier réapparition de sa mesure. Cette mesure est nécessaire car les deux comptes ont zéro journal au départ : comparer deux écrans vides **ne démontre pas** l'isolation.

**État :** login A **PASS** ; logout A, login B, prévention fuite locale et données cliniques hébergées **NON TESTÉS / NO-GO W01**. Aucun déploiement Vercel ni mutation Neon par l'agent sur cette phase ; marqueur de test éventuel uniquement avec action explicite utilisateur dans la Preview synthétique. La PR reste Draft sans merge.


## W01 — Isolation A/B Safari confirmée, Neon en lecture seule (04/11/2026)

**Décision W01 :** valider le parcours authentification, déconnexion, cloisonnement A/B et retour A en Web Preview synthétique, sans patients réels. **Succès local observable :** un marqueur glycémique **fictif 112 mg/dL** saisi dans le Journal du compte A, absent du compte B, retrouvé après retour à A sur le **même navigateur Safari**. L'utilisateur a explicitement confirmé l'exécution et la réussite des quatre étapes (ajout A, logout A, login B et absence A, logout B puis retour A avec marqueur). Cette preuve est une déclaration de test humain ; absence de captures indépendantes AFTER.

**Corroboration API déployée et journal d'événements :** API Preview `dpl_9ryTimFJ6JwsfbW66NXno2gWYcZB`, runtime exact `53f22063677e4dfed88f2d701b2476cb2d816511` :
- `2026-11-04T22:18:38.445Z POST /api/v1/auth/login?path=auth%2Flogin HTTP/1.1` **200** — connexion A corrélée au `last_login` Neon ID 15.
- `2026-11-04T22:29:32.320Z POST /api/v1/auth/logout?path=auth%2Flogout HTTP/1.1` **200** — première déconnexion (A par chronologie).
- `2026-11-04T22:30:26.624Z POST /api/v1/auth/login?path=auth%2Flogin HTTP/1.1` **200** — connexion B corrélée au `last_login` Neon ID 16.
- `2026-11-04T22:32:00.067Z POST /api/v1/auth/logout?path=auth%2Flogout HTTP/1.1` **200** — seconde déconnexion (B par chronologie).
- **Limite importante :** aucun **troisième** `POST /api/v1/auth/login` de retour à A dans les logs disponibles jusqu'à `2026-11-04T22:34:09Z`. Le nouveau login distant A n'est donc **pas** prouvé. Les réponses HTTP 200 au logout prouvent que l'endpoint a été appelé, mais ne certifient pas séparément l'invalidation de chaque ancien jeton.

**Neon synthétique, interrogation read-only :** projet `noisy-truth-00115950`, branche `br-sweet-frog-b9ok6ptp`, DB `iamina925_empty`, rôle `iamina_preview_app`.
- A `w01-a@example.invalid`, ID 15, `last_login=2026-11-04T22:18:38.367Z` (inchangé au contrôle après le test complet).
- B `w01-b@example.invalid`, ID 16, `last_login=2026-11-04T22:30:26.517Z`, cohérent à 107 ms avec le `POST /auth/login` HTTP 200.
- `core_basepatientprofile` : **1 ligne liée à A, 1 ligne liée à B**.
- `diabetes_logentry`, `diabetes_labreport`, `core_patientmodule` : **0 ligne pour A, 0 ligne pour B**. Au total : `auth_user=2`, `core_basepatientprofile=2`, `core_observabilityevent=68`, `core_authabusebucket=71`, `diabetes_logentry=0`, `diabetes_labreport=0`.
- **Conclusion cruciale :** la glycémie fictive de 112 mg/dL n'a **pas** été observée dans les tables métier serveur ; la séparation observée concerne le **coffre local IndexedDB/SQLite du navigateur**, sans preuve de synchronisation clinique ni de contrôle inter-comptes sur données métier distantes. Les profils Neon sont physiquement distincts, mais la lecture/écriture distante cross-patient reste non exercée avec données sentinelles.

**Audit du code de cloisonnement sur SHA Web runtime `5cf30263cf2169ef1c8b268a628a63ca7da117ab` :**
- `frontend/lib/data/drift/patient_vault_scope.dart` crée `amina_vault_v1_native_<userId>` ; pour A/B: `amina_vault_v1_native_15` et `amina_vault_v1_native_16`.
- `AppDatabase.forPatientVault(scope)` ouvre un stockage physique séparé par portée, sans reprendre le stockage legacy non scopé.
- `AuthService.signOut` supprime immédiatement le bearer et l'identifiant de compte locaux et change l'époque de session avant toute attente réseau, puis tente `POST /auth/logout`. Les tests `frontend/test/services/patient_vault_session_controller_test.dart` couvrent explicitement A→B→A et sentinelle glycémique locale ; `auth_service_local_first_test.dart` couvre sign-out et l'absence de restauration d'ancienne identité. Ces tests sont des preuves de code/suite, distinctes de Safari.

**Verdict par critère :** **A login PASS (API+Neon)** ; **A logout API 200 PASS** ; **B login PASS (API+Neon)** ; **B logout API 200 PASS** ; **local vault A/B/A isolation PASS selon retour Safari + code/test** ; **re-auth finale A non prouvée par logs** ; **révocation bearer réelle et clinique distante cross-patient non certifiées**. W01 dans son ensemble demeure **PARTIEL / NO-GO** au regard des gates de sécurité/restauration/revue G2/G6/G7 ouverts. Aucun nouveau déploiement Vercel ni écriture Neon par l'agent.

**Next exact :** confirmer par preuve traçable la troisième authentification A seulement si nécessaire à la certification session complète ; tester l'ancienne crédentialité après logout et l'isolement métier serveur au moyen de scénarios synthétiques autorisés sans toucher à Production ; revue G2/G6/G7 et closeout documentaires avant verdict GO global. Toute modification de code nécessitant une nouvelle Preview requiert un nouveau GO Vercel.


## W01 — GO sécurité, G2 Neon quota et fix de révocation en PR (04/11/2026)

**GO accordé :** utilisateur « Greeeen », limité au durcissement G2 et poursuite des preuves W01 ; nouveau déploiement Vercel non autorisé.

**G2 Neon Production tentée :** `square-sun-82359137/br-fragrant-frost-b1lbdfzs`, branche `production`, `default=true`, `protected=false`. L'appel officiel `update_branch(protected=true)` retourne **HTTP 422** « maximum number of protected branches for your current plan ». Liste des branches du projet : **1 seule**, production. **État non corrigé**, aucune donnée Production, autre branche ou protection touchée. Gate externe réel : résoudre limite Neon (forfait/support) avant certification G2.

**Bug sécurité déterministe découvert dans le runtime déployé :** malgré les `POST /auth/logout` 200 de A et B observés dans les logs API, `SELECT patient_id,auth_token_version FROM core_basepatientprofile` sur Neon **sandbox** renvoie **(15,0), (16,0)**. Sur le Web Preview, `frontend/api/index.js` relaie `Authorization` sans cookie ; la route publique `backend/core/api/v1/auth.py::logout_native` ne révoquait que lorsque `request.user` Django était déjà authentifié par cookie. Ainsi les déconnexions no-op répondaient 200 sans invalider le Bearer. **G2 sécurité sessions : FAIL sur le déployé**, indépendamment de la réussite UI.

**Correctif candidat non déployé :** pour la route publique logout uniquement, l'API vérifie le Bearer IAMINA signé dans `Authorization`, refuse les jetons invalides et identités cookie/bearer divergentes avec HTTP 401, puis révoque tous les jetons du propriétaire authentifié via `auth_token_version`. Le cookie-only Django historique reste géré. Pas de contournement Vercel OIDC ni transfert de cookies au proxy.

**Preuve cible commit :** nouveau test `backend/core/tests/test_w01_native_logout_http.py`, exécuté dans le job **W01 synthetic Django HTTP to PostgreSQL** du workflow `.github/workflows/w01-web-topology-contract.yml` : A et B utilisent de vrais `POST /auth/login`, requêtes `Authorization: Bearer` sans cookie, données synthétiques distinctes, GET/PATCH/DELETE cross-patient doivent renvoyer 404, logout A doit incrémenter sa seule version et refuser l'ancien Bearer par 401, B demeure actif, reconnexion A, puis logout B, et cas tampered/cookie conflict/cookie-only. **Statut : CANDIDAT — ne pas déclarer pass sans CI réelle**.

**Non-objectif :** aucune nouvelle Preview API/Web déployée dans ce lot, aucun merge, aucune écriture de données cliniques Production ou de Neon sandbox par l'agent. Tant que l'API actuelle est en place, l'ancienne faille de révocation subsiste. **Next exact :** CI W01 + tests backend de sécurité, correction si échec, preuve en Preview hébergée seulement après GO explicite Vercel, G2 toujours bloqué par forfait, puis G6/G7.


### W01 CI — première tentative du fix de révocation : échec détecté, correction diagnostique en cours (04/11/2026)

L'exécution [W01 #41938115595](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41938115595) a terminé avec **w01-static SUCCESS** mais **PostgreSQL HTTP FAILURE** : nouveau test retourne 401 pour le Bearer **avant** la déconnexion, et la fixture B n'avait pas encore créé son `BasePatientProfile`. Le code API correctif ne peut donc **pas** être considéré testé ou certifié. Une mise à jour du test au commit `31f566233cb1168e67d9d9045e1d47d46d7404db` vérifie que le jeton signé est localement valide, que `HTTP_AUTHORIZATION` arrive dans le request WSGI, affiche seulement le corps de la réponse anonyme en cas d'échec, et crée explicitement le profil B synthétique. La configuration W01 `pull_request.paths` inclut maintenant le fichier auth et ce test pour déclencher une CI de sécurité sur toutes futures modifications liées à ce problème. **Ne pas confondre preuve d'un test rouge, diagnostic, et résolution runtime.** Next : CI ciblée puis correction selon motif de 401, re-test PostgreSQL réel, aucun déploiement Vercel.


### W01 — PG16 routeur HTTP : preuve et correction de portée limitée (05/11/2026)

Le diagnostic [W01 #41939841962](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41939841962) est **FAILURE** sur l'assertion d'appel du bearer ; tests statiques SUCCESS. L'authentificateur `HybridBearerAuth` est valide en direct, l'en-tête est présent, mais la route Django résolue est bien `api/v1/logs → list_logs` et les opérations du `logs_router` affichent `auth_callbacks=[]` pour les GET/POST/PATCH/DELETE. Le vrai HTTP retourne 401 sans appeler `HybridBearerAuth.authenticate`. Preuve ciblée d'un problème d'attachement des callbacks au routeur clinique, indépendamment du ticket de révocation du logout.

**Candidat minimal :** expliciter `auth=[firebase_auth_backend, SessionAuth()]` dans `backend/diabetes/api/v1/logs.py::Router(...)` lui-même, en conservant l'auth de montage existante dans `diabetes/api/main.py`. Ceci ne rend aucun endpoint public et ne change pas la validation du jeton ni la politique CSRF. Retrait des sondes de diagnostic du test HTTP W01, conservant les assertions requises : Bearer valide A/B sans cookie → 200, séparation de lecture/écriture cross-patient, logout révoque version et ancien bearer → 401, ancien cookie conflict → 401, re-login A valide. **PAS CERTIFIÉ tant que la nouvelle CI PG16 n'est pas verte.** Pas de déploiement Vercel dans cette action.


### W01 — Routage Journal monté deux fois, auth explicite par opération (05/11/2026)

L’essai [W01 #41940238242](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41940238242) est **FAILURE HTTP PostgreSQL** sur `GET /api/v1/logs` retournant 401 malgré jeton natif valide et auth du Router déclarée. Le registre P3 `diabetes/apps.py` monte le **même objet** `logs_router` sur `/v1/logs` et `/v1/diabetes/logs`, cause possible d'auth héritée masquée par le second montage (hypothèse, pas encore démontrée).

**Correctif candidat plus strict :** chaque opération (GET /logs, POST /logs, POST /logs/batch, GET/PATCH/DELETE /logs/{id}) porte désormais explicitement `auth=[firebase_auth_backend,SessionAuth()]`. Test ajouté `test_w01_every_logs_operation_explicitly_requires_bearer_or_session` vérifie les 6 callbacks d'opérations, et le vrai HTTP PG16 vérifie la politique A/B et la révocation. **CI en attente**, aucun déploiement, aucun changement de données Prod/Neon.


## W01 — reprise 05/11/2026 : CI réelle rouge et diagnostic du Bearer en contexte HTTP

**État de la PR au début de reprise :** HEAD `d071af66d2bfbd04ac72a44696fee6dcc6578352`, Draft ouverte ; [W01 #41942015079](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41942015079) **FAILURE**, [CI #41942015089](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41942015089) **FAILURE**, Developer portability #41942014995 **FAILURE**. Web/API Preview déployées sur leurs anciens SHAs et non modifiées.

**Preuve ciblée échec W01 :** sur PostgreSQL16 éphémère, `test_w01_http_logout_revokes_bearer_without_cookie_and_keeps_b_private` échoue car `GET /api/v1/logs` est **401 au lieu de 200 avant le logout**. Les callback Ninja `HybridBearerAuth` et `SessionAuth` sont attachés à `/logs`, et le header `Authorization` contient un Bearer natif de format attendu. La capture précédente `W01_HTTP_AUTH_CALLBACK_OUTCOMES` indique **bearer=False** et **session=False**. L'assertion `verify_native_token(token)` effectuée dans le thread du test passe, mais la même vérification au sein du callback HTTP n'avait pas encore été isolée. **Aucune preuve de cause définitive ni de correction validée.**

**Action de diagnostic :** instrumenter dans le test synthétique les résultats du validateur natif **à l'intérieur** du callback Ninja, journaliser seulement le type d'exception ou l'ID utilisateur synthétique et la présence de résultat, sans aucun jeton/cookie/donnée clinique. Corriger aussi les 2 règles Ruff `I001` (test W01 et imports relatifs `logs.py`), sans changement de politique d'accès. Le test de protection du logout reste un gate bloquant et tout contournement consistant à supprimer l'assertion 401/200 est interdit.

**CI générale :** 6 échecs du backend dont W01 et 5 tests de gouvernance attestant `fallback.processor_identity evidence is stale` ; ces 5 erreurs sont hors de cette décision, à documenter séparément et ne pas masquer pour rendre artificiellement le run vert. Lint `I001` sur les 2 fichiers W01 est dans le périmètre. Frontend Web/PWA job SUCCESS. Aucun benchmark lourd ou déploiement Vercel n'est lancé.

**G2 Production Neon :** branche Production toujours non protégée ; protection demandée et refusée HTTP 422 (« quota protected branches ») sur organisation forfait Free. Aucun autre projet/branche/DB modifié. **W01 NO-GO** tant que révocation n'est pas certifiée et blocage G2 non résolu.


### W01 — Correctif candidat de sélection Bearer au callback HTTP (05/11/2026)

Le run [W01 #41987676848](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41987676848) a montré **HTTP PostgreSQL FAILURE** pour le premier test de sécurité, mais la preuve a progressé : `W01_HTTP_AUTH_CALLBACK_OUTCOMES=[('bearer',False,...),('session',False,...)]` avec en-tête et jeton de la fixture exacts et `W01_NATIVE_VERIFY_IN_CALLBACK=[]`. Le contrôleur `HybridBearerAuth.authenticate` n'est **jamais appelé** dans le vrai parcours HTTP en dépit de sa callback présente et du Bearer reçu. Un test direct de `verify_native_token` dans le thread principal réussit ; le problème arrive avant cette vérification, et ne doit pas être masqué par un faux 200.

**Candidat de code nouveau (non encore prouvé)** : définir `HybridBearerAuth.__call__` explicitement dans `backend/diabetes/api/v1/security.py`. Ce point de passage unique lit `Authorization`, accepte seulement le schéma Bearer (insensible à la casse) et un jeton non vide sans espace ambigu, puis appelle `self.authenticate` qui applique toujours la signature/version et le conflit cookie. Les headers malformés restent rejetés ; `SessionAuth` interdit la reprise silencieuse via cookie quand un header Authorization est présent. Le nouveau test réel PG16 doit prouver lecture privée A et B, rejet des requêtes croisées, révocation effective du token de A à logout et non-impact sur B, puis re-login. Les sondes temporaires seront retirées seulement après diagnostic final.

**État :** fix candidat GitHub PR Draft uniquement, sans déploiement Vercel. La précédente API hébergée `53f22063` et Web `5cf30263` restent inchangées. G2 protection branche Neon Production toujours refusée par quota du forfait Free ; aucun coût/souscription/DB prod touché. W01 **NO-GO** jusqu'aux preuves.


### W01 — Épreuve HTTP A/B sans instrumentation (05/11/2026)

La précédente épreuve [W01 #41988593407](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41988593407) du candidat `HybridBearerAuth.__call__` strict `7783079d` donne encore **HTTP PostgreSQL FAILURE** pour GET /logs avec Bearer, `401` avant logout ; job statique SUCCESS. La trace de test affiche à nouveau `W01_NATIVE_VERIFY_IN_CALLBACK=[]`. **Attention à la limite :** le test diagnostic remplaçait lui-même `HybridBearerAuth.__call__`, `HybridBearerAuth.authenticate`, `SessionAuth.__call__` et `Operation._run_authentication` à l'aide de monkeypatch ; cette instrumentation peut interférer avec la méthode que le test cherche à qualifier. Il n'est pas rigoureux de déclarer le nouveau code invalide sans réexécuter le parcours sans ces substitutions.

**Nouvelle épreuve candidate :** retirer *tous* les monkeypatches et leurs traces du test W01, tout en conservant `@pytest.mark.django_db(transaction=True)`, les assertions sur `GET /logs A et B = 200` sans cookies, `GET/PATCH/DELETE` entre comptes = 404, logout A revocation version, ancien Bearer = 401, B non affecté, nouveau A autorisé, logout B, jeton falsifié/cookie discordant = 401. Le vrai scénario A/B HTTP/PostgreSQL reste non passé à l'instant du commit. Aucune baisse de garde sécurité, aucun déploiement Vercel ni mutation Neon Production.


### W01 — Nouvelle preuve indépendante du test sans sondes et diagnostic du callback réel (05/11/2026)

Le test [W01 #41989388386](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41989388386) du commit `0d76afdc` est **HTTP PG16 FAILURE** (`GET /api/v1/logs HTTP 401`) alors qu'il ne remplace plus aucune méthode d'authentification ; `w01-static` SUCCESS. Cette preuve **écarte les monkeypatches comme cause unique** du 401. Le commit de parser Bearer explicite `7783079d` était effectivement inclus dans le merge GitHub Actions précédent (source vérifiée sur `68084b9`).

**Stratégie diagnostique sans baisse de sécurité :** seul le test instrumente provisoirement `Operation._run_authentication`, à l'entrée de l'opération réelle, pour exécuter `verify_native_token` dans le même contexte et mesurer uniquement des booléens de parsing (schéma, séparateur, whitespace, token synthétique exact), le nom du module/méthode `HybridBearerAuth`, la présence de session et l'ID utilisateur *synthétique* vérifié ou le type d'exception. Ni jeton, ni cookie, ni donnée clinique réelle dans les logs. L'authentification conserve son comportement original via `return original_run(self,request)`. **But :** discriminer un refus de format, une divergence de module, un échec natif côté contexte HTTP, ou un autre point de rejet. Ne pas déployer ce test ni le code en Production. Supprimer ces sondes après diagnostic et refaire une preuve HTTP pure.

**Restant :** W01 no-go, G2 Neon Production Free protected=false, aucun déploiement Vercel, aucune donnée patient.


### W01 — Cause racine prouvée : fixture globale de test bloquant les vrais Bearers (05/11/2026)

**Preuve déterminante** : [W01 #41990125300](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41990125300), `w01-static SUCCESS`, vrai HTTP PG16 FAILURE. Le diagnostic `W01_HTTP_IN_OPERATION_GATE` montre pour A et B : module réel `diabetes.api.v1.security`, **call_method=`_session_aware_call`**, `scheme_ok=true`, `separator=true`, `token_present=true`, `has_whitespace=false`, `exact_synthetic_token=true`, **verify_native_token réussit dans le callback** (IDs synthétiques 3/4), `session_authenticated=false`.

L'inspection du code `backend/conftest.py` confirme une fixture `@pytest.fixture(autouse=True)` patchant `diabetes.api.v1.security.FirebaseAuth.__call__` (**FirebaseAuth alias de HybridBearerAuth**) par une fonction `_session_aware_call` qui retourne l'utilisateur lorsqu'il a une session Django, mais **retourne `None` pour toute authentification Bearer sans cookie**. Voilà l'origine exacte des 401 répétés dans le banc de test, malgré jeton signé valide et code backend présent. Le fichier lui-même annonçait « fall back to token check » alors que l'implémentation ne le faisait pas.

**Correctif déterministe candidat :** garder le comportement de compatibilité des anciennes fixtures Django `force_login` uniquement pour les requêtes **sans en-tête Authorization** ; dans tout autre cas (Bearer valide, invalide, contradictoire), déléguer au **véritable `FirebaseAuth.__call__` capturé avant le patch**. Cela permet à la nouvelle épreuve W01 PostgreSQL de tester le vrai authentificateur au lieu de son substitut no-op. **Retirer** le parser `HybridBearerAuth.__call__` ajouté par hypothèse précédente, car le parser de Django Ninja n'était pas la cause ; éviter la duplication du code de sécurité Production. **Retirer** toutes les sondes temporaires de W01. Renforcer le test A/B avec un cookie B + Bearer A explicitement contradictoires → 401. Conserver toutes les assertions de révocation du Bearer, de GET/PATCH/DELETE cross-patient 404 et de re-login A ; aucune baisse de sécurité.

**État :** vrai test sur CI du nouveau commit **à établir**, aucun déploiement Vercel et aucune modification Neon Production ; W01 reste NO-GO avant test vert, preuve sur Preview après GO Vercel et résolution du gate G2 Free/HTTP422.


## W01 — Résultat vérifié du correctif de révocation, 05/11/2026

**Décision :** sécuriser le trajet Web Preview → API Preview → Neon synthétique et certifier la déconnexion des comptes A/B, sans données patients réels. **Goal technique ciblé :** `POST /auth/logout` révoque l'ancien Bearer, le nouveau Bearer A et le Bearer B fonctionnent indépendamment, et B ne peut pas accéder en lecture/édition/suppression aux entrées A.

**Code candidat** : PR Draft [#1273](https://github.com/hraaaaf/IAMINA-MVP/pull/1273), HEAD sous test `977d137659244d0f834202d1f5aa41f334e3031c`. **Cause racine du 401 en CI réellement trouvée :** `backend/conftest.py` utilisait `@pytest.fixture(autouse=True)` qui substituait globalement `FirebaseAuth.__call__` (alias de `HybridBearerAuth`) par une fonction renvoyant toujours `None` lorsque la requête portait un Bearer sans cookie. La fixture désormais délègue au vrai `__call__` dès qu'un `HTTP_AUTHORIZATION` est présent ; le fallback `force_login` ne reste valable que sans header. L'override de parser natif introduit pendant le diagnostic a été retiré, et aucune sonde de test n'est conservée. Le correctif API `backend/core/api/v1/auth.py` valide explicitement le Bearer à `/auth/logout` sur le routeur public avant `revoke_native_tokens`, rejette invalidité ou conflit cookie/Bearer (401).

**Preuves CI exactes sur ce SHA :**
- [W01 #41990891616](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41990891616) **COMPLETED/SUCCESS, 2/2 jobs SUCCESS** : `w01-static` et `W01 synthetic Django HTTP to PostgreSQL`.
- Dans le job PostgreSQL16 réel : conducteur PostgreSQL, migrations, Django HTTP authentifié, `test_w01_native_logout_http.py` (Bearer A/B sans cookie, isolation GET/PATCH/DELETE par propriétaire, logout A et B invalidant leurs jetons, ancien Bearer 401, re-login A, contradiction cookie B/Bearer A 401), CORS et préflight fail-closed, serveur Vercel fail-closed : **toutes étapes SUCCESS**.
- **W01-G6 LOCAL :** le même job a exécuté `W01-G6 localhost PostgreSQL16 backup, restore and rollback` **COMPLETED/SUCCESS**. Ce résultat **n'atteste pas** une restauration sur Neon distant.
- [CI générale #41990891693](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41990891693) : au contrôle, **Backend Ruff+pytest FAILURE** et **Backend PostgreSQL source-of-truth FAILURE**, mais les suites passées comptent respectivement 2893 et 2896 PASS ; **5 tests en échec dans les deux suites** sont liés à `fallback.processor_identity evidence is stale` dans des tests de gouvernance pilot/consent `core/tests/test_pilot_consent_governance.py` et `core/tests/test_pilot_release_provider_scope.py`, **distincts du correctif W01**. Frontend PWA build était encore IN_PROGRESS au dernier contrôle, W01 spécifique entièrement vert. **Ne pas déclarer CI générale verte.** Ces tests de gouvernance conservent leur garde fail-closed : ne pas falsifier ni contourner l'évidence pour rendre artificiellement la CI verte.

**E2E hébergé et gate humain :** Web Preview `dpl_FbthU6wWtg6iuXwy6hdjoPbetJXq` READY runtime `5cf30263...`, API Preview `dpl_9ryTimFJ6JwsfbW66NXno2gWYcZB` READY runtime `53f22063...` : **aucun n'intègre le nouveau fix API du HEAD**. Le test Safari antérieur A→B→A/112 mg/dL portait uniquement sur coffres locaux ; deux `POST /auth/logout` hébergés répondaient 200 mais les versions de révocation en Neon sandbox étaient restées 0. La correction existe **uniquement en GitHub/CI** jusqu'à un **nouveau GO explicite** pour déployer **API Preview synthétique uniquement** et refaire login/logout A/B, preuve de `auth_token_version` et lecture distante cross-patient. **Aucun déploiement Vercel, aucun merge** dans ce closeout.

**Gates W01 après preuve :** G4/G5 hébergés **PARTIELS**, G6 **PASS local / NON PROUVÉ distant**, G7 **OUVERT** (preuve candidate/revue indépendante/merge/postmerge), G2 **BLOQUÉ EXTERNE** : Neon IAMINA Production `br-fragrant-frost-b1lbdfzs` `protected=false`. Demande `protected=true` refusée HTTP 422 sur forfait Neon Free ; aucun achat ni changement Production. G3 environnement/SMTP/risques production patient non clos. Les cinq tests de gouvernance stale restent signalés séparément. **Verdict W01 global NO-GO**, W02 GELÉ, Production patient INTERDITE.

**Next exact :** (1) confirmer résultat complet CI générale sur SHA code ; (2) recueillir le **GO distinct Vercel API Preview** pour vérifier correction de révocation en runtime synthétique ; (3) vérifier compteurs et API A/B plus restauration distante isolée selon autorisations ; (4) régler G2 forfait/protection via décision humaine, G7 revue indépendante et closeout/merge seulement si toutes preuves obtenues. Aucun % non vérifié.


## W01 — Reprise CI après preuve hébergée, 2026-11-05

**Goal :** conserver la preuve réelle de révocation du vieux Bearer (`GET /api/v1/logs 200` à 13:01:32.705Z, `POST /api/v1/auth/logout 200` à 13:01:33.181Z, même Bearer `GET /api/v1/logs 401` à 13:01:33.643Z sur API Preview `dpl_5Udg4esbrYAHqY4RRLB2SsdkfNnv`), sans prétendre certifier le chantier complet.

**Neon (inventaire AFTER contrôlé) :** suppression autorisée des neuf branches non-default de la sandbox `noisy-truth-00115950` ; conserve sa seule branche `synthetic-only` (`br-sweet-frog-b9ok6ptp`, endpoint `ep-old-art-b9sy0oo4`), son snapshot `snap-orange-mode-b9tjsdd1` et le projet Production `square-sun-82359137` avec son unique branche `production` (`br-fragrant-frost-b1lbdfzs`, `protected=false`), plus les projets tiers inchangés. IAMINA 11 → 2 branches, sans purge des bases conservées. La restauration G6 antérieure metadata-finalized n'est pas une certification de récupération de données de Production.

**Corrections candidates sur branche Draft (GO Preview donné le 05/11) :** test Flutter `w01_revocation_probe_test.dart` exécute un test fail-closed sans flag sur CI générale et des scénarios HTTP mock uniquement avec `IAMINA_W01_SESSION_PROBE=true` sur la Web Preview ; géométrie Login change `EdgeInsets.fromLTRB` en `EdgeInsetsDirectional.fromSTEB` pour le RTL. Cinq tests historiques de gouvernance exécutent leur commande au contexte explicite du 04/08, sans changer la validation ni les dates d'approbation ; un test supplémentaire exige le refus `fallback.processor_identity evidence is stale` au 05/11. **L'attestation opérationnelle réelle reste expirée et Production NO-GO jusqu'à une revue humaine conforme.**

**À vérifier après commit :** CI W01, Flutter générale, backend pytest/Postgres, D7 FUE et Developer portability ; Web Preview SHA exact, RTL et bouton sur mobile/desktop. **Aucun commit = autorisation de Production**. G2 Neon protected branch payante reste human gate ; G6 intégrité DR Production et G7 revue indépendante demeurent ouverts. Logs et décision exhaustive dans [Notion W01](https://app.notion.com/p/3fc77c66336281ab8bfcf0c6b0060e2f). W01 global NO-GO.

## W01 — G2 annulé ; G6 snapshot et récupération ; G7 état (05/11/2026)

**Décision utilisateur :** G2 annulé/WAIVED et sorti du chemin de travail W01. Cette annulation n'est pas une certification : Neon Production reste sans branche protégée ni allowlist IP sur le forfait Free. Ne pas réactiver G2, changer d'offre, appliquer des protections ou toucher Production sans nouvelle instruction explicite. Elle ne vaut pas autorisation de déployer pour de vrais patients.

**Référence de preuve** : PR #1273 Draft, HEAD code 14a97bfa, 17/17 workflows GitHub SUCCESS ; deux Previews Web/API READY au même SHA ; A→B→A et isolation confirmés humainement, sans trace réseau instrumentée transmise.

### G6 — essai de restauration synthétique et incident rétabli

Projet sandbox noisy-truth-00115950, branche originale br-sweet-frog-b9ok6ptp, endpoint original ep-old-art-b9sy0oo4.c-7.eu-central-1.aws.neon.tech, DB iamina925_empty. AVANT : 46 tables publiques, 2 comptes, 2 profils, 78 événements, 76 auth buckets.

Snapshot daté du 21/10/2026 snap-orange-mode-b9tjsdd1. L'outil restore_snapshot sans target_branch_id a, de façon inattendue, permuté la branche par défaut et l'endpoint du sandbox. La branche restaurée br-super-block-b9ka8qll contenait 42 tables mais 0 compte/profil/événement/bucket. L'ancienne branche br-sweet-frog-b9ok6ptp a conservé toutes les données actuelles. Incident transitoire possible sur Preview, non mesuré via une trace client.

RÉCUPÉRATION VÉRIFIÉE : branche tampon non-default br-rough-meadow-b9fcfhaq sans compute créée, endpoint additionnel ep-cool-dream-b98tmthn déplacé via tampon, endpoint original ep-old-art-b9sy0oo4 réassigné à la branche d'origine br-sweet-frog-b9ok6ptp, branche renommée synthetic-only et rétablie default=true. Snapshot historique br-super-block-b9ka8qll nommé w01-g6-snapshot-proof-20261105, non-default, accessible sur endpoint alternatif ep-cool-dream-b98tmthn. AFTER ORIGINAL : 46 tables, 2 comptes, 2 profils, 78 événements, 76 auth buckets, tous identiques à l'avant-test. Neon Production et Vercel non modifiés.

Deux branches auxiliaires G6 restent dans le sandbox (snapshot et tampon). Suppression non autorisée : action destructive soumise à confirmation spécifique. Tentative de snapshot courant sur la source : HTTP 422 snapshots limit exceeded ; aucune suppression de l'ancien snapshot. G6 = restauration HISTORIQUE constatée, récupération ACTUELLE et Production NON certifiées. Ne pas relancer restore_snapshot sans procédure explicitement sans bascule de l'endpoint.

### G7 — revue de cohérence statique, pas revue indépendante

À HEAD code 14a97bfa, audit ciblé : auth.py (création comptes interdite Preview ; logout révoque Bearer), diabetes/api/v1/security.py (tokens natifs + conflit identité), diabetes/api/v1/logs.py (scope patient et actions protégées), middleware/csrf_exempt_api.py et vercel_session_auth.py (CSRF et fail closed), frontend/api/index.js (proxy Preview fail-closed et aucun cookie transféré), backend/amina/settings.py (cookies HTTPS si DEBUG=False) ; DEBUG=False contrôlé en variables Vercel Preview et Production. Test W01 réel PG16 sur les Bearers et cross-patient présent et CI 17/17 SUCCESS à l'ancien HEAD.

Le contrôle ci-dessus ne remplace pas un avis indépendant ni un test E2E adversarial documenté. G7 = NON certifié. Aucun merge ni déploiement Vercel autorisé par cette note.

**Next exact** : documenter une restauration isolée sans permutation endpoint ou banc indépendant, résoudre la limite snapshots sans supprimer une preuve sans accord, obtenir revue indépendante G7 ; recontrôler les nouvelles CI du commit documentaire. Notion : https://app.notion.com/p/3fc77c66336281ab8bfcf0c6b0060e2f


## 05/11/2026 — Closeout technique CI W01 (décisions propriétaire actualisées)

**Goal :** vérifier la non-régression Web/API/DB et les captures Chrome pour le candidat de branche Draft, avec preuves GitHub sur SHA exact. **Succès observé sur `31f12e94a6301d50dcb1ee5e1335e02b9eadcf48` : 17/17 workflows COMPLETED/SUCCESS** (aucun workflow en cours/rouge lors du contrôle final). Il s'agit du HEAD précédant l'ajout de ce compte-rendu ; un commit documentaire suivant exige son propre état CI et ne peut hériter du statut sans contrôle.

**Preuves sur `31f12e94a6301d50dcb1ee5e1335e02b9eadcf48` :** [CI générale #42111037305](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42111037305) SUCCESS avec jobs `Backend — ruff + pytest`, `Backend — PostgreSQL source-of-truth` et `Frontend — analyze + tests + PWA build` tous SUCCESS ; [UI browser screenshot #42111037412](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42111037412) SUCCESS pour 390×844, 768×1024, 1280×900, chacun avec 18 captures réelles et trois artifacts présents (IDs 13455002651, 13454012509, 13454012785) ; [D11 routed FR/AR Web PG16 #42111037450](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42111037450) SUCCESS ; [Developer portability #42111037312](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42111037312) SUCCESS. Aucun score de similarité visuelle manuel BEFORE/AFTER annoncé, car aucune modification de UI Flutter n'a été faite dans ce sous-lot : le correctif `.github/workflows/ui-browser-screenshot.yml` ne touche que le démarrage de Chrome (3 essais propres, fail-closed), sans désactiver l'exigence de capture ou ses assertions.

**Périmètre révisé confirmé par propriétaire :** **G2 ANNULÉ/WAIVED pour le travail W01**, non certifié ni sécurité de Production obtenue. **G6 REPORTÉ AVANT lancement réel** (sauvegarde indépendante, récupération isolée et vérification intégrité), car l'application n'a pas encore de données patients réels ; ne bloque plus le développement ou le closeout technique synthétique. Ne pas relancer les manipulations Neon G6 durant le développement ; garder les branches/snapshots existants sans suppression non autorisée. **G7 OUVERT** : le dossier technique existe, mais **0 revue indépendante sur PR #1273** à la vérification. La CI verte ne certifie pas la confidentialité des données réelles ni le lancement clinique.

**État :** sous-lot correction Ruff + Chrome **VALIDÉ PAR CI sur `31f12e94a6301d50dcb1ee5e1335e02b9eadcf48`**. **W01 release/patient NO-GO**, PR #1273 reste OPEN/DRAFT/non fusionnée. Aucun nouveau déploiement Vercel ni modification Neon Production ; les Previews READY existantes restent sur leur SHA applicatif antérieur `14a97bfa4fc74a8869ff7c7de16b9cf800b4ab70`, non sur le HEAD documentaire. L'absence de revue G7 et la divergence avec la Preview déployée restent explicites.

**Next exact :** contrôler la CI du commit de closeout documentaire, puis obtenir une **personne distincte et habilitée** pour la revue G7, avec verdict GitHub ou rapport signé sur SHA figé. Sans reviewer nommé, gate humain réel (ne pas s'auto-approuver). Préparer une nouvelle Preview seulement après GO explicite du propriétaire.


## 05/11/2026 — W01/G7 : nouvelle méthode de validation, FUE adaptés (décision propriétaire)

**Correction de doctrine :** le propriétaire a explicitement remplacé **la revue G7 indépendante comme condition de clôture du lot de développement W01** par des **First User Experiences (FUE) ciblés**, vérifiables sur vraie interface Flutter Web et PostgreSQL16 synthétique éphémère. Il n'est plus attendu de bloquer W01 sur la désignation d'un reviewer externe GitHub. Cette nouvelle décision prévaut sur les mentions historiques « G7 reviewer blocking » présentes plus haut dans ce document. **La conformité et le GO de mise en Production avec patients réels restent des gates distincts** : les FUE de développement ne peuvent attester à eux seuls la sécurité d'un service clinique réel.

**Goal sous-lot :** parcours Web réel A→logout→B→logout→A, avec comptes synthétiques, 401 anciens jetons, 404 accès croisés GET/PATCH/DELETE, 403 inscription Preview, cookie/bearer et CSRF négatifs, 0 fuite et preuves JSON + screenshots. **Critère succès :** FR et AR PASS sur Chrome réel mobile 390×844 et desktop 1280×900 et DB post-FUE intacte ; le run Workflow du SHA exact doit être SUCCESS. Si un seul verdict négatif : FUE NON VALIDÉ, correction obligatoire.

**Candidat implémenté dans cette PR :** .github/workflows/w01-g7-web-fue.yml ; tools/w01_g7_preview_fue_browser_check.js ; frontend/lib/ui_w01_g7_preview_fue_main.dart ; scripts/w01_g7_fue_seed.py ; backend/core/tests/test_w01_g7_fue_privacy.py. Protocole détaillé : docs/reviews/W01_G7_FUE_WEB_2026-11-05.md. **Le nouveau FUE n'est PAS déclaré passé avant les logs/artifacts du run correspondant à son SHA.** Les 17/17 workflows du parent `90fd8cfd` étaient SUCCESS avant le commit candidat FUE.

**Bornes :** aucun déploiement Vercel, aucun merge, aucune mutation Neon. Le FUE Web local PG16 ne prouve pas un E2E hosted OIDC de la Preview; si requis ultérieurement, human gate de déploiement Vercel explicite. G2 annulé ; G6 reporté à la préproduction. **Next exact :** exécuter et durcir le FUE jusqu'à PASS observé, documenter SHA/runs/artifacts ; clôturer W01 technique sans exiger une signature indépendante GitHub, mais sans déclarer Production-ready.
