## 23/10/2026 — Épreuve Chrome SSE POST autonome, sans chat patient réactivé

Candidat de nouveau workflow `.github/workflows/sse-post-synthetic-browser-proof.yml` : réutilise le backend synthétique et Chromium de #1144 pour contrôler vrai `POST /api/v1/ai/chat/stream`, 200 SSE, `[DONE]`, canari absent URL/log d'accès local, no-store et cache PWA initial correct ; **retire** les anciens gestes chat/saisie et l'attente de réponse UI, incompatibles avec Web RELEASE local-only. Capture l'état du navigateur sans interpréter la messagerie comme ouverte. Conserve en parallèle, sans changement, le workflow `companion-chat-e2e-screenshot.yml` issu de #1140 qui certifie le refus de l'egress clinique dans l'UI. Le proxy test peut conserver un enregistrement temporaire de réponse synthétique, mais aucune capture/message réel n'est attendu ou publié.

**Preuve : non exécuté sur ce nouveau SHA avant CI**. À vérifier avant CLOSEOUT. Aucun patient réel, aucune activation serveur ni déploiement Vercel.

---

# IAMINA Web — L0 Release Candidate Integration — 23 octobre 2026

## Goal / Succès / Preuve

**Goal :** combiner **sans déploiement ni merge sur main** les quatre protections déjà codées et approuvées par CI séparées :
- [Réseau local-only/UX #1140](https://github.com/hraaaaf/IAMINA-MVP/pull/1140), HEAD `3249c5ca`, **9/9 CI SUCCESS** : client CGM/Companion fail-closed et interface honnêtement désactivée Web RELEASE.
- [Glycémie #1141](https://github.com/hraaaaf/IAMINA-MVP/pull/1141), HEAD `337a7e73`, **8/8 SUCCESS** : rejet NaN/Inf/overflow et navigation bloquée durant write Drift.
- [D11 #1142](https://github.com/hraaaaf/IAMINA-MVP/pull/1142), HEAD `450c0f93`, **6/6 SUCCESS** : zéro demo medical data dans compte patient, setup_demo refusé sur PostgreSQL.
- [SSE/CSRF #1144](https://github.com/hraaaaf/IAMINA-MVP/pull/1144), HEAD `288bfefb`, **4/4 SUCCESS** : POST-only SSE JSON, plus de patient message dans URL, auth/CSRF et egress scope.

**Provenance technique :** base main `8ada5aab8e8006bbbdc275eabbabf014a4714e0b`, 48 fichiers uniques modifiés dans l'union des quatre PR, dont **deux seuls conflits de chemin explicitement résolus** :
1. `.github/workflows/companion-chat-e2e-screenshot.yml` : choisir **la preuve local-only qui refuse l'HTTP et cache le chat patient Web RELEASE**, issue de #1140 ; ne pas rétablir les anciennes affordances médicales interactives de #1144.
2. `docs/api/openapi.json` : fusionner **le texte 403 de D11 /demo/seed** ET le **POST /ai/chat/stream** de #1144. Pas de rollback de l'un au profit de l'autre.

Tous les autres blobs sont copiés de leurs commits de provenance **sans réécriture**. Ce candidat n'inclut pas le **workflow Chrome SSE POST spécifique** de #1144 comme job distinct : la preuve précédente reste accessible [#39939744853](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39939744853), mais la **preuve navigateur SSE au SHA combiné manque encore** et devra être intégrée à part en gardant l'UI du chat désactivée. Ceci est un point de revue et un **gate de livraison**.

**Succès observable à tester** : CI complète exact SHA, source API OpenAPI, refus 405/403/auth, zéro fausse donnée patient, glucose fini et save in-flight, PWA recovery & browser persistence, Chrome CGM/Companion local-only, FR/EN/AR × 390/768/1280 BEFORE/AFTER, absence de fuite HTTP et erreur console. **Toutes les anciennes CI vertes sont des preuves séparées, pas preuve combinée.**

**Autres gates bloquants** : W01 #1128 NO-GO (compte A→B→A, DB runtime, Redis/CSRF, review), sécurité/privacy indépendants, avis clinique urgence #1134, tests réels tactiles, score certifié ≥9.0. Toute fusion de main pourrait déclencher Vercel Production : **aucune fusion, aucune Vercel Preview/Production, ni données réelles autorisée** pendant ce travail.

**Next exact** : publier draft intégration, CI exact SHA, corriger les erreurs, contrôler les artefacts et les interactions croisées ; isoler l'épreuve Chrome SSE synthétique sans réactiver la messagerie patiente ; obtenir revues avant merge/Production.
