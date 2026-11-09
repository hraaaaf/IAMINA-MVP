# IAMINA — D7 Web : BEFORE / AFTER de la transition du type de diabète

Date : 29 octobre 2026. Périmètre : PR [#1164](https://github.com/hraaaaf/IAMINA-MVP/pull/1164) **test-only**, non certification de la décision clinique D7. Sources : `main` avant le merge `16a5d9d2ce34fb005bf325d536dfeefdd0adf4d4` ; après le merge `538ec3f555e4f2699f402b093533f781048c8118`.

## Goal / succès / preuve

**Goal :** empêcher qu'un changement déclaré de type de diabète supprime ou modifie silencieusement les traitements déjà renseignés, tout en laissant à la personne l'initiative de changer sa déclaration.

**Succès du sous-lot test :** ajouter un test Flutter D7 FR puis AR/RTL pour Type 2 → Type 1 → inconnu ; aucune modification de code, affichage, seuil clinique, persistance, API, DB, synchronisation ni déploiement. **Preuve :** diff GitHub avant/après, SHAs Git, CI et test widget (prémerge [#40788484834](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40788484834), [E2E pilote #40788484908](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40788484908), tous deux SUCCESS sur HEAD prémerge `9da10a6f0056cd16cdc5c7c2df506e3c2ce91b77`). Fusion squash [#1164](https://github.com/hraaaaf/IAMINA-MVP/pull/1164) → `538ec3f555e4f2699f402b093533f781048c8118`.

## BEFORE → AFTER — comparaison code et comportement prouvable

| Dimension | BEFORE (main `16a5d9d2`) | AFTER (main `538ec3f5`) | Preuve |
|---|---|---|---|
| Composant Flutter de traitements | Code présent | **Identique** | Blob `6cd8e3312cf2376fc64f98e5e3d1c206aefe6734` dans les deux |
| Modèle de déclaration D7 | Code présent | **Identique** | Blob `3c036782072db2ac386e71cbef509f20f7511f04` |
| Onboarding Web | Code présent | **Identique** | Blob `a4cd7897de4f21e2f23fadfa65969aaddef51d54` |
| Stockage local déclaration | Code présent | **Identique** | Blob `ff189df220c299178af566a6a41d3354ada6682b` |
| Test Type 2 → Type 1 → inconnu | Fichier absent | **Test ajouté : 94 lignes** | `frontend/test/features/profile/d7_web_type_transition_contract_test.dart` |
| Saisie patient | Aucune modification explicite de comportement | Aucune modification explicite de comportement | Test vérifie que les codes de traitements persistent sans action patient, puis qu'une sélection expresse les change |
| FR / AR | Code et libellés existants | Code et libellés inchangés ; test bilingue ajouté | Test widget FR puis `Locale('ar')` |
| Visuel, layouts, scroll, accessibility | Code UI existant | **Zéro différence source UI** | Git compare du merge : **1 fichier ajouté, aucun fichier runtime/UI modifié** |

**Attention :** zéro différence source UI est une preuve d'absence de modification UI dans cette PR, **pas une capture BEFORE/AFTER de navigateur ni une certification FUE**. Aucun mockup ou capture artificiellement dupliquée n'est utilisé. Les captures Chrome FR/AR du lot Web précédent [#1168](https://github.com/hraaaaf/IAMINA-MVP/pull/1168) restent des preuves de son propre périmètre/commit et ne valident pas la transition D7 en vraie session.

## Matrice de scénarios

| Scénario | Test / observation | Verdict limité |
|---|---|---|
| Déclaration Type 2 `oral_meds + insulin` → Type 1 | Rebuild widget, compteur `onChanged` reste nul, codes préservés, chips visibles | **PASS — widget sur HEAD prémerge** |
| Clic explicite sur `oral_meds` | `onChanged=1`, insulin reste, oral supprimé | **PASS — widget sur HEAD prémerge** |
| Passage Type 1 → inconnu, AR | `onChanged` ne monte pas, insulin reste visible | **PASS — widget sur HEAD prémerge** |
| Patient choisit « aucun traitement » en AR | État `noneDeclared`, liste vide, compteur à 2 | **PASS — widget sur HEAD prémerge** |
| Vrai Chrome FR/AR aux 3 viewports pour cette transition | Non démontré par ce test | **NOT_RUN — FUE** |
| A→logout→B→A, sauvegarde/reload/offline multi-session | Non démontré par ce test | **NOT_RUN — sécurité/persistance** |
| Validation clinique/privacy de toute D7 | Non démontrée | **NO_GO global D7** |

## Gates et limites

- Tests prémerge #1164 : **2/2 SUCCESS** sur `9da10a6f0056cd16cdc5c7c2df506e3c2ce91b77`.
- Runs post-merge vérifiés sur `538ec3f555e4f2699f402b093533f781048c8118` : [CI #40842001176](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40842001176) **COMPLETED/SUCCESS** (frontend analyze, Flutter tests et PWA build) et [E2E pilote #40842001292](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40842001292) **COMPLETED/SUCCESS**. Les tests E2E génériques ne remplacent pas la matrice FUE complète de la décision D7.
- Aucun changement sur `frontend/vercel.json` ni `backend/vercel.json` : `git.deploymentEnabled=false` dans les fichiers ; ce paramètre code ne prouve pas à lui seul l'absence de toute automatisation cloud. **Aucun déploiement Vercel n'a été lancé par ce lot.**
- **D7 reste OPEN / FUE_NO_GO** pour son périmètre complet : vraie première utilisation FR/AR, vues 390×844/768×1024/1280×900, clavier/tactile, comptes, offline, persistance et validation risque santé / confidentialité. Ne jamais confondre merge d'un test et validation médicale.
- **Next exact :** conclure CI/E2E postmerge D7, puis test FUE Web réel de transition et persistance sur sandbox synthétique, revues clinique/privacy ; reprendre ensuite D22 sous dépendance D19, sans fixer arbitrairement de cibles ni déployer Vercel sans GO.

Références : [Roadmap](../ROADMAP.md), [D7 revue historique](2026-10-13-v1-d7-medical-profile-relevance.md), [Notion tri D1–D30](https://app.notion.com/p/40777c6633628177b325d3cb5412fc18).
