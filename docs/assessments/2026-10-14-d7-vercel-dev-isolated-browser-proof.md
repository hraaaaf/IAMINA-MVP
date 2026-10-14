# IAMINA D7 — Vercel DEV preview / navigateur isolé — preuve du 14 octobre 2026

**Statut : PASS — limited browser scope. Ne remplace pas l'essai clinique A→B→A sur deux appareils physiques.**

## Goal et succès observable
Goal : compléter la CI D7 verte de la PR #986 par une Preview de développement isolée, navigable dans un véritable navigateur et vérifiée avec deux contextes indépendants, sans aucune requête au backend certifié. Critère de succès : Preview READY, capture Chrome mobile+desktop, isolation localStorage + IndexedDB, état conservé après bascule offline sur page déjà chargée, aucun appel au domaine backend certifié, aucune erreur JS observée.

## Cadrage source — sécurité
- PR fonctionnelle D7 [#986](https://github.com/hraaaaf/IAMINA-MVP/pull/986) OPEN/DRAFT, HEAD du code certifié `c9577c8ea6d6233f7b49b260436909f592e9a37e`, 17/17 workflows SUCCESS. **PR et main non modifiés par ce lot.**
- Le script normal `frontend/vercel_build.sh` du projet `iamina-review` relie le frontend au backend **`iamina-certified.vercel.app`**, y compris lorsque construit en Preview. Pour protéger le backend, ce test a créé une branche d'audit indépendante.
- Branche `audit/d7-vercel-preview-offline-20261014` issue de la PR : build isolé commit `a8486c974a5f9f6a10da1d83fb77b6257b33d6b1`. **Garde explicite** `VERCEL_ENV=preview`, `VERCEL_PROJECT_ID=prj_AYaUi32KTDHak8I7dmdQpDrqd8SI` ; `IAMINA_OFFLINE_DEMO=true`, `IAMINA_REMOTE_ACCOUNT_ENROLLMENT=false`, `API_BASE_URL=https://iamina-d7-preview.invalid` (hôte inexistant). Aucun autre environnement modifié.
- Vercel project `iamina-review`, team `team_NNhXPDOIfjGNBcn253btpyk0`. Preview ID `dpl_MuEwzm8Pvx8BYqEKA55kSkKp5GS6` : **READY**, `target=null` (Preview, pas production), URL https://iamina-review-la39twh0a-achraf-benmoussa-s-projects.vercel.app
- Production contrôle : déploiement précédent `dpl_CJpLFLEQngvjsZXj23FinoXYoH1t` toujours READY, alias officiel `iamina-review.vercel.app`, code `1e44ba57ad63638b1eb15af916adc54d0f8c15fc`. Aucun promote, rollback ou changement d'alias.

## Preuve exécution navigateur réel
- Workflow GitHub **[IAMINA D7 Isolated Vercel Preview Browser Smoke #38580529227](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38580529227)**, HEAD de branche audit `d502613e79d83dc0739b1deae371fd147d12df0c`, SUCCESS.
- Artifact **#11901704607**, `iamina-d7-vercel-dev-two-context-smoke`, GitHub SHA-256 `4ad19ce96688b64621ad047d62841ffd3c606e675f192527d040c8662f6a8386`. ZIP téléchargé et ouvert : `proof.json` + screenshots `preview-390x844-context-A.png`, `preview-1280x900-context-B.png`, dimensions vérifiées et images inspectées.
- Client Chromium via Playwright : session A mobile 390×844 et B desktop 1280×900 indépendantes. `localStorage` et `IndexedDB` marqueurs synthétiques distincts A/B puis relecture A préservée : PASS. Ce sont deux *browser contexts*, PAS deux identités médicales authentifiées.
- Les deux pages répondent HTTP 200 et affichent l'écran local initial (« Set up IAmina here »), textes visibles, CTA présent, aucune collision visuelle majeure observée.
- Aucun hostname `iamina-certified.vercel.app` dans la bundle compilée ; **0 requête à ce hostname observée**, aucun pageerror dans cette session ; pas de donnée patient et pas de requête API réelle. 
- Après `context.setOffline(true)`, `navigator.onLine=false` et le marqueur local A demeure visible sur la page ouverte. **Un redémarrage hors ligne sans réseau n'a pas été réalisé** par ce test ; le workflow P5-4A distinct a une preuve de reload offline sur sa propre app-shell synthétique, ce n'est pas une validation clinique D7.
- Résultat calculé par le test : `PASS_LIMITED_SCOPE`. Ce n'est pas une certification sécurité complète, ni un score UX D7.

## Limitations / Next
1. Tester sur **2 appareils physiques** les parcours *authentifiés* A→logout→B→A, offline/outbox, confrontation 409, confirmation serveur sans écrasement, et traces réseau.
2. Provisionner un **backend de test séparé** avec identités et stockage persistants isolés si l'on veut pousser l'E2E distant au-delà des simulations. Ne **jamais** réutiliser `iamina-certified` à cette fin.
3. Valider la protection clinique/consentement de synchronisation (D30 #988/#989/#990), revue médicale et privacy indépendantes, puis screenshots BEFORE/AFTER de la modal 409 réelle et acceptation humaine.
4. Le GOAL D7 produit reste OPEN ; **PAS DE MERGE, PAS DE VERCEL PRODUCTION, PAS DE VRAI PATIENT**. Avancement global P5 historique 6/12 = 50 %, inchangé.

**Fichier canonique D7 produit** : `docs/handovers/2026-10-13-iamina-d7-revue-profil-medical.md` sur la branche D7. Ce dossier d'audit ne le remplace pas.
