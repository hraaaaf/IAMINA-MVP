# IAMINA Web V2 — W01 hosted synthetic Preview smoke (17 octobre 2026)

## Goal, succès observable et preuve

**Goal :** déployer **Preview seulement** la Web Flutter et l'API Django reliée à la sandbox Neon synthétique, vérifier les deux artefacts, l'accès PostgreSQL et l'absence de mutation patient/Production, sans annoncer une certification clinique ou une release complète.

**Résultat vérifié : PARTIEL.** Deux déploiements Vercel Preview `READY`. L'API hébergée répond HTTP 200 avec `db=ok`; le frontend hébergé sert son HTML Flutter en HTTP 200 et son build embarque **l'URL unique de l'API Preview**, non l'alias stable. **Aucun test navigateur interactif Web→API**, aucun login patient, aucune écriture clinique. **W01 NO-GO, W02 GELÉ.**

## Autorisation et limites

Le propriétaire a donné explicitement « Go » à la proposition ciblée de déployer **Vercel Preview synthétique uniquement**, après résolution de Neon LOGIN. Le périmètre n'inclut **aucun déploiement Production, aucune donnée patient, aucun changement Neon Production, aucune activation `IAMINA_ENV=production`, aucune facture/upgrade, ni désactivation du SSO Vercel**.

## Preuves directes

| Contrôle | Identifiant / observation | Verdict |
| --- | --- | --- |
| Neon sandbox | projet `noisy-truth-00115950`; branche `br-sweet-frog-b9ok6ptp` (`synthetic-only`), base `iamina925_empty` | isolée du projet Neon IAMINA Production |
| Identité applicative Neon | `current_user=iamina_preview_app`, authentification SQL effective ; LOGIN=true, mot de passe présent, 5 privilèges admin false | PASS |
| ACL Neon | `public.USAGE=true`, `public.CREATE=false` ; 39 tables runtime CRUD, 2 métadonnées lecture seule, `django_migrations` sans droit | PASS |
| Pas de données patient en sandbox | `SELECT COUNT(*)` sur **chacune des 39 tables runtime** avec le rôle app : **0 ligne totale / 0 table non vide** après le smoke API | PASS à l'instant du contrôle |
| Backend Vercel Preview | projet `iamina-certified` / `prj_Pn9FnyconF3h2w9gOU74iV98kJoU`; déploiement `dpl_EYcpDXk1juYoYBxb3okkcCAkHd1X` ; source `c0192dedfe7f415d365322085036d8ab1a20be4d` ; state `READY` ; `target=null` (Preview) | PASS build |
| HTTP Django→PostgreSQL | `GET https://iamina-certified-n3g9na2ou-achraf-benmoussa-s-projects.vercel.app/api/v1/health` via accès propriétaire Vercel ; **HTTP 200**, `{"status":"ok","db":"ok","cache":"unavailable"}` ; runtime log Vercel lié au déploiement `GET /api/v1/health ... 200`, `environment=preview` | PASS connectivité DB ; cache non disponible, non fatal |
| Web Flutter Preview | projet `iamina-review` / `prj_AYaUi32KTDHak8I7dmdQpDrqd8SI`; déploiement `dpl_Mvz8HrtW3ZTq2Awf4yykeVfrD9U7`; source `1d42c311b65085fb7ba1b918b0a90315ad6e50ac` ; `READY`, `target=null` | PASS build |
| HTTP Web statique | `GET https://iamina-review-goowsfx8j-achraf-benmoussa-s-projects.vercel.app/` ; **HTTP 200**, document HTML Flutter | PASS livraison statique, pas un test d'interaction |
| Contrat de liaison Web→API | build Vercel Web consigne `Building IAMINA web with configured backend: https://iamina-certified-n3g9na2ou-achraf-benmoussa-s-projects.vercel.app` ; source `frontend/vercel_build.sh` refuse l'alias stable sur Preview, exige URL allowlistée, met `IAMINA_REMOTE_ACCOUNT_ENROLLMENT=false` sur Preview, et conserve l'ancien comportement Production | PASS build/config source uniquement |
| Compatibilité des deux SHA de déploiement | Git compare `c0192ded...1d42c311` : **un seul fichier changé**, `backend/evaluation/test_clinician_prep_protected_shadow_benchmark.py` (test portabilité), aucun changement backend runtime | PASS compatibilité de source |
| Configuration Vercel | backend `IAMINA_EXPECTED_DB_ROLE=iamina_preview_app` Preview seulement ; backend `DATABASE_URL` Preview changée via Neon ; frontend `IAMINA_REVIEW_PREVIEW_API_BASE_URL` Preview seulement ; secrets Production distincts inchangés ; secret Preview non relisible via API | écriture API et séparation config vérifiées ; secret exact non divulgué |
| Déploiements Production | backend `dpl_9tPKqRpMiyEMhCtQ99Jc5QV2ew77` (`9d24cff...`) ; Web `dpl_8eqWcB1cTJudwE9Rw581WenUsy1K` (`60de80ec...`) sont encore les derniers déploiements `target=production` à la vérification | aucune promotion observée |
| Neon IAMINA Production | projet `square-sun-82359137`, branche `br-fragrant-frost-b1lbdfzs`, `protected=false` toujours | **gate Production ouverte** |

## Traçabilité GitHub / CI

- [PR #1124](https://github.com/hraaaaf/IAMINA-MVP/pull/1124) **MERGED**, squash `main@37d9a5c2db62d66018172796b6f95b94bed8ab20`.
- CI prémerge sur source exacte `1d42c311b65085fb7ba1b918b0a90315ad6e50ac` : [CI #39031832193](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39031832193), [Developer portability #39031831993](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39031831993), [W01 static #39031832012](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39031832012), [migration drift #39031832013](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39031832013) : **4/4 COMPLETED/SUCCESS**.
- Une première exécution macOS a révélé `ModuleNotFoundError: evaluation` dans un sous-processus démarré depuis la racine monorepo. Correction `cwd=backend` dans le test, puis exécution complète `Developer portability` passée. Le correctif concerne le test uniquement.
- CI postmerge sur `main@37d9a5c2...` : [CI #39032351885](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39032351885), [W01 #39032351839](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39032351839), [migration #39032351859](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39032351859)  ; **3/3 COMPLETED/SUCCESS** sur `main@37d9a5c2db62d66018172796b6f95b94bed8ab20` (SHA exact vérifié). [PR docs #1125](https://github.com/hraaaaf/IAMINA-MVP/pull/1125) MERGED `main@281629603b29664a154b2d4d466fcca128c91335` ; CI docs prémerge [#39032690309](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39032690309) SUCCESS ; postmerge exact SHA [#39032830258](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39032830258) **SUCCESS** (docs-only ; jobs backend/frontend SKIPPED).

## Limites / risques bloquants

1. **Aucune preuve de parcours navigateur Web→API→DB avec auth et CORS/CSRF réels.** Le backend Vercel a `ssoProtection.enabled=true`, `deploymentType=all_except_custom_domains`. Le smoke HTTP API a nécessité l'accès propriétaire/authentifié Vercel. La Web Preview publique n'a pas été démontrée capable d'appeler directement l'API Preview protégée. **Ne pas désactiver le SSO implicitement.**
2. Le frontend HTTP 200 et le health Django HTTP 200 **ne valident ni compte patient, ni session, ni upload, ni mutations, ni transactions cliniques**. Aucun test patient n'a été réalisé.
3. `cache=unavailable` : dépendance cache dégradée et non fatale selon `core/api/v1/health.py`. À évaluer si le parcours visé nécessite ce cache.
4. **Neon Production reste `protected=false`** (limite quota Free déjà établie). Les protections réseau, preuves backup/restore, SMTP/récupération et garde clinique/réglementaire de Production restent ouvertes.
5. **Revue indépendante non obtenue**. Les validations CI, smoke limité et auto-revue n'équivalent pas à une certification indépendante.

## Next exact — W01 reste NO-GO, W02 gelé

Tester en **navigateur authentifié autorisé** l'interaction Web Preview→API Preview sans exposer ni désactiver les protections ; caractériser le SSO inter-projets / CORS / CSRF et la dégradation cache ; corriger seulement via solution sûre approuvée si changement de protection demandé. Exécuter G4–G7 restant (auth, sécurité, restores distants, revue indépendante). **Tout changement de politique SSO, toute mise en Production, tout achat et toute donnée patient sont des human gates séparés.**

Fichier de pilotage principal : `docs/assessments/2026-10-16-w01-before-w02-gates.md`.
