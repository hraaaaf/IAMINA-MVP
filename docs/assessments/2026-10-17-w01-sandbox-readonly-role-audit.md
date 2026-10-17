# IAMINA W01-G2/G3 — Audit Neon sandbox, lecture seule (17 octobre 2026)

## Goal / succès / preuve

**Goal :** évaluer la préparation d'un futur accès applicatif Vercel Preview à la sandbox synthétique **sans utiliser de données patients, sans modifier Neon, secrets ou déploiements**.

**Succès du lot ciblé :** identifier directement la base, vérifier les comptages exacts des tables et les privilèges du rôle propriétaire, documenter les interdits et le protocole d'acceptation. **Ce succès local ne clôt ni W01-G2/G3 ni W01.**

**Sources mesurées :** API Neon connectée `list_branches`/`run_sql` ; lectures catalogues PostgreSQL et `SELECT COUNT(*)` sur les 42 tables `public` du projet synthétique. Source IAMINA `main@949f37f9329c45dfdfba5890f3a44790df0e9529`. Aucune lecture de ligne nominative ni opération d'écriture.

## Résultats observés

| Contrôle | Preuve / verdict |
| --- | --- |
| Projet sandbox | `noisy-truth-00115950`, distinct du projet IAMINA production `square-sun-82359137` |
| Branche / base | `br-sweet-frog-b9ok6ptp`, `iamina925_empty` |
| PostgreSQL | `16.15`, `current_database()=iamina925_empty` |
| Tables `public` | **42 tables** recensées dans `pg_tables` ; comptage **exact** de chacune |
| 39 tables hors métadonnées Django | **39/39 ont exactement zéro ligne** |
| Métadonnées Django | `auth_permission=150`, `django_content_type=38`, `django_migrations=69` : **257 lignes de métadonnées** |
| Propriétaire | `iamina925_empty_owner` possède **42/42 tables** |
| Attributs PostgreSQL owner | `rolsuper=false`, **`rolcreatedb=true`, `rolcreaterole=true`, `rolreplication=true`, `rolbypassrls=true`**, login activé |
| Rôles de test | `SELECT COUNT(*) FROM pg_roles WHERE rolname LIKE 'iamina_preview_%'` → **0** |
| ACL schéma `public` | `aclexplode` : `PUBLIC` possède `USAGE`, pas `CREATE` ; propriétaire du schéma `pg_database_owner` |
| Vercel Preview → vraie Neon DB | **NON PROUVÉ** : `DATABASE_URL` sensible distincte par target, valeur non exposée par le connecteur |
| Patient-production | **INTERDIT** : aucune donnée patient, aucune release autorisée |

**Diagnostic :** ne pas réutiliser `iamina925_empty_owner` comme compte de l'application Web/API Preview. Même sans `SUPERUSER`, `CREATEROLE` et `BYPASSRLS` notamment excèdent les permissions applicatives attendues. **On ne conclut pas à une compromission** : c'est un défaut de cloisonnement à corriger **avant un accès applicatif réel**.

## Reproductibilité — SQL strictement lecture seule

Les contrôles suivants ne produisent que des identifiants de rôles/objets et des comptes :

```sql
SELECT current_database(), current_user, current_setting('server_version');
SELECT tablename FROM pg_catalog.pg_tables
WHERE schemaname = 'public' ORDER BY tablename;
SELECT rolname, rolsuper, rolcreatedb, rolcreaterole,
       rolreplication, rolbypassrls, rolcanlogin
FROM pg_catalog.pg_roles
WHERE rolname IN ('iamina925_empty_owner', 'iamina_preview_runtime');
SELECT pg_catalog.pg_get_userbyid(c.relowner) AS owner, count(*) AS table_count
FROM pg_catalog.pg_class c
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind IN ('r','p')
GROUP BY 1;
SELECT count(*) AS preview_test_roles
FROM pg_catalog.pg_roles
WHERE rolname LIKE 'iamina_preview_%';
```

Pour l'absence de données applicatives, faire **`SELECT COUNT(*)` individuellement sur chaque table publique** (comme fait ici), plutôt qu'une approximation `pg_stat_*` ; exclure uniquement les 3 tables de métadonnées indiquées. Ne pas afficher de colonnes ou de lignes cliniques et **ne jamais lancer ce contrôle sur la Neon production** sans autorisation spécifique.

## Plan préparatoire — non exécuté, gates humaines requises

1. Conserver `IAMINA_ENV=development` et tous les secrets Vercel existants **inchangés**. Le nouveau code Django (`main`) est fusionné mais **non déployé** ; son fail-closed ne prouve pas la connexion de l'ancien runtime.
2. Préparer un **rôle PostgreSQL applicatif dédié**, distinct du propriétaire et du futur rôle de migrations : `NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS`. Ne jamais employer le rôle propriétaire comme secret applicatif. Vérifier les permissions par inventaire des vrais besoins de Django, **sans GRANT blanket sur 42 tables**, sans `CREATE` schéma, sans `BYPASSRLS`. Ne pas créer/mettre à jour le rôle ni son mot de passe dans ce lot.
3. Préparer la preuve de séparation des deux secrets Vercel `DATABASE_URL` **sur l'hôte autorisé**, via host, nom de DB, `current_database()` et rôle courant **sans exposer URI, utilisateur, mot de passe, chaîne de connexion ou données patients**. Vérifier Preview vers `iamina925_empty`, Production inchangée ; refuser toute divergence, ne pas toucher aux secrets maintenant.
4. Avant tout déploiement synthétique Vercel : **autorisation explicite distincte** du propriétaire, rôle least-privilege opérationnel et vérifié, DB séparée attestée ; test navigateur Web → Django → Neon avec données fictives, rollback isolé.
5. Conserver séparément les gates de production : protection de la branche Neon IAMINA (essai refusé **HTTP 422 / quota plan**), restrictions réseau, récupération SMTP et certification de release. **Aucun achat/upgrade** sans décision propriétaire.

## Verdict et continuité

**Preuve locale sandbox : PASS** pour l'inventaire de schéma, les comptages exacts et la découverte de privilèges. **Accès runtime Vercel Preview, compte least-privilege, G2/G3 complet : NOT VERIFIED.** **W01 NO-GO ; W02 GELÉ.**

Décision propriétaire de conserver provisoirement la sandbox synthétique : [issue #1117, décision](https://github.com/hraaaaf/IAMINA-MVP/issues/1117#issuecomment-6227852503). Audit ajouté au suivi : [issue #1117, comptages/permissions](https://github.com/hraaaaf/IAMINA-MVP/issues/1117#issuecomment-6227987143).

## Tentative autorisée du 17/10 — compte SQL sandbox à privilèges limités

L'utilisateur a explicitement dit « Go » pour créer le rôle sandbox et, **uniquement si sa connexion était vérifiée**, modifier le secret **Vercel Preview**. **La mutation du secret n'a PAS eu lieu.**

- `iamina_preview_app` a été créé en SQL comme rôle **`NOLOGIN`**, sans `SUPERUSER/CREATEDB/CREATEROLE/REPLICATION/BYPASSRLS`. Attribution transactionnelle par tables réelles : **39 tables runtime** avec `SELECT/INSERT/UPDATE/DELETE`, **2 métadonnées** (`auth_permission`, `django_content_type`) en `SELECT` seulement ; **aucun droit sur `django_migrations`**, ni `CREATE` de schéma ; **37 séquences runtime** en `USAGE/SELECT`. Le compte reste inutilisable pour se connecter, donc **pas prêt** pour Vercel.
- `ALTER ROLE ... LOGIN PASSWORD` refusé (permissions Neon). Deux alternatives avec `CREATE ROLE ... LOGIN PASSWORD` / transaction atomique ont été rejetées ; **aucun deuxième rôle `LOGIN` ajouté**. La confirmation finale par `pg_roles` ne montre que `iamina_preview_app` **`rolcanlogin=false`**.
- Les mots de passe aléatoires générés lors des essais n'ont jamais été imprimés, enregistrés dans Git/Notion ni injectés à Vercel ; aucune requête vers Neon IAMINA production.
- **Mesure de prévention ajoutée au code candidat, non déployée :** toute cible `VERCEL_ENV=preview` doit déclarer `IAMINA_EXPECTED_DB_ROLE` et sa `DATABASE_URL` doit utiliser exactement cet utilisateur non propriétaire. Interdiction des paramètres libpq de redéfinition d'identité `user`, `password`, `passfile`, `options`. Des tests synthétiques couvrent les violations.
- **Gate humain restant :** opérateur Neon autorisé à créer/activer une identité de connexion réellement limitée ; vérification de login SCRAM et droits ; puis mutation ciblée `DATABASE_URL` de Preview uniquement (pas Production), sans déploiement automatique. Éviter d'utiliser `create_postgres_role` par défaut si les attributs hérités accordent `BYPASSRLS`.

**État prouvé :** grants et rôle `NOLOGIN` sur sandbox **PASS** ; compte connecté Preview, secret Vercel et tests runtime **BLOCKED/NOT VERIFIED** ; **W01 NO-GO, W02 gelé**.


## Closeout Git de la prévention Preview — 17/10/2026

[PR #1121](https://github.com/hraaaaf/IAMINA-MVP/pull/1121) fusionnée : `main@c4507fb8d920da830cc69b083711d9271623ad59`. Tests backend de la garde d'identité Preview : CI prémerge [#39013879410](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39013879410), [W01 #39013879437](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39013879437), [drift #39013879408](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39013879408) SUCCESS. Postmerge W01 [#39014322981](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39014322981) et drift [#39014322888](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39014322888) SUCCESS ; générale [#39014322826](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39014322826) en cours au relevé.

**Attention : succès des tests de code ≠ preuve login/Preview.** Neon `iamina_preview_app` est toujours `NOLOGIN`, le secret `DATABASE_URL` Vercel Preview reste inchangé. Aucune publication Vercel ni donnée patient. [État blocage et procédure opérateur Neon](https://github.com/hraaaaf/IAMINA-MVP/issues/1117#issuecomment-6231236408). **W01 NO-GO.**
