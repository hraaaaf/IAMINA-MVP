# IAMINA V1-03 — SSE production deployment drift + isolated DRAFT hotfix (#938)

Date : **2026-10-11**. Scope : audits **read-only** GitHub + metadata Vercel et préparation d'une branche corrective **NON fusionnée**. Pas de patient réel, pas de lecture de logs réels, pas de modification/deploy Vercel.

## Goal / Succès / Preuve

**Goal :** ne plus construire ni accepter l'ancienne URL `GET /api/v1/ai/chat/stream?message=...` contenant un texte patient. Préserver l'authentification, la protection CSRF des sessions, la sécurité déterministe des urgences et un contrat SSE consommable.

**Succès observable, non encore atteint en production :**
1. Frontend réellement servi : `POST` corps JSON `message/context_days` et **aucune** donnée patient dans la query.
2. Backend réellement servi : `POST` uniquement ; `GET?message=` retourne 405 sans redirection ni provider.
3. Urgence sur POST : SSE canonique `is_emergency=true`, après auth/CSRF, sans provider, `no-store`.
4. Aucun logger applicatif de triage ne capture extrait de message, identifiant patient ou exception contenant PHI.
5. CI exacte du candidat verte ; essais synthétiques en conditions de déploiement et contrôles d'ingress/retention effectués. Versions PWA installées / web cache et clients natifs connus ; stratégie d'upgrade validée.

## Preuve de drift réel GitHub ↔ Vercel

Lecture de `list_deployments(target=production)` et de `get_deployment` authentifiés :
- **Backend `iamina-certified`** : dernier déploiement marqué production `dpl_7SogpUMHNHd9rF7s7rfALccKduv7`, état READY, **2026-10-02**, Git commit `df004bcb25d2ae5c9004825ebee092306696b9e5` (branche main au moment du déploiement). Une preview créée plus récemment sur `preview/intent-envelope-v1-demo` ne doit PAS être confondue avec ce déploiement production.
- **Frontend `iamina-review`** : dernier déploiement marqué production `dpl_CJpLFLEQngvjsZXj23FinoXYoH1t`, état READY, **2026-10-08**, Git commit `1e44ba57ad63638b1eb15af916adc54d0f8c15fc`.
- **GitHub `main`** : `13b7cce12c86daf60119fb703f22e8c6c192cf8d`, pas égal aux SHAs des deux déploiements production. Les PR #932–#937 sont DRAFT non fusionnées.
- **Code exact backend déployé :** `backend/ai/api/v1/ai.py` contient `@router.get("/ai/chat/stream")` et `def chat_stream(request, message: str, context_days: int = 14)`. Le header documente `GET ...?message=...`.
- **Code exact frontend déployé :** `frontend/lib/services/api_client.dart::chatStream` fait `.replace(queryParameters: {'message': message})` puis `http.Request('GET', uri)`. `frontend/lib/features/journal/widgets/amina_chat_view.dart` consomme le stream.
- **Câblage** : `frontend/vercel_build.sh` (revu à #934) pointe le build Vercel `iamina-review` vers `https://iamina-certified.vercel.app`. `backend/vercel.json` au commit backend live redirige `/(.*)` vers `/api/index.py`, appli Django ; `frontend/vercel.json` ne sert que la SPA. `root/vercel.json` a `git.deploymentEnabled=false`, alors que le backend Vercel a sa configuration spécifique. L'endpoint SSE peut donc arriver à l'ingress Vercel du backend, sans que les routes projet vides prouvent le contraire.

**Conclusion prouvée :** le **code associé aux deux déploiements production** permet/forme encore une URL contenant le message patient. Cela crée un risque de présence de PHI dans URL/logs; **aucune donnée réelle ni divulgation n'a été vérifiée**. Contrôler les fichiers sources ne prouve pas que des appels ont effectivement eu lieu, ni que toutes les requêtes ont été journalisées. Ne pas minimiser le problème comme simple legacy inactif.

## Deuxième faille révélée par contre-revue de migration POST

Dans `main/backend/core/middleware/triage_vital.py`, `_log_emergency` écrit `user_id` et `message[:120]` dans `logger.critical`. Le passage du SSE à POST traverse en plus `TriageVitalMiddleware._is_chat_endpoint` : sans adaptation, un POST urgent est intercepté **avant l'authentification de l'endpoint** et renvoie une réponse JSON que le client SSE ne peut consommer. Ces faits sont supportés par le code source main. Ce log peut exposer du texte de santé aux collecteurs applicatifs ; la présence de tels enregistrements est **UNKNOWN**.

## Correctif préparé sans merge

**[PR DRAFT #938](https://github.com/hraaaaf/IAMINA-MVP/pull/938)**, base **main** (évite de mélanger les PR #932–#937) :
- `backend/ai/api/v1/ai.py` : `POST ChatRequest` JSON ; CSRF explicite pour cookie session, y compris Bearer forgé ; `ai_egress_scope` reconstitué pour chaque `next()` SSE ; `no-store`, pas d'exception brute dans les logs ; urgence canonique `compose_emergency_for_patient(...).as_stream_event()`, sans appel provider.
- `frontend/lib/services/api_client.dart` : builder POST JSON avec URL sans message, SSE accepté.
- `backend/core/middleware/triage_vital.py` : ne pré-intercepte pas le chemin SSE ; laisse passer la requête à Ninja pour **auth/CSRF avant la branche urgente**, et retire extraits de texte et user_id de `_log_emergency`. Les autres urgences nonstream conservent leur voie déterministe.
- `docs/api/openapi.json` : opération `post` only, `ChatRequest` dans requestBody, retirée query `message`.
- Tests : `backend/core/tests/test_v1_03_legacy_sse_no_provider.py` (repris de #935), `backend/core/tests/test_v1_03_sse_hotfix_flow.py` (synthetic HTTP POST, malformed body, urgence/auth/CSRF/logs) et `frontend/test/services/v1_03_sse_privacy_contract_test.dart` (repris de #932).

**État du test :** invariants de source ciblés contrôlés ; **CI exacte HEAD #938 lancée, initialement pending/in_progress**, résultat final NON encore établi. Aucun test sur Vercel de cette branche, aucune modification du runtime déployé, aucun merge.

## Gates restants, dont l'ordre importe

1. Achever la validation de la **PR #938 exacte** via CI, corriger toute régression et tests de sécurité. `openapi.json` est aligné statiquement, mais la commande `export_openapi` n'a pas encore été exécutée en local.
2. Revue adversariale indépendante privacy : logs Python/Django, proxy, Vercel edge/log drains, CDN, APM et rétention/historique (inconnus; `list_drains` renvoie 404, **pas** « zéro drain »). Audit autorisé sans faire remonter de PHI dans les tickets.
3. Inventaire distribué PWA/iOS/Android/versions réelles (GitHub releases listing vide n'établit pas l'absence d'apps distribuées). Tester upgrade PWA cache et local-first/offline avec valeurs **synthétiques** uniquement.
4. Définir une fenêtre opérationnelle coordonnée : l'ancien frontend produit la query **avant** toute réponse 405 ; un correctif backend seul n'efface pas l'historique d'ingress ni ne met à jour un ancien client. Les deux ordres frontend/backend ont une période possible d'incompatibilité SSE. Conserver l'accès à la voie déterministe d'urgence hors stream et communiquer une dégradation sûre.
5. **Human gate explicite :** autorisation pour tout merge, Vercel production/preview deploy ou traitement d'éventuels logs de production ; pas de passage silencieux à V1 clinique.

**Status :** `OPEN — HOTFIX DRAFT, NOT_DEPLOYED, NOT_RELEASE_AUTHORIZED`.

## Distribution : traces source ≠ parc réellement installé

Le dépôt GitHub `hraaaaf/IAMINA-MVP` renvoie **zéro GitHub Release** dans la liste interrogée et **aucune latest Release** (HTTP 404) à la date de l'audit. Il serait incorrect d'en déduire l'absence d'un déploiement web, d'APK partagé hors GitHub ou de distribution Apple/Google.

Inventaire des workflows `main` :
- `.github/workflows/pilot-ios-packaging.yml` valide un `flutter build ios --release --no-codesign`. C'est une compilation, **pas** une distribution TestFlight/App Store.
- `.github/workflows/pilot-mobile-packaging.yml` construit et vérifie un **debug APK** `flutter build apk --debug` ; cela ne prouve pas de release Play Store.
- `.github/workflows/p5-android-cloud-upgrade-rehearsal-v2.yml` signe temporairement des APK N-1/N avec un **keystore CI non-production**, lance un émulateur et supprime les APK/clefs en fin de job. Ce n'est pas une preuve d'installation/upgrade de clients utilisateurs.
- `.github/workflows/p5-4a-pwa-update-recovery-proof.yml` utilise un serveur et des releases simulées en CI pour tester le recovery PWA. Ce n'est pas une preuve du cache des navigateurs réels installés.

**Gate non comblé :** obtenir via les contrôles de distribution autorisés (et sans identifiants personnels) le nombre par version et plateforme, la version/service worker effectivement servie, l'âge des caches et les éventuels clients continuant à envoyer du GET, avant toute affirmation de migration complète. Le passage du site review vers POST pourra dégrader les clients PWA non actualisés ; le backend 405 protège le traitement mais **pas l'URL émise par un ancien client**.

## Contre-audit d'intégration de la pile DRAFT — ne pas fusionner naïvement

GitHub `compare_commits(main 13b7cce1 → head)` confirme :
- #938 : **10 commits / 7 fichiers** par rapport à `main` (hotfix autonome et tests, pas clinique V1 entièrement intégré).
- #932 : **101 commits / 59 fichiers** par rapport à `main` ; contient déjà un changement SSE POST et des modifications OCR / gardes provenant de sa longue base ancestrale.
- #934 : **141 commits / 72 fichiers** par rapport à `main` ; contient les changements locaux de consentement/opt-out.
- #937 : **113 commits / 65 fichiers** par rapport à `main` ; garde la dormance des aliases P3.

**Fichiers qui se chevauchent entre #938 et les ancêtres DRAFT :** `backend/ai/api/v1/ai.py`, `backend/core/middleware/triage_vital.py`, `frontend/lib/services/api_client.dart`, `docs/api/openapi.json`, `frontend/test/services/v1_03_sse_privacy_contract_test.dart`. La suite de tests GET legacy de #935 est également reprise dans #938.

**Décision technique recommandée après human gate :** ne pas traiter un merge vert de #938 comme validation de #932–#937. Conserver les garanties les plus restrictives de chaque version lors d'une réconciliation ultérieure : POST JSON sans query, CSRF cookie même Bearer, urgence canonique SSE **après** auth, pas de log PHI, dormance P3, opt-out local persistant, gardes egress. La variante #932 intercepte les urgences SSE dans le middleware ; la variante #938 choisit d'abord Ninja auth/CSRF : comportement volontairement différent, à tester explicitement avant toute déduplication. Faire valider la CI sur **chaque HEAD d'intégration** et les comportements end-to-end, sans attribuer à #938 des protections qui restent seulement dans #932–#937.

**État immuable :** #938 est DRAFT, n'a pas été merge ni déployée. Un feu vert CI ne constituerait pas l'autorisation Vercel ni la preuve des migrations de clients réels.

## CI #938 — échec diagnostiqué et reprise corrective (2026-10-11)

Au HEAD #938 `9e7ca998e0666cebb6367bfabc2d3099d8f4da67` (run GitHub CI `38184659246`, job backend `114604378730`) : lint, anti-bypass LLM, anti-bypass egress, Bandit et synchronisation OpenAPI **passés**. Pytest a exécuté **2 781 passed, 3 failed, 5 skipped, 3 xfailed**, avec 121 subtests. Échecs détaillés :

1. `core/tests/test_input_safety.py::test_sse_urgent_fast_path_does_not_initialize_iamina` et `::test_sse_insulin_fast_path_does_not_initialize_iamina` — tests unitaires historiques appelaient directement `ai.chat_stream(request, "urgence"/"dose")` selon la signature GET ancienne ; `data.message` POST provoque `AttributeError`. Le code applicatif ne doit **pas** réintroduire GET pour satisfaire ces tests. Correction tests : `RequestFactory().post` + `ai.ChatRequest`, et composer urgent simulé pour rester non-patient/DB-free.
2. `core/tests/test_v1_03_sse_hotfix_flow.py::test_session_post_rejects_missing_csrf_despite_spoofed_bearer` — **défaut réel** : HTTP 200 au lieu de 403. Investigation source : `amina/middleware/csrf_exempt_api.py` attribuait `_dont_enforce_csrf_checks=True` dès présence d'un header Bearer, même avec session cookie. Résultat : le contrôle manuel `check_iamina_csrf` ne suffisait pas à contrer la dispense effectuée plus tôt. Correction : ne dispenser Bearer du CSRF **qu'en absence de cookie de session** ; préserve l'exception bootstrap Firebase. Régression multi-routes synthétiques : account, logs, profile, chat et stream avec Bearer falsifié + cookie doivent tous répondre 403, tandis que session + vrai CSRF doit atteindre validation JSON.

**Nouveau HEAD #938 : `cbddb5621af3e82ac63ca6b98cbaa72ef82fe4eb`**, 10 fichiers modifiés/ajoutés. Nouveaux runs GitHub Actions lancés, initialement pending/in_progress. **Ne jamais réutiliser le verdict de `9e7ca998` pour `cbddb562`**. Les 3 échecs connus ont une correction ciblée poussée ; aucun verdict test final encore prouvé à cette étape.

**Preuve cross-check sécurité clinique :** `backend/core/middleware/emergency_operating_mode.py` possède un garde de sortie SSE `_sanitize_stream` ; il ne déduit pas l'urgence depuis le corps POST (utilise `request.GET`), d'où la nécessité maintenue de produire l'événement urgent canonique directement dans `chat_stream`. Les tests HTTP urgents sur cookie/no-cookie sont la preuve de comportement ciblée, pas une validation clinique humaine ni screenshot BEFORE/AFTER.

**Risque restant :** l'ensemble de la pile DRAFT possède d'autres changements CSRF. Avant intégration, résoudre ces interactions et rejouer la matrice entière à l'exact HEAD. Aucun déploiement autorisé.

## Runbook de cutover proposé — NON autorisé, NON exécuté

**Avant human gate :** aucune requête de test sur des comptes patients, aucun déploiement de preview ou production sans autorisation. La politique privacy de journalisation des URLs au **backend certified**, CDN/WAF/APM et drains/rétention doit être caractérisée **sans extraire de PHI** ; config inconnue jusqu'à preuve. Vérifier l'état des clients PWA caches/service workers et les versions natives installées. Obtenir revue juridique/privacy et clinique pour une éventuelle vérification des anciens logs, puis traiter les journaux sous procédure formellement autorisée.

**Si autorisation explicite de test synthetic preview reçue :** valider d'abord par test sans patient le 405 legacy sans Location, le POST JSON sans query, session+Bearer spoofé 403, cookie+CSRF valide traité, urgence canonique SSE avec `is_emergency` et sans LLM, absence de texte test dans les logs autorisés. Établir BEFORE/AFTER **aux mêmes viewports** pour urgence/chat, comportement en offline/PWA reconnecté, et vérifier que la disponibilité ne repose pas sur l'ancien GET.

**Si et seulement si merge ET déploiement séparément autorisés :** préparer simultanément artefacts backend/frontend avec SHA et version explicites ; respecter la fenêtre contrôlée et l'éventuelle dégradation de la messagerie SSE pendant la bascule. Préférer un fallback local déterministe connu plutôt que dégrader la confidentialité par une redirection ou restauration GET. Les clients périmés peuvent encore former une URL patient **avant** le 405 : communiquer l'upgrade, évaluer cache purge et bloquer la collecte des URL de cette route au plus en amont possible. Faire un smoke synthétique exact déploiement, vérifier métriques non PHI et faire approuver le closeout. En cas de régression, ne pas rebasculer silencieusement vers une version qui accepte le message dans l'URL.

**Human gates distincts :** (1) accès/revue des logs ou appareils réels ; (2) merge ; (3) déploiement Vercel. Un CI vert autorise seulement une étape de revue technique.

## Contre-validation deuxième run — protection pré-Ninja (2026-10-11)

Le run CI `38184949625`, job `114605240652`, HEAD #938 `cbddb5621af3e82ac63ca6b98cbaa72ef82fe4eb`, confirme l'évolution : **2 786 tests réussis, 5 sub-échecs, 5 skips et 3 xfail**. Les 2 tests directs à signature GET et le contrôle CSRF du POST valide avec Bearer forgé ont cessé d'échouer ; les 5 **nouveaux** sous-tests de matrice ont montré que les corps JSON malformés de routes protégées étaient encore acceptés jusqu'à validation de schéma (422/404 au lieu de 403). Il ne s'agit **pas** d'un simple artefact de test ; le contrôle de session devait être centralisé **avant** toute validation Ninja pour les requêtes mutatrices.

Après **deux runs avec échec de la même zone**, changement de stratégie : reprise à l'identique des 2 implémentations de la pile #932 **déjà passée en CI sur son HEAD** :
- `backend/amina/middleware/csrf_exempt_api.py` : vérification `check_iamina_csrf` **en entrée du middleware** si session cookie + méthode unsafe sous `/api/v1/`, avant `get_response`/Ninja, avec exception existante de la route de login public. Bearer ne peut dispenser du CSRF si un cookie de session existe.
- `backend/amina/vercel_session_auth.py` : `SessionAuth._get_key` vérifie explicitement le CSRF sur les appels unsafe avec cookie ; `check_iamina_csrf` évite l'ancienne exemption Bearer falsifiée.
- Les tests synthétiques de la matrice 5 routes ajoutés à #938 restent inchangés ; ils doivent maintenant prouver la protection **avant** validation de schéma, plus la compatibilité avec cookie + bon token.

La copie de référence a été confirmée par **égalité des SHA blob** avec #932, pas par une reformulation. Nouveau HEAD hotfix **`e2bbb9a34fccf643c62d329641217648522e7f41`**, 11 fichiers. Quatre nouveaux workflows déclenchés au HEAD, initialement `queued/in_progress` ; la CI de ce HEAD **n'est pas encore déclarée verte**. Ce changement de middleware est transverse, et doit être retenu comme risque de non-régression de toutes les routes protégées, publiques et de l'auth mobile, non pas traité comme une simple correction SSE.

**Ni les 2 786 tests du HEAD précédent ni le succès CI #932 ne remplacent la preuve CI exacte pour #938.** Aucun merge, Vercel ou consultation PHI.

## Dernière revue de la matrice d'authentification (2026-10-11)

Troisième perspective indépendante du simple test SSE : portage **octet pour octet** de `backend/core/tests/test_v1_03_cross_route_csrf.py` depuis #932 (blob SHA `f8e8e180d5beda31c420f22b3344c8cae803fbaa`) vers la PR isolée #938. Ses **10 tests** couvrent la matrice cookie sans CSRF, faux Bearer, cookie+CSRF valide, native Bearer uniquement (sans cookie), re-login public et inventaire OpenAPI des routes unsafe réellement montées. Motif : une correction CSRF transverse doit aussi démontrer l'absence de régression d'authentification mobile et des routes publiques, pas seulement refuser un paquet synthétique. La réussite de ces tests **dans #932** est un indice de référence, pas un verdict pour #938.

**HEAD #938 après portage : `1461e31419920459292d059819ffeced8f6c57fa` (12 fichiers), PR DRAFT.** La preuve CI devra être collectée sur **ce HEAD exact** ; les runs précédents peuvent être annulés ou rester liés à un commit précédent. Aucune fusion ni déploiement autorisé.

## Reprise le 12 octobre — CI #38185369954 et diagnostic natif sans secrets

**Run terminé et ROUGE :** [CI #38185369954](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38185369954), HEAD exact `1461e31419920459292d059819ffeced8f6c57fa`. Les six jobs : scope/secret/PR-size/frontend réussis ; backend PostgreSQL et backend SQLite échouent sur leurs étapes pytest. Les workflows séparés migration Django, P5-5 et screenshots compagnon sont **verts**.

**Logs exacts :** job SQLite `114606510755` : 2 796 passés, 4 sous-échecs, 5 skips, 3 xfail ; PostgreSQL `114606510657` : 2 800 passés, 4 sous-échecs, 1 skip, 3 xfail. Ce sont **les mêmes quatre sous-cas** du test `ProtectedApiCookieCsrfTests.test_native_bearer_only_is_not_subject_to_cookie_csrf` : POST `/api/v1/account/consent`, POST `/api/v1/logs/batch`, PATCH `/api/v1/profile`, PUT `/api/v1/cgm/connection`. Un token natif généré et vérifié par `verify_native_token` en amont obtient HTTP `401` au lieu d'atteindre la validation de payload `422/404`. **Aucune autre panne testée n'a été observée dans ces deux jobs.**

Les scénarios de cookie session CSRF, spoof Bearer et URL POST SSE ne figurent plus parmi les échecs. Le test natif a été copié à l'identique de #932, où le run CI `38107828563` rapporte **2846 passed** sur son HEAD ; ce résultat **ne peut pas certifier** son comportement dans le hotfix isolé. Ne pas changer les 401 attendus en succès ni supprimer le test sans établir si l'auth natif est réellement inaccessible.

**Action diagnostique appliquée :** instrumenter **uniquement le test synthétique** `test_native_bearer_only_is_not_subject_to_cookie_csrf` pour enregistrer au besoin, sans valeur de jeton, si `HybridBearerAuth.authenticate` est appelée, si le jeton transmis correspond au jeton émis, si elle authentifie et si un cookie session est présent. La PR #938 reste DRAFT ; HEAD de diagnostic `7146ddd4ad74ac42fc1ef2f6872a0ecf79d8aa25` ; CI exacte nouvelle `38229702400` démarrée, initialement queued. Ce contrôle distingue problème de routage/authentificateur et problème de transport de Bearer ; **aucune cause racine affirmée avant lecture des résultats**.

Aucune donnée patient ni token réel n'est collecté dans l'instrumentation. Pas de merge, pas de déploiement Vercel.

## Root cause confirmée des quatre 401 : fixture globale d'auth trompeuse (2026-10-12)

**Preuve code croisée #938 ↔ #932 :** `backend/conftest.py` sur `main` installe une fixture autouse `_patch_firebase_auth` qui remplace `diabetes.api.v1.security.FirebaseAuth.__call__` par `_session_aware_call`, retournant `request.user` lorsqu'une session existe et `None` sinon. Or `FirebaseAuth = HybridBearerAuth` est un **alias de classe** dans `backend/diabetes/api/v1/security.py`. La fixture modifie ainsi **tous** les appels `HybridBearerAuth.__call__`, y compris les jetons IAMINA natifs valides. Les essais de bearer sans cookie dans les deux jobs backend du run `38185369954` échouent donc en 401 dans l'environnement **de test**. Cette défaillance n'est **pas la preuve d'une panne native identique en production**, et la solution n'est pas d'accepter 401 comme succès.

**Résolution robuste, déjà prouvée en amont :** `backend/conftest.py` sur #932 supprime le patch de l'auth et conserve uniquement la fixture autouse d'accès aux bases de tests `_legacy_suite_db_access(db)`. La CI complète #932 `38107828563` indique **2846 passed** au HEAD propre de cette branche. Cette implémentation et le test complet de matrice `backend/core/tests/test_v1_03_cross_route_csrf.py` ont été repris **exactement par SHA blob identique** sur #938. L'instrumentation de diagnostic temporaire du test a été supprimée après établissement de la cause (aucun jeton ni PHI consigné).

**Nouveau HEAD #938** : `beeed3ecb60b68a9a30b5a9d46736f9a6f520e4d` (13 fichiers). CI exacte **`38230019452`** et 3 workflows associés déclenchés automatiquement ; au premier contrôle, tous `queued/pending`. **Ne pas les déclarer verts sans preuve**. Aucune modification de production, merge ni Vercel.

**Recommandation sécurité :** conserver cette fixture non falsifiante comme garde : une suite intégration qui remplace l'auth hybride par une session trompeuse peut masquer des régressions d'auth natives et fausser des conclusions CSRF.
