# IAMINA WEB — W02/D11 — Vercel Preview isolé (19/10/2026)

## D10 — constat indépendant de revue de code (19/10/2026, HEAD 12072153)

**Goal :** ne jamais permettre qu'un compte distant B devienne l'autorité de récupération d'un verrou Web appartenant à A, ni traiter un simple déverrouillage de plateforme comme une preuve d'appartenance du coffre patient. **Statut : D10 OPEN, blocage de certification, non-exploitation prouvée.**

**Preuve statique exacte :**
- `frontend/lib/services/app_lock_authenticator.dart` : `AppLockCredential` contient `credentialId`, `publicKeySpki`, `rpId`, `origin`, `signCount`, **aucun identifiant de compte patient/propriétaire**.
- `frontend/lib/services/app_lock_service.dart` : les clés de stockage `iamina_app_lock_credential_v1` et `iamina_app_lock_required_v1` sont globales à l'installation. `recoverWithVerifiedRemoteAccount()` vérifie seulement `isRemoteCredentialVerified` et `hasRemoteApiCredential`, sans comparer `auth.boundNativeAccountId` à l'identité du propriétaire du verrou préexistant. Ensuite elle supprime les deux marqueurs et autorise une réinscription. `unlock()` valide une assertion d'authentification de plateforme mais ne compare pas non plus un propriétaire du credential à `boundNativeAccountId`.
- `frontend/lib/services/auth_service.dart` : `boundNativeAccountId` est disponible ; `resolvePatientVaultScope()` attribue bien les noms physiques distincts `amina_vault_v1_native_<id>`. `PatientVaultSessionController` et `PatientVaultAppHost` compartimentent les bases/epochs. Cette séparation réduit les risques de fuite de données, mais **ne prouve pas** l'autorité du compte B sur le verrou de A.
- Les tests actuels couvrent le verrou au démarrage, l'absence de credential, l'échec de recovery sans compte distant vérifié, le logout et A→B→A physique ; **ils ne prouvent pas le refus de récupération croisée A→B avec B distant vérifié**.

**Qualification :** lacune d'autorisation dans le contrat de récupération **confirmée par lecture du code** ; exploitabilité clinique, exposition de données, contournement WebAuthn et scénario E2E **non démontrés**. Ne pas appeler cela une fuite prouvée. La validation D10 reste **NO-GO**.

**Correction recommandée (pas encore implémentée) :** définir une propriété de verrou persistée et non ambiguë, liée au `nativeDjangoUserId` de A et vérifiée lors du recovery ; une session B, même distante et valide, doit être refusée pour récupérer A. En cas d'identité propriétaire manquante/corrompue, conserver un état fail-closed avec procédure de récupération explicite, sans effacer les données locales ni réinscrire silencieusement. Tester A→logout→B→tentative recovery A (refus), puis A→recovery autorisé, redémarrage, retour B, annulation WebAuthn, et stockage ambigu. Le design doit aussi préserver le mode device-local et la migration des anciennes installations ; ne pas décider une migration irréversible sans preuve de compatibilité.

**Next exact :** écrire les tests de propriété A/B (D10) et le contrat de migration fail-closed sur la branche W02 isolée, exécuter Flutter/Dart + vrai Chrome, puis évaluer un patch minimal sans modifier W01.


> **ACTUALISATION DÉCISIVE — 19/10/2026 : GATE VERCEL PREVIEW→PREVIEW PASS SUR ROUTES PUBLIQUES.** Après autorisation par le propriétaire dans le tableau de bord Vercel, le déploiement Web Preview `dpl_8v69xWz2FaURzoVjJnNitb16rSp4` expose `GET /api/v1/health` **200 JSON** (`status=ok,db=ok,cache=unavailable`) et `GET /api/v1/demo/scenarios` **200 JSON / 8 scénarios** via le BFF même origine ; API directe health 200 ; Web racine 200. Les deux projets conservent leur SSO. Les anciens résultats **302 amont / 502 BFF** ont été résolus pour ces deux routes et décrivent seulement l'état AVANT l'intervention. Les en-têtes Web observés : `Cache-Control: private, no-store, max-age=0`, `X-Content-Type-Options: nosniff`, ni `Set-Cookie` ni CORS permissif transmis. **Périmètre précis du PASS : liaison OIDC/Vercel et routes GET non cliniques ; pas encore de preuve de session patient Django, autorisation 401/403, compartimentation A/B ou test Chrome E2E.** Un outil fetch de Vercel a intercepté les réponses attendues 401 des routes cliniques comme `deployment_authentication_required`, donc verdict négatif hébergé **INCONCLUANT**. Django tests synthétiques existants restent prouvés par CI. À la dernière vérification, W01 PR #1128 est à HEAD `7f222dbc93fe799dc282526ffa2bfdcd573843bf` et CI actuelle partiellement rouge/en cours : W01 **NO-GO** ; D11 **OPEN** ; aucun merge ni Prod. Avant clôture, vraie session navigateur autorisée, comptes synthétiques A→logout→B→A, compte neuf 0 faux logs, audit indépendant, décision récupération/chiffrement W02, W01 GO puis rebase/CI finale.


**Status : D11 OPEN / W01 NO-GO / zéro promotion Production.** Cette preuve concerne un candidat Preview synthétique non fusionné ; elle ne certifie pas le parcours patient.

## Goal / succès / preuves

- **Goal D11 :** compte patient neuf vide, aucune injection de mesures de démonstration, aucune suppression de mesures existantes dans un coffre patient.
- **Succès produit requis :** code Flutter/Drift + Django, tests d'isolation A/B et compte neuf, E2E Chrome via SSO Web → BFF → authentification Django → Neon Preview isolée, sécurité et revue indépendante.
- **Preuves présentes :** trois protections et exécution réelle Django + Flutter en Vercel Sandbox, build Vercel des deux projets. **Preuves manquantes :** E2E sécurisé hébergé, revue indépendante, GO W01.

## Source GitHub, portée

- Branche isolée : `test/w02-d11-vercel-preview-20261019`, depuis l'ancien W01 HEAD `8c072a3ebcb838fd575d3febd66f1179f3a5c724` ; base historique de `main` `31380a7f4c8f61a3ec886ec9d2d66d26c2bf222b`.
- `e6ea036fe44ef35368ea1a49eaf6524c06dcffd0` : garde de scope dans `offline_demo_audit_seed.dart`, garde directe préalable à toute transaction dans `AppDatabase.seedDemoData()`, retrait de la logique backend d'injection du patient ; tests Dart et Django.
- `e179a0b541ac78bd0d6cda7c3d8fc35199e49b19` : BFF origine API Preview exacte + oracle Node correspondant.
- `688e028fba0caa165c7daffd345ff06d86f1b947` : accolade dans la garde Dart, `flutter analyze` propre.
- **Pas de merge, pas de branche Production, aucune mutation Neon Production ni compte médical réel.** Auto-deploy Git désactivé dans les manifests.

## Artefacts Vercel exécutés, SSO conservé

| Élément | Projet | Déploiement | Commit | Résultat |
|---|---|---|---|---|
| Django API Preview | `iamina-certified` | `dpl_4RRtv8Aog9ZhzEswK3ftbgtXdFWU` | `e6ea036` | READY / cible Preview |
| Flutter Web Preview | `iamina-review` | `dpl_EhPvMv2x9eHcDY8VjD6nZ8sUejgf` | `688e028` | READY / cible Preview |

API : https://iamina-certified-1mrvxnuk9-achraf-benmoussa-s-projects.vercel.app
Web : https://iamina-review-42tjbohfh-achraf-benmoussa-s-projects.vercel.app

- API `GET /api/v1/demo/scenarios` → 200 et huit scénarios ; `GET /api/v1/health` → 200, `status=ok/db=ok/cache=unavailable`. Cache dégradé reste à diagnostiquer. DB Preview configurée avec identité différente de Production et vérification fail-closed Django, sans exposition de DSN.
- Web `GET /` → 200 HTML, build Flutter Release réussi sur Vercel ; SSO de `iamina-review` activé pour Preview et celui de `iamina-certified` toujours activé.
- Web BFF `GET /api/v1/health` et `GET /api/v1/demo/scenarios` → **502** malgré API 200 directement, y compris après build sur `688e028`.
- **Gate externe prouvé :** tentative Vercel `PATCH /v9/projects/prj_Pn9FnyconF3h2w9gOU74iV98kJoU` pour une Trusted Source **uniquement** `iamina-review (prj_AYaUi32KTDHak8I7dmdQpDrqd8SI) from:preview → to:preview` → **HTTP 404**, `Deployment Protection Trusted Sources not found`. Aucun changement de contrôle d'accès obtenu ; pas de bypass global, pas de désactivation SSO. Cause exacte interne du 502 non attestée par trace d'upstream ; configuration Trusted Sources reste néanmoins indispensable.

## Résultats de tests exécutés, source exacte

Sandbox Vercel sécurisé, checkout SHA `e179a0b` puis `688e028`, ressources synthétiques, réseau sortant restreint :

1. Django réel : `python manage.py test diabetes.tests.test_w02_d11_demo_seed_disabled` → **3/3 PASS**, aucune base de données de production ouverte par cette suite `SimpleTestCase`.
2. Django `Client` local avec authentification **synthétique mockée** : `POST /api/v1/demo/seed` sans identité → **401** ; après authentification simulée → **404** `Demo seeding disabled`. **Ce n'est pas un POST réel authentifié sur l'API hébergée.**
3. Node `scripts/tests/test_w01_preview_bff.mjs` → **17/17 PASS** ; topologie `scripts.tests.test_w01_web_topology_contract` → **7/7 PASS**.
4. Flutter 3.41.0, sandbox Linux avec `libsqlite3.so` lié au `libsqlite3.so.0` de l'OS : **40/40 tests PASS** au HEAD `688e028` ; suites D11, isolation coffre, auth locale, gate compte existant.
5. `flutter analyze lib/services/offline_demo_audit_seed.dart lib/data/drift/database.dart test/services/d11_vercel_preview_guards_test.dart` → **No issues found**, code de sortie 0, après correction d'une règle d'accolades.
6. Le premier essai Flutter a échoué sur `libsqlite3.so` absent dans le sandbox ; l'ajout du symlink local a rendu les tests exécutables. Ce n'était pas un défaut d'application.

## Blockers, next et interdit

1. **Human/external gate Vercel :** dans **iamina-certified → Settings → Deployment Protection → Trusted Sources**, faire autoriser *seulement* `iamina-review` **Preview → Preview** par un administrateur, ou résoudre le 404 avec Vercel Support. Ne pas toucher à Production ni configurer de bypass statique permanent. Ensuite re-vérifier les réponses HTTP via Web.
2. Test E2E Browser Chrome sous SSO réellement connecté, comptes synthétiques A/B, logout, compte neuf zéro mesure, conservation sentinelles, erreurs 401/403/502 ; vérifier chiffrement/lock plus tard au lot D10.
3. Revue de sécurité indépendante, tests CI sur tête finale W01, correction de l'écart parent W01 actualisé, puis éventuelle intégration avec autorisation et GO W01. Les limites W01 SessionAuth/cookies, pièces >4 MiB et cache dégradé restent ouvertes.
4. **Aucune D déclarée DONE**, pas de merge, pas de promotion ni de déploiement Vercel Production. Statut exact : W01 NO-GO, W02 testé en isolation, D11 OPEN.

Journal Notion : https://app.notion.com/p/3fd77c66336281f390e2fe3e46651931
Issue de suivi : https://github.com/hraaaaf/IAMINA-MVP/issues/1130


## Diagnostic hosted W01-G5 — 19 octobre 2026 — REDIRECTION 302 PROUVÉE

**Objectif observable :** classifier le HTTP 502 du Web BFF sans exposer de secret ou de données patient. **Résultat réel :**

- Nouvelle instrumentation **Preview uniquement**, commit source `5c447f997f9747e464cfd6821d5a9fa944b2583d`, modifie `frontend/api/preview-proxy.js` uniquement : `console.warn` avec **catégorie fixe et entier HTTP** ; aucun jeton OIDC, Authorization, cookie, chemin de requête, contenu patient ou exception réseau journalisé. Régression Node sur clone exact en sandbox Vercel : **17/17 PASS**. Sandbox `sbx_8yTIgs28swVhpxHUnYotq27kaCUE` **arrêté** après les tests.
- Web Vercel Preview **`dpl_ETsHZM56R2ZpEBBn37FNZkM94rUx`** `READY`, déployé manuellement sur commit `5c447f9` : `https://iamina-review-4bv5j2qrc-achraf-benmoussa-s-projects.vercel.app`. GET / = **200**.
- GET `/api/v1/health` via Web = **502** ; log serveur de ce déploiement daté **19/10/2026 11:08:20Z**, request `6b88d-1792408099873-9436f40ef744`, classe `IAMINA_W01_PREVIEW_UPSTREAM_GATE {category:'redirect',status:302}`.
- GET `/api/v1/demo/scenarios` via Web = **502** ; log serveur daté **11:08:23Z**, request `g46rh-1792408103847-dd9faea254ff`, **même HTTP 302** en amont.
- La réponse `302` est refusée par le BFF conformément à son contrat fail-closed, qui retourne `502` au navigateur ; **le 502 n'est pas dû à une erreur réseau du BFF ni à un crash Flutter** dans ces deux requêtes. L'URL Location du 302 et les claims OIDC n'ont pas été inspectés/journalisés ; la redirection est compatible avec une interception par Vercel Deployment Protection/SSO mais cette cause exacte nécessite la configuration d'autorisation interprojets.
- API Preview autonome `dpl_4RRtv8Aog9ZhzEswK3ftbgtXdFWU` a confirmé auparavant GET /api/v1/health 200 sous accès Vercel autorisé (`db=ok/cache=unavailable`) et demo/scenarios 200. **Aucun succès Web→API protégé n'a été observé.**

**GATE EXTERNE inchangé :** Projet API `prj_Pn9FnyconF3h2w9gOU74iV98kJoU` → Settings → Deployment Protection → Trusted Sources : autoriser exclusivement l'appelant `prj_AYaUi32KTDHak8I7dmdQpDrqd8SI`, **from=preview → to=preview**. La requête de configuration par API échoue **HTTP 404 `Deployment Protection Trusted Sources not found`** (request ID `fra1:sfo1::cd64q-1792406808820-a673da3b16c3`). Contacter administrateur/support Vercel, sans désactiver SSO ni créer de bypass statique. Référence incident : https://github.com/hraaaaf/IAMINA-MVP/issues/1130#issuecomment-6265746724

**Next exact après human gate :** rerun GET /api/v1/health + scenarios par URL **Web Preview** et constater **200 JSON** sous OIDC, puis test Chrome connecté identité synthétique A/B, compte neuf vide D11, contrôle de non-interférence Neon, revue indépendante et closeout W01. Retirer le code temporaire d'observabilité avant toute intégration de production. **W01 NO-GO ; D11 OPEN ; aucun GO certifié.**


## Correctif complémentaire D11 — login, audits visuels, CI (19/10/2026)

**Goal :** empêcher toute injection automatique de données fictives lors d'une authentification patient et conserver les outils de visualisation sans toucher aux coffres cliniques. La certification D11 reste **OPEN** tant que les vraies épreuves de navigation/SSO et la revue indépendante ne sont pas obtenues.

**BEFORE vérifié source et premières CI** :
- `login_screen_mena.dart` et `login_screen_fr_certified.dart` déclenchaient explicitement `api.seedDemoData()` puis `db.seedDemoData()` après `auth.signInAnonymously()`, ce qui contredisait l'isolation D11. `ApiClient` conservait une méthode pour l'ancien POST /api/v1/demo/seed qui est désormais volontairement HTTP 404 côté Django.
- Outils de capture `ui_browser_audit_main.dart`, `ui_global_desktop_missing_audit_main.dart`, `ui_dashboard_backend_cert_main.dart`, `ui_visual_screenshot_test.dart`, `reports_mobile_metrics_layout_test.dart`, `dashboard_responsive_convergence_visual_test.dart` initialisaient des données de test dans `AppDatabase.defaults()` (legacy) ou une mémoire non scoped. Les nouveaux gardes D11 les bloquaient — comportement fail-closed attendu.
- Workflow `dashboard-responsive-visual-cert.yml` appelait `POST /api/v1/demo/seed` sur une identité synthétique dans son PostgreSQL temporaire ; HTTP 404 attendu, CI `39251988136` **FAIL**, aucune capture faite. `reports-mobile` CI `39251987922` FAIL 3/3 à cause du guard audit-only, `P7` CI `39251988179` FAIL 4/4 pour la même raison. `global missing routes` CI `39251987917` FAIL car `kIsWeb` n'était plus importé dans login FR après nettoyage.

**Goal visuel écrit :** mêmes libellés, layouts et fixtures intentionnellement synthétiques qu'avant le garde, mais stockés exclusivement dans `PatientVaultScope.auditOnly()`; aucun changement de style/contenu clinique réel prévu. **Références BEFORE** : assertions des tests golden/metrics et workflows Chrome existants ; aucun score numérique inventé. Les mêmes viewports doivent être capturés APRES : 390×844, 768×1024, 1280×900, plus tests responsive P7 et échelles de texte 1.0 / 1.3 / 1.6. Comparaison visuelle/scoring restent non faits tant que les artefacts Chrome ne sont pas disponibles.

**Implémentation sur la PR Draft #1131** :
- Login FR/MENA : supprime les deux appels de seeding ; le login démo ne fait que `auth.signInAnonymously()` (session d'audit) ; rétablit `package:flutter/foundation.dart` nécessaire à `kIsWeb`. `ApiClient.seedDemoData()` historique retiré, aucun client Web ne construit la requête patient de demo seeding.
- Les entrées `ui_browser_audit_main.dart`, `ui_global_desktop_missing_audit_main.dart`, `ui_dashboard_backend_cert_main.dart` utilisent `AppDatabase.forPatientVault(PatientVaultScope.auditOnly())`.
- Fixtures mémoire `ui_visual_screenshot_test.dart`, `reports_mobile_metrics_layout_test.dart`, `dashboard_responsive_convergence_visual_test.dart` utilisent `AppDatabase.testPatientVault(NativeDatabase.memory(), PatientVaultScope.auditOnly())`, sans changer les widgets.
- Le workflow `dashboard-responsive-visual-cert.yml` crée exclusivement une identité backend synthétique **vide**, ne fait plus le POST de demo seeding, valide son Bearer sans exposer de token dans les logs, et ajoute une suite Django 3 tests et une suite Flutter D11/no-seed avec SQLite natif local.
- Nouveau `test/d11_demo_login_no_seed_contract_test.dart` : test des deux écrans login, de l'absence du client POST demo, et de l'ordre garde audit-only → transaction/suppression.

**Preuves au moment de ce lot** : vérification directe de neuf blobs GitHub d'isolation **9/9 source checks PASS** sur le HEAD antérieur `5e9a30b`. Les **8 workflows GitHub** ont été déclenchés automatiquement par les chemins UI des correctifs, certains encore queued/in_progress ; les FAIL ci-dessus ont été diagnostiqués par stacks/étapes GitHub et corrigés. **Pas encore de confirmation CI Flutter/Chrome sur le dernier HEAD `4d789707e397a7959a21bafc1baa7cec682dce5e`**, ne pas lui attribuer les tests verts d'anciens SHAs. En historique sur SHA `688e028` : 40/40 Flutter D11/auth/coffre + 15/15 UX/first-use/D9, Django 25/25, Node BFF 17/17, analyze ciblé propre. **Ces historiques ne certifient pas la nouvelle version**.

**Blocage inchangé W01** : API Preview directement 200, BFF Web amont redirect **302** → navigateur 502 en fail-closed. Vercel Trusted Sources Preview→Preview refusée **404** par plateforme ; intervention administrateur/Support nécessaire. Aucun bypass statique, pas de désactivation SSO. SSO hébergé E2E multi-comptes non réalisé.

**Next exact** : lire CI sur dernier HEAD, analyser/corriger toute erreur restante, exécuter vraies captures Chrome et comparaison BEFORE/AFTER lorsqu'elles sont disponibles, reprendre Web→API seulement après Trusted Sources. Maintenir PR Draft et non fusionnée, W01 NO-GO, aucune D DONE, zéro Vercel Production et zéro donnée patient.

## Validation UI finale — 19/10/2026
**8/8 UI workflows SUCCESS sur 4d789707e397a7959a21bafc1baa7cec682dce5e**, sans FAIL. Dashboard responsive run **39253126899** : tests réels Django D11 **3/3**, Flutter D11 + login no-seed **6/6**, compte backend synthétique vide, **9/9** captures Chrome distinctes et zéro erreur console.

**BEFORE** : run navigateur audit **39251988081**, 54 PNG (18 écrans × 390×844, 768×1024, 1280×900). **Goal** : mêmes écrans et données fictives réservées au coffre audit-only, jamais au patient. **Mockup/référence** : ces 54 PNG d'origine. **Implémentation** : deux login sans auto-seed, API client sans appel /demo/seed, fixtures visuelles isolées, workflow Django sans seed patient. **AFTER** : run navigateur audit **39253126717**, 54 PNG aux mêmes dimensions. **Comparaison vérifiée** PIL/numpy/skimage : SSIM moyen **0,999935**, médian **1**, minimum **0,999450**, pixels différents moyens **0,005 %** ; 0/54 image sous SSIM 0,98. **Score de fidélité visuelle = 99,9935 %**, pas un score clinique ou de sécurité. Rapport reproductible/empreintes SHA des six ZIPs : `IAMINA_D11_visual_comparison_2026-10-19.json` et script `IAMINA_D11_visual_compare.py` dans la conversation.

**Limite de certification** : ces succès concernent le code `4d789707`, la PR comporte ensuite des changements documentaires seulement. SSO interprojets Vercel encore bloqué : amont **302** et BFF **502**, Trusted Sources PATCH **404**. **W01 NO-GO, D11 OPEN, aucun merge ni déploiement Production.** Next : exécution E2E hébergée après règle Preview→Preview Vercel, revue indépendante, puis CI SHA final et intégration.

## D11 Importer — garde DEV pour coffre audit-only (19/10/2026)

**BEFORE :** dans `features/import/import_screen.dart` le bouton « données démo » était visible dans toutes les sessions Flutter `kDebugMode`, y compris avec coffre `PatientVaultScope.nativeDjango()`, et son action `_seedDemo()` appelait `AppDatabase.seedDemoData()`. Avec la sécurité D11, cette écriture était refusée avant suppression des données, mais l'interface restait bloquée sur `_seeding=true` en cas d'exception.

**Goal observable :** patient authentifié en debug : **aucun bouton DEV** ; audit isolé : bouton DEV visible et utilisable ; toutes les exceptions rétablissent l'état de chargement. Zéro changement de design de la version Web **Release**.

**Implémentation :** contrôle `kDebugMode` **ET** `db.patientVaultScope.databaseName == PatientVaultScope.auditOnly().databaseName` dans le rendu, vérification identique avant la transaction, `try/catch/finally` pour restaurer le bouton. Garde Drift demeure l'autorité finale. **AFTER à vérifier** : nouveau widget test `frontend/test/services/d11_import_demo_visibility_test.dart` exerce les vrais widgets à viewport 390×844 : patient natif sans `DEV`, audit-only avec `DEV`, absence d'exception. Nouveau test rattaché au workflow `dashboard-responsive-visual-cert.yml` avant les captures.

**État de preuve :** tests ajoutés au code au HEAD `41a75532c2f0379d720d0ebcd3954b4a7e21f294`, **résultat CI non encore constaté au moment de cette note**. Référence visuelle des 54 PNG avant correction globale : `39251988081`, après lot global `39253126717`, score SSIM moyen 99,9935 % sur code `4d789707`; **ne pas attribuer ce score à la nouvelle version tant que sa capture Chrome n'est pas vérifiée**. W01 NO-GO, D11 OPEN, aucun merge/Production.

**Next exact :** vérifier CI nouvelle branche, diagnostiquer et corriger si échec, confirmer Release Web visuellement identique, mettre à jour SHA/rapport ; le gate Hosted Preview→API exige toujours Vercel Trusted Sources Preview→Preview.

## D11 — clôture de la sous-validation Import et 9 workflows (19 octobre 2026)

**Goal exact** : une session patient n'affiche pas l'action « DEV données fictives » et un échec de seeding n'immobilise pas le bouton ; le coffre d'audit, distinct des coffres cliniques, conserve son jeu visuel synthétique. **SUCCESS observable (sous-lot uniquement)** : widget patient sans bouton, widget audit avec bouton, aucun appel seeding patient, 9/9 certifications visuelles passées. **Preuves** :
- SHA de code **`41a75532c2f0379d720d0ebcd3954b4a7e21f294`**, branche `test/w02-d11-vercel-preview-20261019` ; PR #1131 reste Draft, aucun merge.
- **9/9 workflows Actions `SUCCESS` sur ce SHA** : Dashboard responsive run `39263024128`, UI browser screenshot `39263024434`, CGM browser `39263024487`, Onboarding Chrome `39263024159`, First-use `39263024458`, P7 `39263024135`, Reports `39263024418`, Global routes `39263024139`, UI geometry `39263024388`.
- Dashboard run : **8/8 Flutter D11 PASS**, incluant deux tests widgets `d11_import_demo_visibility_test.dart` dans un viewport 390×844 (patient natif 734 : DEV invisible ; auditOnly : DEV présent), **3/3 Django D11 PASS**, **15/15 Dashboard contracts PASS**, 9 captures Chrome top/mid/lower sur trois viewports, toutes différentes. `ImportScreen._seedDemo()` ne peut plus modifier un coffre patient ni laisser un spinner bloqué si une exception survient.
- Relecture indépendante des chemins de code D11 : **13/13 source assertions conformes** (login FR/MENA, client API, Import, seeding Drift, backend Django, six fixtures audit-only).

**Comparaison visuelle BEFORE→Goal→AFTER, dernière itération** :
- Référence BEFORE : run Chrome `39253126717` sur code `4d789707`, 18 surfaces × trois viewports `390×844 / 768×1024 / 1280×900` ; AFTER run `39263024434` sur code `41a75532` ; six archives PNG recoupées par SHA-256, script reproductible `IAMINA_D11_visual_compare_latest.py` et JSON `IAMINA_D11_visual_latest_2026-10-19.json` dans la conversation.
- **54 paires** même noms, même pixels/dimensions. SSIM global moyen **0,994942887**, minimum **0,906395563**, **3/54 sous 0,98** : exclusivement les trois vues **Journal**.
- **Cause documentée des trois écarts temporels** : méthode `AppDatabase.seedDemoData()` crée des lignes de démo audit avec `loggedAt` fixé dans la journée et filtre `if (loggedAt.isAfter(now)) continue`. Les deux captures sont de la même date mais de part et d'autre du créneau fictif déjeuner **13 h 03** ; un nouveau log **115 mg/dL / 4 U** est donc visible seulement dans le second run. L'entrée « en direct » est volontairement `DateTime.now() - 2 min`, donc son horodatage varie aussi. **C'est une différence d'état des données synthétiques**, pas une preuve de changement de mise en page ou d'injection dans un patient.
- **51 vues sans cette variation de données** : SSIM moyen **0,999438914** (99,9439 %), minimum **0,994361039** (99,4361 %), **0/51 sous 0,98**, pixels modifiés moyens **0,0385458 %**. Pas de score de perfection sur les trois Journal. Pas de nouveau mockup ou changement visuel en Release ; le bouton DEV n'existe que dans un build debug sur auditOnly.

**Vercel** : déploiement Web Preview manuel `dpl_8v69xWz2FaURzoVjJnNitb16rSp4` sur SHA documentaire `4f40749228747f1448a7a6448b287cb1202ec66e` (code identique à `41a75532`), état **BUILDING** à la dernière observation, SSO conservé ; sans changement API, Production ni Neon Production. **Gate d'intégration externe toujours ouvert** : Web BFF reçoit amont **302** puis renvoie **502** par conception ; règle Vercel Trusted Sources `iamina-review Preview → iamina-certified Preview` refusée **HTTP 404** par API plateforme, nécessite un administrateur/Support Vercel. Aucune session utilisateur réelle / clinique / E2E A→B→A réalisée.

**Verdict** : sous-lot D11 « import debug invisible patient + CI/UI testées » **validé** ; **D11 complète OPEN**, **W01 NO-GO**, PR #1131 Draft, zéro D certifiée terminée. **Next** : état READY + GET Web Preview sur le nouveau déploiement ; intervention Trusted Sources, puis test Chrome authentifié synthétique A→B→A / compte neuf vide et revue sécurité indépendante avant W01 GO et toute intégration.

## Closeout technique vérifié — nouveau Vercel Preview D11 (19/10/2026)

**Résultat :** le déploiement manuel `iamina-review` **`dpl_8v69xWz2FaURzoVjJnNitb16rSp4` est READY** sur commit documentaire `4f40749228747f1448a7a6448b287cb1202ec66e` (code identique à **`41a75532c2f0379d720d0ebcd3954b4a7e21f294`** : 9/9 workflows CI SUCCESS, tests D11 Flutter 8/8, Django 3/3, Dashboard 15/15). URL : `https://iamina-review-l70o1te8q-achraf-benmoussa-s-projects.vercel.app`. Cible Vercel : **Preview (target null)**, branche `test/w02-d11-vercel-preview-20261019`. Aucune promotion Production.

**Preuve HTTP du déploiement final :**
- Web `GET /` → **200 HTML**.
- API Django Preview existante `GET /api/v1/health` → **200 JSON**, `status=ok, db=ok, cache=unavailable` ; cache toujours dégradé sans bloquer GET santé.
- Web Preview `GET /api/v1/health` → **502**. Log serveur `2026-10-19T14:05:45.159Z`, request `kvbwp-1792418744957-52eb04172bd5` : `IAMINA_W01_PREVIEW_UPSTREAM_GATE {category:'redirect', status:302}`.
- Web Preview `GET /api/v1/demo/scenarios` → **502**. Log serveur `2026-10-19T14:05:48.829Z`, request `w58bq-1792418748748-14598013dd92` : même `redirect,status=302`.
- Le BFF refuse donc correctement la redirection amont et retourne **502 fail-closed**. Il n'y a pas de preuve de succès d'accès interprojets à l'API sous Trusted Sources. Les jetons, chemins patients, corps des requêtes et URL de redirection ne sont pas journalisés.

**État UI/UX :** les **54 captures de l'avant-dernier et dernier run Chrome** ont été comparées. Global brut SSIM moyen **0,994942887**, mais trois vues Journal ne sont pas de même état temporel (source audit demo `if (loggedAt.isAfter(now)) continue` ; lecture fictive de midi passée entre 2 captures). Les **51 surfaces comparables** : SSIM moyen **0,999438914**, min **0,994361039**, 0 sous 0,98 ; images et JSON SHA-256 vérifiables via script `IAMINA_D11_visual_compare_latest.py` et rapport `IAMINA_D11_visual_latest_2026-10-19.json` fournis dans la conversation. Les 3 écrans Journal nécessiteraient une horloge fixe pour une comparaison image à image rigoureuse, mais **la cause de différence est documentée et indépendante d'une modification de layout**.

**Verdict de ce lot : sous-validation code, tests et interface D11 réussie, pas la D complète.** **W01 NO-GO ; D11 OPEN ; PR #1131 Draft non fusionnée ; aucun déploiement Production/Neon Production.** Deux human gates : (1) configurer Vercel API `Trusted Sources` exclusivement `iamina-review Preview→iamina-certified Preview`, toujours API PATCH **404**, par administrateur ou Vercel Support ; (2) arbitrer séparément le chiffrement / récupération du coffre Web W02 (voir `docs/assessments/2026-10-15-w02-web-vault-evidence.md`). Après gate 1 : Chrome E2E sous SSO sur comptes A/B synthétiques, nouveau compte zéro donnée démo, logout, logs, erreurs ; revue sécurité indépendante ; W01 GO avant tout merge. **0 D entièrement terminée ou certifiée.**


## D10 — owner-bound Web app-lock patch and local evidence (19/10/2026)

- **Goal:** remote verified account B must not unlock/recover an existing Web lock belonging to A; owner marker corruption and legacy ambiguity fail closed without erasing the patient vault.
- **Candidate:** `frontend/lib/services/app_lock_service.dart` persists `iamina_app_lock_native_owner_v1` with the native Django account id when available; `unlock()` and `recoverWithVerifiedRemoteAccount()` check that owner before using WebAuthn or removing lock material. No changes to W01 or production. Flutter tests now include verified remote B (synthetic HTTP 200 and valid-shaped token, Django user id 735) trying to recover A (owner 734), plus missing/corrupt owner and mismatched unlock.
- **Proof:** isolated Vercel sandbox `sbx_6QHlgHydFP4FyD4sl02id0CGs61P` checked out exact W02 test HEAD `a1de5b3614f58b1221885e5eaec3ead1335845d0`, Flutter 3.41.0: `flutter test --reporter expanded test/services/app_lock_service_test.dart` **22/22 PASS**; `flutter analyze` for the app-lock service and its test **exit 0**. Dart formatter ran locally before tests; formatting is **not yet committed**. Test runs were synthetic; they do not establish hosted login or actual passkey verification.
- **CI gate:** GitHub workflow `.github/workflows/w02-web-vault-a-b-a-browser.yml` now includes D10 tests. At earlier HEAD `b3680db1`, zero workflow runs were reported by GitHub; verify workflow registration and CI on latest HEAD before GO.
- **Remaining high-risk gap:** legacy locks lack an owner marker. Under a native authenticated account the patch refuses silent adoption; in recovery mode with no owner it refuses reset. This is safe for isolation but can **strand legitimate existing users**. Migration must be explicitly specified, tested with old real data and owner proof, without deleting or reassigning local vault. **D10 stays OPEN / NO-GO.**
- **Next:** make migration/recovery non-destructive and owner-authenticated; run complete Flutter Web/real Chrome with native accounts A→B→A, then exact-SHA CI and independent review. No Production deployment or merge.
