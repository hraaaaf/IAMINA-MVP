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
