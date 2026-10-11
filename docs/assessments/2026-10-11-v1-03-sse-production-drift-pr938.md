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
