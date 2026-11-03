# IAMINA Chantier A — D12 Web : garde numérique glycémie après D22 / D13

**Date** : 2026-11-03  
**Décision** : D12, issue [#971](https://github.com/hraaaaf/IAMINA-MVP/issues/971)  
**Statut** : garde D12 **VALIDÉE TECHNIQUEMENT et déployée en production** sur SHA exact `7697a179caec0b094e589fbb8775b967754853c4` (12/12 workflows SUCCESS). Vercel READY/alias public vérifiés, PR Draft #1251 non fusionnée. Recette authentifiée iPhone/revue indépendante et D32 clinique non validées ; un commit docs-only ultérieur n'est pas le SHA déployé.

## Goal, succès, preuve

- **Goal** : empêcher tout enregistrement de glycémie non finie/absente/négative ou d'un débordement de conversion, sans inventer de mesure, de seuil médical ni changer les données valides.
- **Succès** : la saisie et le bouton Enregistrer refusent les valeurs non finies et les unités non supportées ; aucune ligne Drift créée dans le test d'entrée invalide ; la conversion D22 et sa valeur canonique restent invariantes lors des bascules d'unité.
- **Preuve requise** : CI Flutter exacte sur cette branche, contrats purs, test widget SQLite réel FR/AR, audit de non-régression D13 et comparaison avec la baseline de production.

## Baseline vérifiée, BEFORE

- Base de la branche : `0b2ad7e1366c68ba3cafef785e602a67b1f0953b`, **commit exact D13 Web réellement publié** sur Vercel `iamina-review.vercel.app` le 2026-11-03.
- `AddLogSheet._displayGlucose` utilisait `double.tryParse` sans `isFinite`; le bouton ne vérifiait que `> 0`, et `_saveLog` rejetait `null` ou `<=0`. Un `Infinity` positif ou une conversion `mmol/L*18.0` débordante pouvait passer la garde (risque constaté **dans le code**, pas incident patient).
- D22 introduit le cadran semi-circulaire, la saisie libre, la préférence mg/dL ↔ mmol/L et le cache canonique `_canonicalUnitSwitchMgdl` pour éviter l'arrondi répété à chaque bascule.
- D13 conserve son refus de retour/navigation pendant `_saving` et la garantie d'un seul INSERT.

## Correctif ciblé, AFTER candidat

- Helpers purs `parsePositiveFiniteGlucoseInput` et `normalizeFiniteGlucoseMgdl` : rejettent `NaN`, `±Infinity`, absent, négatif, zéro, débordement ou unité inconnue ; conservent exactement le facteur **18.0 déjà présent**, sans seuil clinique ajouté.
- `_mgdlGlucose` protège **également la voie du cache canonique D22** en vérifiant unité valide, valeur de saisie finie et cache fini/positif ; les bascules arrondies restent des présentations seulement.
- Bouton Enregistrer activé uniquement si **valeur mg/dL réellement normalisable** ; `_saveLog` applique la même garde immédiatement avant toute écriture Drift.
- Pas de nouvelle limite de saisie, plage de slider, couleur de repère, interface ou valeur par défaut. **Changement visuel attendu : aucun** ; mockup et comparaison BEFORE/AFTER non nécessaires tant qu'aucune UI n'est modifiée.

## Tests et risques

- `frontend/test/features/dashboard/add_log_finite_post_d22_contract_test.dart` : rejets purs NaN/Infinity, overflow fini×18, décimales virgule, unité inconnue, pas de préremplissage ; widget en **FR et AR** avec vraie `NativeDatabase.memory()`, 400 chiffres (Inf/overflow), bouton désactivé, SQLite vide, puis 126 → 7.0 → 126 sans arrondi cumulatif et INSERT unique de 126 mg/dL.
- Les tests D13 existants doivent rester verts ; la non-persistance des invalides est prouvée dans le widget, sans donnée patient réelle.
- Une valeur finie peut rester médicalement invraisemblable : **ne pas transformer ce garde technique en validation médicale**. Évaluation clinique bornes/slider et repères D22 : D32 et avis clinicien.
- Si les tests échouent : corriger sur branche, relancer une CI exact HEAD ; pas de merge ni Vercel sans GO distinct.
- PR D12 originale [#972](https://github.com/hraaaaf/IAMINA-MVP/pull/972) issue d'une base périmée, `mergeable:false` : ne pas cherry-pick, superséder une fois le nouveau candidat prouvé.

## Validation technique vérifiée — 2026-11-03

- [CI Flutter #41693563541](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41693563541) **SUCCESS** sur commit exact `1032bdec80f77256831bf0f50c10d167c5675d62` : `flutter analyze` SUCCESS, **984 tests réussis, 7 skipped**, bundle PWA `build/web` compilé, intégrité de sortie vérifiée ; jobs backend/PG skipped car le delta D12 n'en modifie aucun fichier.
- Dans les logs du job Flutter #126120113809 : **9/9 cas D12 PASS** = trois contrats numériques purs + six cas widget FR/AR × 390×844, 768×1024, 1280×900, avec vrai SQLite ; zéro mesure invalide et une seule entrée à 126 mg/dL après bascule aller-retour. Les assertions n'emploient pas de mesures patient réelles.
- [FUE D13 Chrome #41693563506](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41693563506) **SUCCESS 6/6** sur le même SHA : sauvegarde SQLite bloquée, refus app-back et browser-back, reçu et exactement une mesure 126 mg/dL après rechargement, pour FR/AR × 390/768/1280.
- **12/12 workflows GitHub SUCCESS, 0 en cours/échec** sur `1032bdec80f77256831bf0f50c10d167c5675d62`. Ces preuves sont synthétiques et ne remplacent ni une recette Web authentifiée en production ni une validation clinique.
- Portée code vérifiée `compare_commits` : parent D13 publié `0b2ad7e...` → ce SHA D12 = **3 fichiers seulement** (un widget source, un test, un .md), **0 fichier backend**. Vercel Production demeure sur D13 `dpl_9XFXHNP2gSJAvbt3B6M7EBNM4dSN` READY. Aucune release D12.
- **Gates persistants :** revue indépendante, recette Web réelle/iPhone, décisions cliniques de bornes/slider dans D32, GO explicite distinct pour tout merge ou Vercel. Une CI verte ne suffit pas à déclarer D12 mise en production.

## Déploiement direct en production — vérifié 2026-11-03

- **GO utilisateur explicite :** « Pk en preview !? Directement to prod ». Aucune preview préalable, action ciblée D12 Web.
- **Commit code+docs publié** : `7697a179caec0b094e589fbb8775b967754853c4`, [GitHub CI #41696210864](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41696210864) **SUCCESS 12/12 workflows**, 984 tests Flutter PASS/7 skipped, PWA build et [D13 Chromium #41696210601](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41696210601) SUCCESS 6/6.
- **Vercel frontend seulement** : `iamina-review`, project `prj_AYaUi32KTDHak8I7dmdQpDrqd8SI`, deployment `dpl_AzTqctoykcFwtvSsTT1bomBn5i9h` **READY** target production ; `get_project.latestDeployment` identique et `aliasError=null`. URL publique : **https://iamina-review.vercel.app** (alias vérifié par `list_deployment_aliases`).
- **Observabilité** : `get_runtime_errors` last 30m aucun résultat ; `get_runtime_logs` erreur/fatal du déploiement aucun log, ne valide pas le comportement Flutter client ni les navigations authentifiées.
- **Gouvernance** : [PR #1251](https://github.com/hraaaaf/IAMINA-MVP/pull/1251) OPEN/DRAFT/non mergée, base D13 (`0b2ad7e...`), diff GitHub **3 fichiers**, pas de backend déployé ni de migration DB. Notion Chantier A actualisé.
- **Reste à tester sur iPhone Web** (données synthétiques seulement) : saisir 126 mg/dL → bascule 7.0 mmol/L → retour 126 mg/dL, enregistrer, reçu et exactement une ligne après recharge ; sortie depuis brouillon (confirmer/garder), retour pendant insertion, FR/AR, absence de valeur/overflow interdit. La revue externe, le test réel sur compte et la qualification clinique D32 sont des gates distincts **non validés**.
- **Traçabilité** : le présent chapitre est un *commit documentaire post-release*. Le SHA déployé reste `7697a179...` et ne doit pas être confondu avec le SHA produit par cette mise à jour du .md. Aucun nouveau déploiement n'est nécessaire pour ce commentaire documentaire.

## Reprise

Branche : `fix/a-d12-web-finite-post-d13-20261103`  
Parent : `fix/a-d13-web-post-d22-20261103@0b2ad7e...`  
Next : [PR DRAFT #1251](https://github.com/hraaaaf/IAMINA-MVP/pull/1251) ouverte, toujours non mergée ; **base D13 rétablie et vérifiée**, delta **3 fichiers**. Ancienne PR #972 CLOSED sans merge. D12 Web **production déployée sur SHA `7697a179` avec GO propriétaire explicite**. Reste : recette authentifiée iPhone/Web avec données de test, revue externe, correction si anomalie puis nouvel accord avant tout autre déploiement/merge. D32 clinique hors périmètre.
