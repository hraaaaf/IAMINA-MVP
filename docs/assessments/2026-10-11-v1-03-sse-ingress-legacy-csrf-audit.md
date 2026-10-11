# IAMINA V1-03 — Audit SSE, CSRF, logging et anciens clients

Date: 2026-10-11 | Baseline: `15cfe25fcc93fff00a1198d705fb683c7a2eb960` | Branche: `parallel/v1-03-sse-ingress-compat-audit-20261011` | Issues: #925 #927
Statut: **audit code/tests documenté, réseau ingress externe et anciens clients non validés**. Aucun déploiement ou test ingress live.

## Goal / succès / preuve
Goal: pas de texte patient en query/URL et pas de mutation cookie sans CSRF, préserver triage urgent et isolation de portée.
Succès: tests exact-head sur code + log-redaction ingress effectif + stratégie de compatibilité GET obsolète, avec preuve de rollback. Seul premier volet est documenté ici.

## Preuves vérifiées
1. `frontend/lib/services/api_client.dart:16-21,302-321` : `chatStream` envoie `POST /api/v1/ai/chat/stream` avec `message` **dans le JSON body** et non l'URL. `frontend/test/services/v1_03_sse_privacy_contract_test.dart` vérifie la construction. `backend/ai/api/v1/ai.py:396-414` sert POST, ajoute garde explicite CSRF quand cookie présent. `backend/core/tests/test_v1_03_sse_post_privacy.py:42-45` affirme que l'ancien GET à query renvoie **405**.
2. `backend/amina/middleware/csrf_exempt_api.py:30-60` vérifie le CSRF de toute requête unsafe `/api/v1/` avec cookie, avec une exception explicite **login public** `/api/v1/auth/login`, quel que soit un Bearer ressemblant; les clients purement Bearer bénéficient d'exemption sans cookie. `backend/amina/vercel_session_auth.py:17-49` et `backend/ai/api/v1/ai.py:410-414` apportent défense en profondeur.
3. `backend/core/tests/test_v1_03_cross_route_csrf.py` : matrice cookie, Bearer valide/falsifié, 28 opérations unsafe avec SessionAuth, endpoint login public; `test_v1_03_sse_post_privacy.py` : post/body, GET 405, urgences SSE, interruption de flux, scopes intercalés et non-fuite dans le logger des exceptions. Parent DRAFT #928/#926 et enfant #932 ont réussi leur CI exacte enregistrée (16/16 sur #932; [CI #38107828563](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38107828563)). Ce rapport ne relance pas les tests.
4. `backend/ai/api/v1/ai.py:530-552` borne `ai_egress_scope` autour de chaque `next(stream)` différé, sans le garder à travers `yield`; `logger.error` publie seulement `type(exc).__name__` dans l'exception SSE. `backend/llm/middleware/logging.py` revendique et implémente un journal de métadonnées, pas de prompts; `frontend/lib/services/api_client.dart` ne contient plus `CurlInterceptor`.
5. `backend/vercel.json` et `frontend/vercel.json` déclarent rewrites, mais **pas la politique réelle de logs CDN/proxy/edge, APM, WAF et durée de rétention**. `vercel.json` à la racine a `git.deploymentEnabled:false`. Ne pas inférer du code une suppression effective du corps HTTP dans l'outillage déployé.
6. L'ancienne URL `GET /api/v1/ai/chat/stream?message=...` est volontairement non prise en charge. Aucun inventaire prouvé des anciens clients déjà installés, ingress historiques ou stratégie de dépréciation; **risque de compatibilité**, pas une faille de sécurité actuelle prouvée.

## Verdict et gates
- **Vérifié (source + CI précédente):** transport POST-body en frontend canonique, GET bloqué, protections CSRF sur chemins montés et isolation scope testée synthétiquement.
- **Non prouvé:** masquage effectif de corps/headers chez hébergeur et intermédiaires; compatibilité versions clients antérieures; audit indépendante du login public et ancien clients.
- **NO-GO release:** preuve environnementale ingress et revue indépendante privacy/security toujours requises, aucun Vercel sans autorisation explicite.

## Next exact
1. Ajouter au harnais synthetic un test version ancienne GET=>405 + chemin d'upgrade/documentation, sans réactiver GET PHI.
2. Comparer de façon observable les règles de logging effectives, APM/WAF, proxy, redaction, retention et absence d'URL query PHI; accès réel/autorisation nécessaires.
3. Repasser CSRF login public, cookie+Bearer, SSE urgent, interruptions et ouverture scope sur tout changement; SQLite/PostgreSQL exact-head.
4. Coordonner avec #929 seulement si nouveaux chemins montés; sinon ne pas élargir la surface API.

## Complement technique — 2026-10-11
- Test adversarial ajouté : `backend/core/tests/test_v1_03_legacy_sse_no_provider.py`. Il caractérise le refus du GET ancien contenant un marqueur synthétique en query et l'absence d'invocation fournisseur.
- Pas de vérification des logs ingress réels ni des versions clients installées. Verdict CI exact-head à établir.

## Inspection Vercel en lecture seule — 2026-10-11
Via le connecteur Vercel authentifié, `list_projects(search="iamina")` a renvoyé exactement deux projets accessibles sous le même compte : `iamina-review` (`prj_AYaUi32KTDHak8I7dmdQpDrqd8SI`) et `iamina-certified` (`prj_Pn9FnyconF3h2w9gOU74iV98kJoU`). `get_project` confirme ces deux identifiants ; son payload minimal ne fournit **ni stratégie de journalisation ni politique de rétention ni config de logs CDN/proxy**. `list_drains(teamId)` a répondu **HTTP 404 `not_found`** : il est interdit d'interpréter cet échec comme l'absence de drains. Aucun log runtime potentiellement patient n'a été consulté, aucun secret lu, aucune configuration/deployment modifiée.

**Verdict de preuve corrigé :** vérification d'identité des projets uniquement. Pour vérifier la redaction réelle de query/body/headers et la rétention, un accès autorisé à la configuration et à un environnement synthetic dédié est encore nécessaire. Les 16/16 verts précédents portent sur le code/tests, non sur l'infrastructure Vercel.


## Prévention de régression des anciens GET SSE — 2026-10-11

**Goal** : si un ancien client envoie du texte synthétique dans l'URL `GET /api/v1/ai/chat/stream?message=...`, refuser sans réactiver le provider ni rediriger ce texte vers une autre URL ; annoncer dans l'OpenAPI le contrat de migration **POST JSON-body exclusivement**. Ce sont des tests d'API in-process, pas une vérification de logs de proxy ni une preuve d'inventaire de clients installés.

Deux tests ajoutés à `backend/core/tests/test_v1_03_legacy_sse_no_provider.py` :
- requête GET avec marqueur synthétique : HTTP **405**, **pas de Location** ni de reflet du marqueur dans la réponse ; `companion.core.IAmina` non instancié ;
- schéma `api.get_openapi_schema()` : `/api/v1/ai/chat/stream` annonce `post`, **pas `get`**, avec `requestBody.content.application/json`.

Le test initial GET 405 + aucun provider est conservé. **Sans changement runtime ni compatibilité GET réactivée**. Certifier ce nouveau HEAD en CI Django SQLite/PostgreSQL, puis restituer #935 à la base #932 ; n'inférer aucune politique CDN/WAF/log/retention depuis cette preuve. Avant release : analyser les anciens clients, concevoir une notification de version minimale ou migration côté client, et réaliser un audit ingress autorisé avec requêtes **strictement synthétiques**. Aucun déploiement Vercel, merge ni patient réel.
