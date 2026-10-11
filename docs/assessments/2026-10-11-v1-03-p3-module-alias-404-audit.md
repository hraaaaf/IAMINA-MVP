# IAMINA P3/V1-03 — Audit alias ModuleRegistry 404

Date: 2026-10-11 | Baseline: `15cfe25fcc93fff00a1198d705fb683c7a2eb960` | Branche: `parallel/v1-03-module-alias-404-audit-20261011` | Issue: #929
Statut: **constat 404 confirmé par CI historique; mécanisme causal précis non reproduit localement**. Audit statique clos, correctif de routage interdit tant que la décision d'architecture est ouverte.

## Goal / preuve
Goal: expliquer l'écart entre module enregistré et route `/api/v1/diabetes/logs/batch` non exposée, sans ouvrir une surface non protégée.
Succès engineering ultérieur: `ModuleRegistry.all()` et le routage effectif accordés, et si l'alias est intentionnel, tests Django resolver/HTTP/OpenAPI/CSRF SQLite+PG.

## Constat actuel
1. `backend/diabetes/apps.py:15-51` : `DiabetesConfig.ready` enregistre `DIABETES_MANIFEST` avec **le même objet** `logs_router` que l'API canonique. `backend/core/registry.py:25-45` garde les objets en dictionnaire de classe. `backend/diabetes/manifest.py` : `url_prefix="/diabetes"`.
2. `backend/diabetes/api/main.py:81` monte `logs_router` sur `/v1`, puis `:103-106` boucle sur les modules pour monter `/v1/diabetes` avec `_mod.router` sans `url_name_prefix`. `backend/amina/urls.py` charge cet objet sous `api/`.
3. [Issue #929](https://github.com/hraaaaf/IAMINA-MVP/issues/929) rapporte **quatre réponses 404** HTTP sur l'alias en [SQLite CI #38102619725](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38102619725), et l'OpenAPI générée n'a aucun chemin `/api/v1/diabetes/...`; le chemin canonique `/api/v1/logs/batch` continue de fonctionner. Ce n'est pas une preuve de bypass CSRF ni de vraie fuite.
4. `backend/core/tests/test_p3_module_registry.py` couvre inscription, activation, dépendance du module, mais **pas la résolution de la route namespacée**. La matrice CSRF actuelle a retiré cette supposition d'accessibilité : comportement rigoureux, ne pas tester une route inaccessible comme protégée.
5. **Hypothèse technique documentée, pas cause racine prouvée:** selon la documentation actuelle Django Ninja, monter deux fois la même instance `Router` sur une même `NinjaAPI` nécessite `url_name_prefix` distinct, sinon `ConfigError`. Voir https://django-ninja.dev/guide/routers/ et https://django-ninja.dev/reference/api/ . `backend/requirements.txt:9` spécifie `django-ninja>=1.0` **sans version exacte**, donc le mécanisme local au runner dépend de la version effectivement installée. Le 404 sans erreur et le test du registre enregistré sont des indices incompatibles avec une attribution certaine au seul préfixe manquant. Vérifier chronologie `ready()` / import / `api.urls` / version effective.

## Diagnostic discriminant à exécuter ensuite
A. Instrumenter test read-only: `django.get_version()`, `ninja.__version__`, `ModuleRegistry.all()`, identité `_mod.router is logs_router` juste avant et après import `diabetes.api.main`, puis `api._routers`/route-list si exposition autorisée.
B. Tester `django.urls.resolve('/api/v1/diabetes/logs/batch')`, méthode POST sans cookie puis cookie-CSRF invalide/valide, extraire `api.get_openapi_schema()`. Comparer `/api/v1/logs/batch` dans le **même process**.
C. Si registre vide lors de construction: corriger ordre d'import/initialisation sans route publique accidentelle. Si duplication effective: isoler nouveau routeur ou `url_name_prefix` unique selon version; préserver auth, patient scope et CSRF.
D. Avant toute activation, arbitrer **alias P3 attendu ou dormant**; s'il est dormant intentionnellement, supprimer seulement la promesse trompeuse documentaire et maintenir l'inaccessibilité.

## Verdict
- **Vérifié:** écart canonique / alias observé en CI historique, registration et double référence source.
- **Non prouvé:** cause exacte du 404, version Ninja du runner, nécessité métier de la route P3.
- **Gate:** aucune activation/modification du routage avant décision et tests HTTP/OpenAPI/CSRF exact-head SQLite+PostgreSQL.
Next exact: script diagnostic non intrusif dans la branche, puis correction conditionnelle exclusivement après preuve de la cause et décision de surface.

## Complement technique — 2026-10-11
- Test de caractérisation ajouté : `backend/core/tests/test_p3_dormant_alias_route_guard.py` sur registry, OpenAPI et resolver HTTP. Il prévient une activation accidentelle tant que l'alias est considéré dormant ; toute activation voulue requiert mise à jour explicite des tests et gate de sécurité.
- Ce test n'établit pas la cause racine du 404. Verdict CI exact-head à établir.

## Diagnostic discriminant ajouté — 2026-10-11
Le test `backend/core/tests/test_p3_dormant_alias_route_guard.py::P3DormantAliasRouteGuardTest::test_current_ninja_mount_inventory_has_canonical_router_only` compare les préfixes effectivement enregistrés dans la collection `api._routers` pour **le même objet** `logs_router`, indépendamment du Django resolver et de l'OpenAPI déjà inspectés. Résultat attendu de caractérisation : **un seul montage `/v1`**, aucun `/v1/diabetes`. Une réussite sur SHA exact renforcera l'explication « alias jamais monté », tandis qu'un échec orientera vers un problème de construction des opérations / URL. Ce test ne peut pas à lui seul dater l'import avant `AppConfig.ready`.
Django Ninja actuel documente `url_name_prefix` obligatoire pour remonter le même Router sur un même NinjaAPI ; cf. https://django-ninja.dev/guide/routers/ et https://django-ninja.dev/reference/api/. Rien n'est activé : pas de route nouvelle, pas d'auth/CSRF ou de contrat patient modifié.

**CI gate après ajout du test :** la base `main` est utilisée temporairement uniquement parce que les GitHub Actions `pull_request` sont limités à `main` / `dev`. À l'issue de la certification du nouveau HEAD, restaurer `safety/v1-03-glucose-ocr-unit-provenance-20261011` et conserver la PR en DRAFT. Un succès démontrerait le montage observé par le test, non le moment précis de l'import ni la décision de rendre l'alias actif.

## Chronologie dans un processus Django neuf — nouveau test discriminant

**Goal** : établir si la boucle `ModuleRegistry.all()` exécutée depuis `diabetes.api.main` passe avant ou après l'appel réel de `ModuleRegistry.register()` de `DiabetesConfig.ready()`, plutôt que déduire cet ordre depuis l'absence d'alias. **Critère observable** : événements tracés par un interpréteur Python indépendant lors de `django.setup()` puis import `diabetes.api.main`. **Preuve demandée** : test exact-HEAD vert, avec `all()` depuis la construction API observé alors que le registre est vide, avant l'appel `register()` ; ensuite registre final contenant diabetes et routage de `logs_router` limité à /v1.

Nouveau test `backend/core/tests/test_p3_dormant_alias_route_guard.py::test_fresh_django_bootstrap_registry_timeline` : lance `sys.executable -c` dans `backend/` pour éviter de réutiliser les imports déjà initialisés du test runner. `sys.setprofile` intercepte **uniquement** les appels `ModuleRegistry.all/register` sans modifier le registre, son URLconf ni les providers. Le subprocess lit `django.get_version()` et la version Ninja, ainsi que l'identité des montages réels du même `logs_router`. Seul du contenu de diagnostic structurel non patient est produit.

**Limite** : le test vérifie une hypothèse précise sur la version et l'environnement CI, pas la décision métier de publier une nouvelle route, pas un test CSRF de l'alias, pas une preuve de conformité patient. Une trace divergente doit mener à un diagnostic alternatif — jamais à activer automatiquement `/api/v1/diabetes/...`. En cas de succès, nous pourrons remplacer l'hypothèse « import-order » par une observation de l'ordre dans l'interpréteur isolé, sans prétendre connaître les importeurs exacts hors de cette trace. La CI de ce nouveau HEAD est à obtenir avant toute déclaration.
