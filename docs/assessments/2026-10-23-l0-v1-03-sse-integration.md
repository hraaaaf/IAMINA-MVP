# IAMINA Web — L0-04 V1-03 SSE privacy candidate (PR #1056 reprise), 23/10/2026

**GOAL** : préparer sur exact `main@8ada5aab8e8006bbbdc275eabbabf014a4714e0b` le correctif déjà codé [#1056](https://github.com/hraaaaf/IAMINA-MVP/pull/1056), passage des entrées cliniques SSE GET query → POST body + tests anti-egress/CSRF et documentation OpenAPI.

**Préparation SOURCE STRICTE** : 13 chemins de `#1056` HEAD `f57917c37ea18dad672e248422022224213cafbf`, vérifiés identiques au merge-base de cette PR dans le `main` actuel (8 fichiers existants, 5 fichiers nouveaux) : aucun écrasement de changements main. Les blobs de code/tests/workflow sont recopiés strictement, **non combinés avec W01/L0 Companion** et non revendiqués opérationnels.

**Gates de validation** : exécuter Django PostgreSQL, Ruff, tests SSE négatifs GET/POST/CSRF/auth/headers, Flutter `ApiClient` et PWA cache, tests navigateur pour démontrer absence d'URL/query avec données médicales. Comparer réseau/console/captures, faire revue indépendante sécurité et confidentialité (logs, CDN, APM, redirects, replay). **IMPORTANT** le workflow `.github/workflows/companion-chat-e2e-screenshot.yml` diverge de l'actuelle PR L0 #1140 qui vérifie un chat local-only désactivé ; réconcilier les deux oracles sans rouvrir HTTP patient. La couche auth/BFF de W01 #1128 reste NO-GO, donc SSE complet patient ne peut pas être certifié sur ce seul candidat.

**Status** : commit git **DÉTACHÉ seulement**, sans branche/PR/CI concurrentes, ni Vercel; aucune autorisation de merge/Production; score NOT RATED, W01 NO-GO/W02 gelée. Next : attendre conclusion CI D11 #1142, puis publier une PR L0-04 sur main et exécuter une seule batterie complète, résoudre recouvrements #1140 et W01 avant livraison.
