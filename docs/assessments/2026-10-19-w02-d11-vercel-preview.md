# IAMINA WEB — W02/D11 — Vercel Preview isolé (19/10/2026)

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
