# W01-B — Inventaire distant en lecture seule et décision de release

**Date : 16 octobre 2026.** **Statut : NO-GO production patient.**
**Goal :** identifier précisément ce qui est vérifié sur Vercel et Neon sans modifier production ni lire de secret.
**Succès de ce sous-lot :** données distantes non secrètes relevées, requête PostgreSQL 16 **read-only sur projet de test indépendant**, rapport traçable, test automatisé empêchant d'interpréter l'inventaire comme feu vert prod.
**Ce n'est pas la certification W01/W02/W14.**

## Preuves directes — connecteurs authentifiés

| Cible | Preuve vérifiée le 16/10/2026 | Interprétation contrôlée |
|---|---|---|
| GitHub | `hraaaaf/IAMINA-MVP`, `main@5275d9618962d1ebc10d33ef9cb7e35cb2c77194` au relevé ; CI générale et W01 exact HEAD SUCCESS | Code et validations synthétiques, **pas runtime hébergé** |
| Vercel frontend | Projet `iamina-review` / `prj_AYaUi32KTDHak8I7dmdQpDrqd8SI` ; déploiement `target=production` READY `dpl_8eqWcB1cTJudwE9Rw581WenUsy1K` ; commit Git `60de80ec070157f912cb62c80a7ded1e9bde75a6` | Déploiement **plus ancien** et d'une branche différente du HEAD GitHub. Logs de build observés : Flutter 3.41.0, origine backend fixée à `https://iamina-certified.vercel.app` |
| Vercel backend | Projet `iamina-certified` / `prj_Pn9FnyconF3h2w9gOU74iV98kJoU` ; déploiement `target=production` READY `dpl_9tPKqRpMiyEMhCtQ99Jc5QV2ew77` ; commit Git `9d24cff11fc422fe0c6235757dbf317eebe32912` | Différent du frontend et du HEAD. Logs : Python 3.12, dépendances installées depuis `backend/requirements.txt`, sortie build READY. **Ce log ne certifie pas la Root Directory réelle** |
| Variables Vercel backend | `DATABASE_URL` sensible déclarée pour `production` et `preview` ; `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `SECRET_KEY` déclarés | Les **valeurs**, les fingerprints des cibles et l'isolation preview/prod **n'ont pas été lus ni prouvés**. Aucune variable `IAMINA_ENV` constatée dans l'inventaire |
| Vercel frontend | 0 variables retournées par l'inventaire du projet | N'indique ni sécurité suffisante ni conformité du build Web |
| Neon IAMINA | Projet `square-sun-82359137`, région `aws-eu-central-1`, PostgreSQL 16 ; unique branche `production` `br-fragrant-frost-b1lbdfzs` avec `protected=false` | Aucune preuve d'une branche preview/dev isolée. **Aucune requête SQL n'a été faite sur cette branche** |
| Paramètres Neon IAMINA | `block_public_connections=false`, `allowed_ips.ips=[]`, `hipaa=false` relevés dans les métadonnées du projet | La couche réseau/le périmètre de conformité doivent être revus ; **cela ne démontre pas une fuite ni, seul, une infraction réglementaire applicable** |
| Neon test séparé | Projet `noisy-truth-00115950`, branche `synthetic-only` `br-sweet-frog-b9ok6ptp` ; SQL **SELECT seulement** exécuté : `current_database()='iamina925_empty'`, `server_version_num='160015'`, marqueur `IAMINA_W01B_SYNTHETIC_NEON_READ_ONLY` | Preuve effective de connexion Neon PostgreSQL 16 **via le connecteur**, hors du projet IAMINA. **Ne prouve pas Django/Vercel → Neon ni l'absence de données patient dans tout ce projet** |

**Limite externe :** les réponses accessibles aux outils Vercel n'exposent pas le paramètre effectif `rootDirectory` des projets ; lecture de l'arborescence des déploiements non disponible pour un des déploiements (404). La requête HTTPS directe des domaines depuis le conteneur d'exécution n'a pas pu résoudre leur DNS. Aucun statut de santé applicative distante n'est déduit de ces essais.

## Garde automatique anti-faux vert

Le fichier [inventaire JSON assaini](w01b-2026-10-16-sanitized-cloud-inventory.json) contient les identifiants non secrets et les **preuves manquantes explicitement false**. Le script `scripts/check_w01b_cloud_release_evidence.py` produit la liste des bloqueurs ; neuf tests `scripts/tests/test_w01b_cloud_release_evidence.py` couvrent les substitutions de projets, DSN accidentelle dans le snapshot, branche non protégée, absence d'isolation, route Vercel→Neon inférée à tort, SHA de déploiement obsolètes et garde humaine indépendante. La CI emploie `--assert-no-go` : **elle vérifie que l'état observé reste non autorisé, elle ne constitue jamais un release GO**.

## Suite sans mutation de production

1. **Root Directory :** contrôler côté dashboard Vercel `iamina-review` → `frontend/` et `iamina-certified` → `backend/`, noter preuve non secrète et Git production branch, sans modifier automatiquement.
2. **Bases :** confirmer par identité/fingerprint sûr (jamais DSN dans logs) les bases *preview* et *production*, leur non-interférence et leur conformité ; créer un environnement entièrement synthétique approuvé avant toute migration/restore, sans copier production.
3. **Chaîne compatible :** construire, tester et qualifier un couple frontend/backend candidat, puis E2E dans vrai navigateur sur Vercel → API → base synthétique ; échecs réseau/CORS/auth/CSRF.
4. **W02 :** chiffrement réel du coffre IndexedDB, clé locale/récupération, isolation multi-utilisateur A→B→A, offline et consentement ; décision humaine santé/processor.
5. **W14 :** validation clinique, sécurité, privacy/CNDP/transferts/sous-traitants, backup/rollback, gel SHA, approbations ; **seulement ensuite** stage production sans domaine, tests same-build, promotion.

**Conclusion vérifiable :** Neon synthétique PG16 fonctionne en lecture seule. W01-B distant, W02 et W14 restent ouverts. **NO-GO déploiement production patient**, aucune modification Vercel/Neon production effectuée.
