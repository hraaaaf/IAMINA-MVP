# IAMINA · W02-F09-C7 — Procédure opérateur de migration synthétique (08/11/2026)

**Statut : procédure préparée, NON EXÉCUTÉE.** Ce document ne vaut ni autorisation clinique ni preuve de migration accomplie.

## Périmètre et preuve initiale

- Cible Neon **uniquement** : projet `noisy-truth-00115950`, branche `br-sweet-frog-b9ok6ptp` (`synthetic-only`), **nouvelle base** `iamina_w02_c7_synthetic`, ID `320089`.
- **Interdiction** : `iamina925_empty`, ID `31152` (46 tables avec historique W01/D2 incompatible), tout autre projet/base/branche.
- Code exact : `259cc5c48ccdd0976fbe29b6bb9bb0bae6326991`, PR #1318 Draft. Test [Actions #42430286879](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42430286879) 2/2 GREEN : migration Django propre sur **PostgreSQL 16 jetable** (pas Neon), C7 20 tests + 72 régressions C2–C6, garde-fou 10 tests.
- Exécution précédente de la migration Neon via assistant **refusée par le contrôle de sécurité**, aucune écriture. Ne pas rediriger l'exécution refusée vers un autre outil du chat.
- Compte de migration : `iamina925_empty_owner`, séparé du rôle d'application `iamina_w02_c7_preview_app` qui ne dispose pas de CREATE. La branche appelée `synthetic-only` est **primary/default du projet Neon** : ce nom seul n'est pas une preuve de sécurité.

## Conditions préalables obligatoires de l'intervention administrative

1. Procéder depuis un poste d'administration approuvé disposant d'un coffre de secrets. Le compte propriétaire possède des droits étendus **sur plusieurs bases de la branche** : vérifier la cible effective **dans la session PostgreSQL**, jamais seulement dans le nom du lien. Ne jamais coller mot de passe, URI ou cookie dans une PR, un chat, un job public, une capture d'écran ou un rapport. Ne pas lancer depuis une Preview publique.
2. Exiger une session PostgreSQL avec `current_database() = 'iamina_w02_c7_synthetic'` et `current_user = 'iamina925_empty_owner'`. Avant exécution : **0 table public, aucun registre `django_migrations`, aucun compte ni profil**. Si résultat différent : **STOP**.
3. Vérifier `git rev-parse HEAD` = `259cc5c48ccdd0976fbe29b6bb9bb0bae6326991`. Utiliser les dépendances du dépôt, Python 3.12 comme dans la CI. Définir le DSN uniquement dans une variable protégée injectée par le coffre et isolée du shell history ; jamais dans une ligne de commande explicite.
4. Dans `backend`, lancer **d'abord** `python manage.py migrate --plan` sous une connexion à privilèges de lecture seulement. Examiner toute la liste ; confirmer les deux migrations `core.0020_web_refresh_candidate` et `core.0021_web_refresh_transport_nonce`, sans migrations W01/D2 `0020_erasure_attempt`, `0021_erasure_attempt_claim_states`, `0022_d2_preview_consent_receipt`, `0023_d2_in_app_notice`. Stop si plan différent.
5. **Après autorisation de l'opérateur responsable et seulement si les préconditions sont satisfaites**, exécuter `python manage.py migrate --noinput` avec la connexion de migration à **la nouvelle base seulement**. Cette commande est spécifiée pour l'opérateur ; elle **n'a pas été exécutée par ChatGPT**. Ne pas employer `--fake`, `--fake-initial`, `flush`, `drop`, `reset` ou modification du registre à la main.
6. Après exécution, contrôler en lecture seule : `django_migrations` existe, les trois migrations `core.0019_auth_abuse_bucket`, `core.0020_web_refresh_candidate`, `core.0021_web_refresh_transport_nonce` sont appliquées, et les tables `core_webrefreshfamily`, `core_webrefreshconsumedsecret`, `core_webrefreshtransportnonce` existent. Aucun compte/profil synthétique n'a été ajouté pendant la migration. `python manage.py makemigrations --check --dry-run` doit réussir.
7. Construire une preuve JSON **redactée** sans DSN, email, nom, ID patient, secret, requête brute ni jeton : `database`, `role`, `source_sha`, `public_tables` (entier), `core_migrations` (liste de noms), `c7_tables` (liste de trois noms), `user_count`, `profile_count`. Vérifier hors ligne avec :
   - `python scripts/check_w02_f09_c7_operator_evidence.py --stage before --evidence <preuve-avant.json>`
   - `python scripts/check_w02_f09_c7_operator_evidence.py --stage after --evidence <preuve-apres.json>`
   Un résultat `EVIDENCE_VALIDATED_NOT_AUTHORIZATION` signifie une cohérence de l'inventaire fourni **pas** une preuve cryptographique de sa provenance, ni une validation de sécurité clinique.
8. Avec un opérateur responsable, revoir le besoin d'accès **SELECT minimal à `django_migrations`** du rôle applicatif `iamina_w02_c7_preview_app` pour le garde-fou runtime C7. Vérifier l'absence de droits sur l'ancienne base et **ne pas accorder de droits globaux**. Un rôle `read_write` sur la nouvelle DB ne doit pas avoir CREATE de schéma.
9. Faire vérifier les pièces par un deuxième intervenant ; consigner décision, date, référence de migration, résultat, anomalies dans **un seul canonique Notion W02**. Ne pas partager de journaux de commandes sensibles.

## Vérifications SQL non mutantes (exemples, sur la base explicitement validée)

```sql
SELECT current_database() AS db, current_user AS db_role,
  (SELECT count(*) FROM pg_catalog.pg_tables WHERE schemaname='public') AS public_tables,
  to_regclass('public.django_migrations') IS NOT NULL AS ledger_exists,
  to_regclass('public.core_webrefreshfamily') IS NOT NULL AS family_exists;
```

**Après migration seulement** (ces tables doivent désormais exister) :

```sql
SELECT app, name FROM django_migrations
 WHERE app = 'core' ORDER BY name;
```

```sql
SELECT tablename FROM pg_catalog.pg_tables
 WHERE schemaname = 'public' AND tablename LIKE 'core_webrefresh%'
 ORDER BY tablename;
```

## Hors périmètre / gates restants

- Pas de modification de Production, pas de déploiement Vercel, pas de merge, pas de patient réel.
- La migration **ne monte pas** l'endpoint C7. Les composants Node BFF C4, Django C7, Flutter C8, cookies / CSRF / origine / OIDC et contrôles de nonce doivent faire l'objet d'une intégration **Preview-only** et d'une vérification indépendante.
- Même avec la migration verte, le verdict est **W02 SECURITY NO-GO / PATIENT NO-GO** jusqu'à E2E authentifié, anti-rejeu, déconnexion, 2 onglets, et revue de sécurité.

## Proof & source

[PR #1318](https://github.com/hraaaaf/IAMINA-MVP/pull/1318) · [Actions #42430286879](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42430286879) · [Notion canonique W02](https://app.notion.com/p/3fd77c66336281f390e2fe3e46651931).

**État présent : nouvelle DB créée et vide, procédure rédigée, mutation non exécutée.**
