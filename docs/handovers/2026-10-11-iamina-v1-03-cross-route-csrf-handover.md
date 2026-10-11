# IAMINA — Handover canonique V1-03 / CSRF transversal #927 / PR #928
**Date de reprise : 2026-10-11.** Source d'autorité pour le statut global : `docs/ROADMAP.md`. Ce handover est celui du **sous-lot #928**, séparé du handover transport SSE #926.

## GOAL / succès / preuve
**Goal :** protéger toutes les mutations API authentifiées par cookie de session contre les CSRF (y compris faux Bearer) sans casser l'authentification native Bearer, les reconnexions web, les opérations urgentes ni le Dashboard.

**Succès observable (NON atteint) :** cookie sans CSRF → 403 ; cookie + Bearer falsifié → 403 ; cookie + CSRF valide → contrat route ; Bearer natif vérifié sans cookie → contrat route ; cas Bearer+cookie explicitement défini et testé ; routes publiques et réponses urgentes inchangées ; SQLite/PG + Flutter/PWA + Chrome + 15/15 GitHub exact-head ; revue sécurité/confidentialité indépendante.

**Preuve fonctionnelle validée :** SHA `509c7274` 15/15 verts avant la nouvelle modification de tests/docs. Aucun merge ni déploiement.

## Repo, branches, PR, HEAD
- Repo `hraaaaf/IAMINA-MVP`.
- Parent **DRAFT [#922](https://github.com/hraaaaf/IAMINA-MVP/pull/922)**, branche `security/v1-03-summary-local-only-20261010`, HEAD `cce2b5716d59add380846f3b3a18ef84e33fa41c`, non mergé.
- Intermédiaire **DRAFT [#926](https://github.com/hraaaaf/IAMINA-MVP/pull/926)**, branche `fix/v1-03-sse-post-scoped-20261010`, HEAD `05276ef08319dc4a79c50bbcd6063975c3e0e3af`, base parent #922, **15/15 exact-head CI GREEN** ([run #38086677013](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38086677013)). Validation du transport SSE, pas du CSRF transversal.
- Enfant **DRAFT [#928](https://github.com/hraaaaf/IAMINA-MVP/pull/928)**, branche `security/v1-03-cross-route-cookie-csrf-20261010`, SHA fonctionnel validé `509c7274cda2c3262e431b54a4ebcfc177b954b1`, base `main` temporaire pour la CI. Nouveau SHA tests/docs à vérifier, puis cibler #926 (non mergé).

## Chronologie des modifications et preuves (historique des anciens échecs)
1. Inventaire #927 : **15 fichiers de routeurs protégés**, **28 décorateurs POST/PUT/PATCH/DELETE dans 12 fichiers** (comptage statique partiel, ne constitue PAS 28 vulnérabilités). Un module enregistré remonte aussi le routeur des logs sous `/api/v1/diabetes/logs*`. `CsrfExemptApiMiddleware` exemptait tout en-tête ayant la forme Bearer *avant vérification* ; risque d'authentification mixte identifié.
2. Code enfant : `backend/amina/middleware/csrf_exempt_api.py` contrôle en amont le CSRF pour toute requête unsafe `/api/v1/` avec cookie de session, sans exempter un faux Bearer ; les clients Bearer sans cookie gardent le chemin exempté. Exception ciblée réintroduite pour **login public** `/api/v1/auth/login`.
3. Tests `backend/core/tests/test_v1_03_cross_route_csrf.py` : matrice Client(enforce_csrf_checks=True) compte/consentement, logs batch, profil PATCH et CGM PUT ; sans jeton 403 ; cookie/faux Bearer 403 ; cookie+CSRF valide atteint la validation ; Bearer natif sans cookie ; Bearer+cookie ; GET et reconnexion login ; entrées synthétiques sans modification patient par cas positif.
4. HEAD `1de9fa4` [CI #38091960885](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38091960885) ❌ Ruff I001 avant pytest ; corrigé par `ee04a84`.
5. HEAD `ee04a84` [CI #38092068836](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38092068836) ❌ backend SQLite/PG sur **4 sous-tests Bearer natif sans cookie** (401 attendu 422/404) ; négatifs et positifs cookie-CSRF passaient, frontend Flutter/PWA ✅. [Dashboard #38092068778](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38092068778) ❌ timeout : artefact navigateur et backend a établi login initial 200, reconnexion avec cookie 403 à cause de la nouvelle garde CSRF et de l'origine du proxy de test non reconnue.
6. HEAD code `1d399c5` [Dashboard #38092863710](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38092863710) ✅ sur la certification responsive après exemption du login public ; les autres routes sensibles restent protégées. [CI principale #38092863670](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38092863670) ❌, **14/15 workflows SUCCESS, 1 CI FAILED** : SQLite et PostgreSQL échouent chacun sur 4 sous-tests du même scénario natif. Le wrapper observateur a démontré **Authorization présente, aucun cookie, `HybridBearerAuth.__call__` appelé mais résultat faux, puis `SessionAuth.__call__` faux → 401**. Signature native `issue_native_token` → `verify_native_token` réussie dans ce test. La cause précise dans le callback HttpBearer/token parsing n'est PAS encore prouvée. Jamais écrire les jetons ou données patients dans les logs.
7. Politique **Bearer valide + cookie** : la garde actuelle exige CSRF même avec un jeton éventuellement valide. Risque de compatibilité PWA/mobile web qui conserve un cookie et envoie aussi Authorization ; décisions et preuves nécessaires. Ne JAMAIS relâcher le CSRF seulement sur la forme de l'en-tête.

## Dernière preuve et contre-vérification — 2026-10-11

**Goal :** garder l'ensemble des mutations d'API authentifiées par cookie protégées du CSRF, sans invalider Bearer-only et SSE urgent autorisé. **Succès :** réponse HTTP 403 avant toute mutation pour cookie unsafe sans CSRF, authentification Bearer native réelle, SSE d'urgence avec CSRF valide et absence d'appel LLM. **Preuve ancien HEAD :** SHA `509c7274cda2c3262e431b54a4ebcfc177b954b1`, [15/15 CI success](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38101620136), SQLite 2842 passed/149 subtests ; PostgreSQL 2846 passed/149 subtests ; Flutter 660 passed/1 skipped, PWA, Chrome, migration drift et Protected Shadow success.

**Cause racine prouvée :** une fixture pytest globale `autouse` dans `backend/conftest.py` remplaçait `FirebaseAuth.__call__` par `_session_aware_call`. `FirebaseAuth` étant l'alias de `HybridBearerAuth`, elle neutralisait le vrai Bearer sur toutes les routes. La suppression de ce mock (sans retirer le scope DB historique des tests) explique le 401 auparavant observé et l'apparence initiale d'un CSRF SSE non protégé. **Aucune vulnérabilité en production n'est prouvée par cette observation contaminée.**

**Perfection Pass et finding distinct :** le test HTTP de `/api/v1/diabetes/logs/batch` a retourné **404** (avec cookie+CSRF et Bearer natif) sur [CI #38102619725](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38102619725) **SQLite et PostgreSQL** ; l'OpenAPI ne contient aucune route `/api/v1/diabetes/*`. Cela contredit la promesse de montage par `ModuleRegistry`. Le résultat n'est pas assimilé à un passage sécurité : [issue #929](https://github.com/hraaaaf/IAMINA-MVP/issues/929) créée pour le vrai problème de routage, hors scope de ce PR sécurité. L'URL non montée est supprimée de la matrice de routes HTTP accessibles, sans modifier la production. Le test POST SSE urgent cookie sans CSRF 403 / avec CSRF valide 200 SSE déterministe sans LLM reste en place (succès visible sur la CI précédente). **La correction tests/docs est encore un nouveau SHA à recertifier 15/15 avant closeout.**

**Risques et gates OPEN :** au-delà des quatre familles de routes + alias, inventaire dynamique exhaustif encore à prouver ; compatibilité client Bearer+cookie, exception de login public, sécurité/origine/proxy/ingress, accès au triage d'urgence sans CSRF, revue réellement indépendante auth/privacy, demandes humaines #923/#924. Pas de fusion, de déploiement Vercel, ni d'usage patient.

**Scores techniques provisoires (revue contradictoire non indépendante) :** EXECUTION_SCORE 8.0/10, ADVERSARIAL_SCORE 7.8/10, écart 0.2, RETAINED 7.8/10 (plafond CI exacte manquante et finding #929 documenté) ; `NO-GO` / `OPEN` et non `VERIFIED`. À réévaluer après la nouvelle CI et revue indépendante.

## NEXT EXACT et chemin de clôture
1. Vérifier que la PR #928 pointe sur le nouveau SHA ; certifier **15/15 workflows du nouveau HEAD**. En cas de rouge : diagnostiquer → corriger → CI exacte, jamais contourner CSRF.
2. Contrôler le périmètre et risques persistants ; demander une revue humaine réellement indépendante de sécurité et privacy, plus arbitrages sur cookie+Bearer/login/triage ; faire clôturer les gates #923/#924 et release applicables.
3. Après CI exacte, corriger si nécessaire les documents canonique/Notion/PR et revalider nouveau SHA ; rattacher la base de #928 à `fix/v1-03-sse-post-scoped-20261010` (#926), contrôler diff et ahead/behind ; **conserver DRAFT et ne pas merger/déployer sans gate humain**.
4. Ensuite seulement certifieur indépendant et chemin merge/post-merge si explicitement autorisé ; V1-03 et toutes les 29 décisions non closes restent OPEN.

## Repères de roadmap
Décisions V1 : **29/29 approuvées, 0/29 entièrement livrées** ; V1-03 EN COURS. Ancien programme P5 : **6/12 lots atomiques clos = 50%**, métrique distincte. Référence Notion : [roadmap maître](https://app.notion.com/p/3f477c66336281b28c78eb11c22f5ee6).

**NON CERTIFIÉ sur #928 / NON MERGÉ / NON DÉPLOYÉ.** Le dernier SHA fonctionnel 509c7274 est 15/15 vert ; ce nouveau commit tests/docs demande sa propre CI et une revue externe.
