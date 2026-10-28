# W02 — Web BFF read-only integration candidate (2026-10-28)

Goal: enable same-origin W02 Web Preview BFF and fail-closed remote synthetic registration.

- W01 hosted Web→BFF→API SQL identity read-only returned database `iamina925_empty`, role `iamina_preview_app`, Neon project `noisy-truth-00115950`, branch `br-sweet-frog-b9ok6ptp`.
- This W02 code candidate reuses W01 Vercel OIDC BFF, moves Flutter Preview requests to browser origin, retains `IAMINA_REMOTE_ACCOUNT_ENROLLMENT=false` and additionally blocks POST auth/register unless Preview-only IAMINA_W02_REMOTE_E2E_ENABLED=true AND attested SQL identity matches.
- Protected Backend Preview URL is still controlled by the Git-branch-scoped Vercel environment. Current W02 Preview points to an older backend deployment lacking SQL identity route: E2E cannot start yet.
- No deployment, database write, or production change authorized. Static local code verification only; do not claim hosted W02 E2E.
- Remaining: target a backend deployment with live identity attestation, explicitly authorize Preview deploy and synthetic exercise, verify genuine browser→BFF→API flow, A/B/A with cleanup and independently verify auth_user=0; at-rest clinical encryption and key-recovery security gate independent.

## Préflight et E2E local sans déploiement — 28/10/2026

- Lecture SQL Neon indépendante : quatre identifiants concordants (`iamina925_empty`, `iamina_preview_app`, `noisy-truth-00115950`, `br-sweet-frog-b9ok6ptp`) et `auth_user=0`. Aucune écriture Neon.
- W01 hébergé : Web→BFF→API→Neon GET `/api/v1/ops/preview-db-identity` HTTP 200 JSON 4/4 ; health DB OK. Ceci n'est **pas** une preuve d'E2E W02 hébergé.
- Sandbox Vercel éphémère `w02-e2e-local-20261028`, checkout candidat `adcadb8e` : Node BFF 30/30 PASS après correction de l'assertion concernant `vercel.json` racine ; E2E Node BFF→API synthétique A→B→A 1/1 PASS, suppression et zéro comptes **uniquement en mémoire simulée** ; Python W02 coffre 5/5 PASS ; Flutter 3.41.0 VM 16/16 PASS ; analyse ciblée 0 issue ; Flutter Web release `Built build/web` PASS (80,2 secondes de compilation). Le sandbox a expiré après production de ces preuves.
- Inscription distante bloquée par défaut, attestation SQL 4 IDs fail-closed avant toute inscription synthétique activée explicitement. Aucun compte Neon créé dans cette passe.
- Le W02 Preview actuellement publié renvoie du HTML SPA sur le chemin `/api/v1/ops/preview-db-identity` ; seul un déploiement W02 ultérieur autorisé pourra prouver l'E2E hébergé exact. Aucune CI GitHub relancée ; aucune Preview publiée.
- Chiffrement au repos IndexedDB/Drift, gestion/récupération des clés et révocation serveur hébergée : NON CERTIFIÉS, NO-GO patients/Production.
