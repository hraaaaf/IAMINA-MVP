# IAMINA W01 — Preview synthétique sur main actuel — 04/11/2026

## Décision et périmètre

**Goal :** reproduire la version Web actuelle pour tester W01 Web → API → Neon synthétique, sans confondre la vieille branche du 17/10 avec la Production. **Succès :** builds Preview READY sur SHA runtime connu, URL API exacte embarquée, healthcheck et E2E synthétiques, identité DB et non-interférence vérifiées. **Preuves :** artefacts Vercel, réponses HTTP, logs et tests sur SHA exact. **État : NON CERTIFIÉ avant ces preuves.**

**Base GitHub vérifiée :** branche `preview/w01-current-main-synthetic-20261104` créée depuis `main@d7d650a082300486764019c8238f591057210d54` (04/11). La production Web actuellement publiée est `main@92f61c34522950c62f90c82dbcbc522c9cdd9c4a`, 2 commits derrière ce HEAD (modifications documentaires). Les protections W01 sont **déjà présentes dans main**, dans `frontend/vercel_build.sh` : contrôle ID projet, allowlist URL API Preview, `IAMINA_REMOTE_ACCOUNT_ENROLLMENT=false` et rejet de configuration manquante. `frontend/vercel.json` et `backend/vercel.json` désactivent le déploiement Git automatique. Aucun cherry-pick d'une ancienne branche nécessaire.

**API Preview** : projet `iamina-certified` `prj_Pn9FnyconF3h2w9gOU74iV98kJoU`, déploiement `dpl_5o2Fkjq5sp39nTKk6hkMdxjo16bG`, `https://iamina-certified-96wlik6wo-achraf-benmoussa-s-projects.vercel.app`, Git SHA `d7d650a082300486764019c8238f591057210d54`, target Preview (non Production).

**Web Preview** : projet `iamina-review` `prj_AYaUi32KTDHak8I7dmdQpDrqd8SI`, déploiement `dpl_FvycJYz9iNLRPmA6Wy1LWJDabRtS`, `https://iamina-review-32d3hrble-achraf-benmoussa-s-projects.vercel.app`, même Git SHA, target Preview. Variable `IAMINA_REVIEW_PREVIEW_API_BASE_URL` branch-scoped uniquement sur `preview/w01-current-main-synthetic-20261104` et fixée sur l'URL exacte API ci-dessus (Vercel env ID `JE9CVjqNmNIC75HI`).

**Garde-fous :** GO utilisateur pour Preview uniquement, aucune modification Neon Production, aucun déploiement Production, aucun patient, aucun merge. La branche de déploiement et la branche de documentation peuvent diverger après ce fichier : la certification doit viser **le SHA réellement déployé** `d7d650a...`, pas la tête documentaire.

## Tests à effectuer

- [ ] Vercel Web et API READY ; inspecter les logs de compilation.
- [ ] HTTP API Preview `/api/v1/health` = 200 et `db=ok` ; cache documenté sans extrapolation.
- [ ] HTTP Web Preview = shell Flutter ; bundle contient **uniquement** l'URL API Preview autorisée.
- [ ] Browser E2E synthétique, SSO/bypass CI contrôlé, API/DB fingerprint non secret = Neon sandbox.
- [ ] API rejette accès non autorisés (401/403), CORS/CSRF, résilience panne.
- [ ] 39 tables métier synthétiques restent à zéro en fin de test ; aucune requête/mutation Production.
- [ ] G6 restauration distante isolée, G2 protection Production, G7 revue/CI et closeout.

**Verdict :** W01 NO-GO jusqu'à preuves complètes.
## W01 — Correctif connexion A/B, 04/11/2026 — CANDIDAT NON DÉPLOYÉ

**BEFORE observé sur iPhone Safari :** écran d'activation locale sans entrée compte. Cause : `IAMINA_REMOTE_ACCOUNT_ENROLLMENT=false` dans Web Preview bloquait aussi le choix de connexion.

**Goal :** permettre le login des deux comptes synthétiques existants via API Preview, sans autoriser leur création, sans changer Production ni l'isolation local-first.

**Implémentation candidate :** nouveau flag `IAMINA_REMOTE_ACCOUNT_SIGN_IN=true` sur Preview et Production, mais Preview conserve `IAMINA_REMOTE_ACCOUNT_ENROLLMENT=false`. La séparation conserve le comportement Production antérieur. Le point d'entrée local affiche « Se connecter avec un compte existant » en Preview ; écrans FR/AR masquent inscription, démo et réinitialisation de mot de passe en mode synthétique. `AuthService.registerWithEmail` refuse toujours l'inscription sur ce build. Le flag historique `IAMINA_REMOTE_ACCOUNT_LOGIN_ENABLED` qui forcerait le même domaine Web pour les appels Chopper n'est **pas activé** : les deux projets Vercel Web/API ont des domaines distincts.

**Succès requis / Proof non acquise :** CI exécutée sur HEAD candidat (3 jobs applicatifs effectivement run), tests Flutter ciblés avec flags Preview, capture AFTER sur même iPhone/390/768/1280, vérification du POST /api/v1/auth/login contre **l'URL API Preview exacte**, CORS/CSRF, contrôle de l'inscription aussi au niveau API, account A/logout/B et rejet cross-patient, fingerprint Neon runtime et non-interférence Production, revue indépendante. **Aucun nouveau déploiement Vercel ni merge autorisé par la modification de code : Preview requiert un GO de déploiement distinct.** W01 demeure NON CERTIFIÉ.

### W01 — garde serveur contre inscription directe en Preview (candidat non déployé)

Audit adversarial : la limitation du formulaire et le refus `AuthService.registerWithEmail` ne suffisent pas, car `POST /api/v1/auth/register` reste accessible directement. Correctif backend proposé sur la même branche : rejet 403 **avant toute requête ou création d'utilisateur** lorsque `VERCEL_ENV=preview` ou `IAMINA_ENV=preview`, sauf opt-in explicite serveur `IAMINA_PREVIEW_ALLOW_REGISTRATION=true` pour tests positifs distincts. En Production, comportement inchangé. Tests négatifs et non-régression ajoutés. **Pas encore prouvé sur l'API déployée** : le SHA runtime existant `d7d650a` n'inclut pas cette protection ; elle dépend d'un déploiement Preview autorisé, puis d'un HTTP 403 observé. Ne pas prétendre qu'une Preview en cours refuse déjà l'inscription.
