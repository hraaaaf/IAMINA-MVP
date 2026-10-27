# W01-G7 — Dossier de revue pré-fusion, Web uniquement (27/10/2026)

**Statut : REVUE TECHNIQUE INTERNE PRÉPARATOIRE — NON INDÉPENDANTE — NO-GO.** Le contenu s'appuie sur les sources GitHub consultées au HEAD `1970fdd705ffa96da2fdbb4dc41686dd5c38331a`, PR #1128 Draft, et les runs vérifiés au début de cette revue. Ce document n'est pas une certification conformité, clinique ou Production. **Ne pas réutiliser les PASS d'un ancien commit pour certifier les modifications de ce dossier.**

## Goal, critères observables, preuve

- **Goal :** identifier avant merge les risques bloquants Web → BFF → API → Neon et disposer d'un plan de tests reproductible, indépendant des validations UI.
- **Succès G7 :** revue indépendante formalisée sans findings BLOCKER/MAJOR ; tous les gates G1–G6 effectivement résolus ; CI sur SHA final ; preuve SSO hébergée + isolation patient A/B + nettoyage et vérification SQL ; décision GO par responsable ; merge autorisé et contrôles postmerge. Une CI locale verte est nécessaire mais jamais suffisante.
- **Preuve de départ :** CI principale [#40468638513](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40468638513) SUCCESS au HEAD `83a2a13e` ; 21/22 workflows SUCCESS, seul OIDC refusé et différé. Pour HEAD `1970fdd`, CI [#40473657691](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40473657691) IN_PROGRESS au premier contrôle, donc statut exact à confirmer.

## Écarts ouverts (priorisés)

| ID | Sévérité avant GO | Preuve vérifiable / risque | Prochaine preuve |
|---|---|---|---|
| W01-G7-01 | BLOCKER | G5 : test hébergé OIDC GitHub/Vercel échoue ; parcours navigateur SSO Web → BFF → API → Neon synthétique non certifié. **G5 explicitement différé : aucune intervention OIDC sans nouvel ordre.** | Déverrouillage humain, preflight SHA/API DB/rôle/branche puis E2E A→B→A, suppression, `auth_user=0`. |
| W01-G7-02 | BLOCKER | G6 : clone du marqueur synthétique non vide réussi mais **snapshot neuf du même marqueur non restauré** ; création du projet jetable refusée par l'outil. | Nouveau project_id Neon créé hors outil, snapshot racine frais, restauration `finalize=false`, valeurs et source vérifiées ; nettoyage autorisé sous condition de PASS. |
| W01-G7-03 | BLOCKER | G2 : Neon Production `square-sun-82359137` branche archivée, `protected=false`, connexions publiques non bloquées, 6 h history, aucun snapshot programmé déclaré. Aucun durcissement sans GO. | Plan sécurité/protection, sauvegarde, secrets, monitoring et rollback approuvé ; audit métadonnées puis test non destructif. |
| W01-G7-04 | MAJOR | `backend/core/api/v1/account.py` enregistre sur effacement réussi l'UID Firebase **brut** dans `ErasureRecord.firebase_uid_snapshot`, alors que `ErasureAttempt` l'efface en succès. Le modèle `backend/core/models/erasure_record.py` conserve également un champ `hook_failures` à description legacy. Conserver un identifiant dans un reçu durable requiert justification et politique de rétention explicites. | Décision privacy/légale sur finalité/rétention ; migration de minimisation et revue historique seulement après décision, tests de non-fuite. |
| W01-G7-05 | MAJOR | G3 : `IN_PROGRESS` persiste après interruption non interceptée ; bloque les retries (fail-closed) mais ne restaure pas les opérations Redis/Firebase partiellement effectuées ; aucune procédure cloud de réconciliation prouvée. | Test de crash synthétique ajouté en candidate et revue humaine d'une procédure réconciliatrice avec preuves d'identité, hooks et audit. |
| W01-G7-06 | MAJOR | `frontend/api/preview-proxy.js` limite à 4 MiB tandis que le contrat Flutter documentaire indique 15 MiB pour certains documents. Le proxy enlève cookies/session par sécurité ; la parité complète auth SessionAuth+CSRF et upload réel reste non prouvée. | Test Web Preview d'upload (sans données de santé), décision explicite du contrat de taille et de session ; aucune augmentation aveugle du plafond. |

## Travail autonome exécuté en candidate

**Tests synthétiques de fenêtre crash, sans cloud :** `backend/core/tests/test_w01_g7_erasure_crash_gates.py`.

1. `SystemExit` au hook après commit de `PENDING → IN_PROGRESS` : le SQL User reste présent, aucun reçu de succès, retry refuse 503 avant hook/Firebase.
2. `SystemExit` après lancement Firebase fictif : effet appelé une seule fois, User toujours présent, état `IN_PROGRESS`, retry refuse 503 sans relecture Firebase.

**Limitation cruciale :** `SystemExit` simule un arrêt Python, **pas** un vrai kill du processus, une panne de DB, une coupure réseau ni une garantie transactionnelle entre Firebase et PostgreSQL. En CI, aucune action de suppression réelle ni réseau Firebase.

## Décision et séquence

**NO-GO maintenu.** G7 ne peut pas être déclaré independent/certifié par l'auteur de ces tests. Si CI rouge sur candidate, corriger tests/code ; si vert, attacher résultats au SHA. Après preuves G2/G3/G5/G6 et revue indépendante, décision humaine GO → merge explicite → postmerge/preview et Production uniquement sous GO distinct. W02 gelé. L'authentification OIDC reste différée.

Fichier canonique : `docs/ROADMAP.md`.
