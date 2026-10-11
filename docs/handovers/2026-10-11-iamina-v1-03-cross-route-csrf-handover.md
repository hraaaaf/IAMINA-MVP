# IAMINA — Handover canonique V1-03 / CSRF transversal #927 / PR #928
**Date de reprise : 2026-10-11.** Source d'autorité pour le statut global : `docs/ROADMAP.md`. Ce handover est celui du **sous-lot #928**, séparé du handover transport SSE #926.

## GOAL / succès / preuve
**Goal :** protéger toutes les mutations API authentifiées par cookie de session contre les CSRF (y compris faux Bearer) sans casser l'authentification native Bearer, les reconnexions web, les opérations urgentes ni le Dashboard.

**Succès observable (NON atteint) :** cookie sans CSRF → 403 ; cookie + Bearer falsifié → 403 ; cookie + CSRF valide → contrat route ; Bearer natif vérifié sans cookie → contrat route ; cas Bearer+cookie explicitement défini et testé ; routes publiques et réponses urgentes inchangées ; SQLite/PG + Flutter/PWA + Chrome + 15/15 GitHub exact-head ; revue sécurité/confidentialité indépendante.

**Preuve actuellement :** Chrome Dashboard visuel ✅ sur HEAD code, tests backend Bearer ❌. Aucun merge ni déploiement.

## Repo, branches, PR, HEAD
- Repo `hraaaaf/IAMINA-MVP`.
- Parent **DRAFT [#922](https://github.com/hraaaaf/IAMINA-MVP/pull/922)**, branche `security/v1-03-summary-local-only-20261010`, HEAD `cce2b5716d59add380846f3b3a18ef84e33fa41c`, non mergé.
- Intermédiaire **DRAFT [#926](https://github.com/hraaaaf/IAMINA-MVP/pull/926)**, branche `fix/v1-03-sse-post-scoped-20261010`, HEAD `05276ef08319dc4a79c50bbcd6063975c3e0e3af`, base parent #922, **15/15 exact-head CI GREEN** ([run #38086677013](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38086677013)). Validation du transport SSE, pas du CSRF transversal.
- Enfant **DRAFT [#928](https://github.com/hraaaaf/IAMINA-MVP/pull/928)**, branche `security/v1-03-cross-route-cookie-csrf-20261010`, HEAD *code testé* `1d399c5700999d6d350a70fb05e48060fdcd9a68`, base `main` **temporaire pour déclencher CI**. **Doit être rebasé par ciblage de PR (base branch) sur #926 après exact-head green, pas mergé.** Ce commit documentaire changera le HEAD et exigera sa propre CI.

## Modifications et preuves
1. Inventaire #927 : **15 fichiers de routeurs protégés**, **28 décorateurs POST/PUT/PATCH/DELETE dans 12 fichiers** (comptage statique partiel, ne constitue PAS 28 vulnérabilités). Un module enregistré remonte aussi le routeur des logs sous `/api/v1/diabetes/logs*`. `CsrfExemptApiMiddleware` exemptait tout en-tête ayant la forme Bearer *avant vérification* ; risque d'authentification mixte identifié.
2. Code enfant : `backend/amina/middleware/csrf_exempt_api.py` contrôle en amont le CSRF pour toute requête unsafe `/api/v1/` avec cookie de session, sans exempter un faux Bearer ; les clients Bearer sans cookie gardent le chemin exempté. Exception ciblée réintroduite pour **login public** `/api/v1/auth/login`.
3. Tests `backend/core/tests/test_v1_03_cross_route_csrf.py` : matrice Client(enforce_csrf_checks=True) compte/consentement, logs batch, profil PATCH et CGM PUT ; sans jeton 403 ; cookie/faux Bearer 403 ; cookie+CSRF valide atteint la validation ; Bearer natif sans cookie ; Bearer+cookie ; GET et reconnexion login ; entrées synthétiques sans modification patient par cas positif.
4. HEAD `1de9fa4` [CI #38091960885](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38091960885) ❌ Ruff I001 avant pytest ; corrigé par `ee04a84`.
5. HEAD `ee04a84` [CI #38092068836](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38092068836) ❌ backend SQLite/PG sur **4 sous-tests Bearer natif sans cookie** (401 attendu 422/404) ; négatifs et positifs cookie-CSRF passaient, frontend Flutter/PWA ✅. [Dashboard #38092068778](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38092068778) ❌ timeout : artefact navigateur et backend a établi login initial 200, reconnexion avec cookie 403 à cause de la nouvelle garde CSRF et de l'origine du proxy de test non reconnue.
6. HEAD code `1d399c5` [Dashboard #38092863710](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38092863710) ✅ sur la certification responsive après exemption du login public ; les autres routes sensibles restent protégées. [CI principale #38092863670](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38092863670) ❌, **14/15 workflows SUCCESS, 1 CI FAILED** : SQLite et PostgreSQL échouent chacun sur 4 sous-tests du même scénario natif. Le wrapper observateur a démontré **Authorization présente, aucun cookie, `HybridBearerAuth.__call__` appelé mais résultat faux, puis `SessionAuth.__call__` faux → 401**. Signature native `issue_native_token` → `verify_native_token` réussie dans ce test. La cause précise dans le callback HttpBearer/token parsing n'est PAS encore prouvée. Jamais écrire les jetons ou données patients dans les logs.
7. Politique **Bearer valide + cookie** : la garde actuelle exige CSRF même avec un jeton éventuellement valide. Risque de compatibilité PWA/mobile web qui conserve un cookie et envoie aussi Authorization ; décisions et preuves nécessaires. Ne JAMAIS relâcher le CSRF seulement sur la forme de l'en-tête.

## NEXT EXACT et chemin de clôture
1. Reprendre sur cette branche et le dernier HEAD ; vérifier PR #928 / #926, GitHub exact HEAD CI. Inspecter `backend/diabetes/api/v1/security.py`, `HttpBearer.__call__` django-ninja 1.7.1, le test `test_native_bearer_only_is_not_subject_to_cookie_csrf` et la chaîne Authorization complète **sans jamais afficher la valeur du jeton**. Comprendre pourquoi `HybridBearerAuth.__call__` retourne faux malgré la signature directement valide. Éviter de transformer le test en 401 attendu ou de contourner les protections.
2. Fix minimal ; tests ciblés SQLite+PostgreSQL : cookie seul manquant/faux/valide ; Bearer natif seul ; Bearer falsifié+cookie ; Bearer réel+cookie avec politique explicitement sécurisée ; connexion web/relogin ; GET ; urgence SSE.
3. **15/15 workflows GitHub exact-head** (backend, Flutter/PWA, Chrome Dashboard responsive, Android/iOS, visuels). En cas de rouge : logs → cause → patch → nouveau HEAD/CI ; ne pas clôturer sur CI queued/running. Ne pas lancer de benchmark lourd à l'aveugle.
4. Après green : mettre à jour ce fichier, `docs/ROADMAP.md`, PR #928 et issue #927, Notion ; faire certifier HEAD docs si nouveau commit. Rétablir **base #928 = `fix/v1-03-sse-post-scoped-20261010`**, comparer ahead/behind/diff, conserver DRAFT, aucune fusion.
5. Revue indépendante sécurité/compatibilité/auth, logs de proxy/ingress, routes générées, migration ancien GET SSE → POST et rollback. Gates humaines [#923](https://github.com/hraaaaf/IAMINA-MVP/issues/923) unité glycémie OCR et [#924](https://github.com/hraaaaf/IAMINA-MVP/issues/924) consentement local/global ; CNDP, processor, a11y, FR/AR/Darija-RTL et pilotes P5-6A/P5-6B. Aucun merge, déploiement Vercel ou usage patient sans autorisation.
6. Puis suite logique V1-01 audit calcul/autorité clinique, V1-02 Intelligence Engine, lots V1 restants selon `docs/ROADMAP.md`.

## Repères de roadmap
Décisions V1 : **29/29 approuvées, 0/29 entièrement livrées** ; V1-03 EN COURS. Ancien programme P5 : **6/12 lots atomiques clos = 50%**, métrique distincte. Référence Notion : [roadmap maître](https://app.notion.com/p/3f477c66336281b28c78eb11c22f5ee6).

**NON CERTIFIÉ sur #928 / NON MERGÉ / NON DÉPLOYÉ.** Le Dashboard est vert, le backend Bearer-only est rouge. Ne pas confondre succès parent #926 et succès enfant #928.
