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
