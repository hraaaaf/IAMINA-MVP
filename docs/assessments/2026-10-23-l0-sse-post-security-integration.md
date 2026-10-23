# IAMINA Web — L0 / V1-03 : reprise SSE POST-only et confidentialité, 23/10/2026

## Goal, succès, preuve

**Goal** : reprendre la correction [PR #1056](https://github.com/hraaaaf/IAMINA-MVP/pull/1056) de V1-03 — aucune donnée médicale de chat en URL (GET/query), échanges SSE POST JSON sous contrôle auth/CSRF, contexte AI-egress limité au patient authentifié, refus clinique déterministe, cache PWA cohérent.

**Succès vérifiable** : GET `/api/v1/ai/chat/stream?message=...` → 405 ; POST sans auth → 401/403 ; cookie + Bearer forgé sans CSRF → refus ; refus consentement et sécurité avant tout appel externe ; POST Flutter sans message dans URL ; après instanciation différée du stream, isolation A/B du contexte egress et `[DONE]`. Scénarios Chrome/PWA First Install et rollback cache à tester contre le vrai build Web. Les tests sont **synthétiques uniquement**, jamais avec patient réel.

**Provenance** : source `f57917c37ea18dad672e248422022224213cafbf` (ancienne #1056, 4/4 CI historiques), ancêtre `f41778fcb1cfb0608de2b11e37fe290afc1332e9`, nouveau candidat créé directement sur `main@8ada5aab8e8006bbbdc275eabbabf014a4714e0b`. **13 chemins source vérifiés : tous les blobs sur main sont identiques à ceux de l'ancêtre de #1056**, donc aucun changement ultérieur de ces chemins n'est écrasé. Transplantation blob-pour-blob du code, tests et handovers sources, sans modifier le code productif.

## Tests et revues à exécuter sur le nouveau SHA

| Gate | Critère exact | Résultat |
| --- | --- | --- |
| CI Python / Flutter | suite complète + Ruff, tests CSRF/transport POST, contrat Dart, OpenAPI | EN ATTENTE |
| Browser Web RELEASE | SSE streaming POST sur Preview protégée et zéro message dans URL/log/analytics | NON PROUVÉ |
| Access-control | A→déconnexion→B→A, refus cross-account CSRF, contexte asynchrone par patient | NON PROUVÉ |
| Service Worker | nouvelle installation + cache ancien évincé, documents patients intacts | NON PROUVÉ |
| Compatibilité L0 réseau [#1140](https://github.com/hraaaaf/IAMINA-MVP/pull/1140) | l'écran chat local-only doit rester honnêtement désactivé, tests Chrome harmonisés | À RÉCONCILIER |
| W01 [#1128](https://github.com/hraaaaf/IAMINA-MVP/pull/1128) | same-origin BFF, signature, runtime DB fingerprint/Redis et identity-isolation | NO-GO |
| Audit indépendant clinique, privacy, sécurité | signatures + Perfection Pass + score ≥9.0 | NON OBTENUS |

**Alerte de stack** : `.github/workflows/companion-chat-e2e-screenshot.yml` est aussi modifié par [L0 #1140](https://github.com/hraaaaf/IAMINA-MVP/pull/1140). Ce candidat est **indépendant sur main pour tester SSE**, mais **NE DOIT PAS être mergé isolément** : après décisions de conformité, intégrer son test de flux SSE avec la présentation Web RELEASE qui bloque le chat sur #1140. Ne jamais réactiver l'ancien compositeur médical par un changement de workflow. Même conflit potentiel d'architecture avec le BFF W01 : réconcilier avant publication.

**Human gates** : aucun nouveau Vercel n'est autorisé, aucune approbation clinique/privacy/security indépendante disponible, aucune mutation de Neon ni de vraie donnée patient. **NO-GO pour merge, PROD et certification** tant que les preuves ci-dessus manquent. Les 4/4 verts anciens ne certifient pas ce HEAD.

**Next exact** : publier PR DRAFT L0 SSE, lire les GitHub Actions exact SHA, corriger toute régression, collecter artefacts navigateur; préparer intégration combinée L0 #1140 + SSE #1056 et W01 seulement après les revues/gates.
