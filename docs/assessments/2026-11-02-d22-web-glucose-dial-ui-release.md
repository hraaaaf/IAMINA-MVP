# IAMINA — D22 Web / Demi-camembert Nouvelle mesure — Release UI isolée

**Date :** 2026-11-02  
**Périmètre :** Flutter Web/PWA uniquement — saisie manuelle d'une glycémie  
**État :** `UI_OWNER_ACCEPTED` + `PR_UI_MERGED` + `PRODUCTION_VERCEL_READY_ALIAS_VERIFIED`  
**Hors périmètre :** décisions cliniques D22-A/D22-B, cibles individuelles, migration, CGM/TIR, API et backend.

## Goal, succès et preuve

- **Goal :** livrer le demi-camembert de la page **Nouvelle mesure** sans intégrer la PR clinique empilée de 79 commits.
- **Succès UX :** propriétaire **6/6 validés** sur Preview intégrée D22-B : 40 mg/dL rouge, 80 orange, 140 vert, 170 orange, 240 rouge symétrique, transition fluide ; aucune objection. **Aucune nouvelle note /10**.
- **Succès de périmètre :** [PR UI isolée #1218](https://github.com/hraaaaf/IAMINA-MVP/pull/1218) : **1 commit, 8 fichiers**, 3 fichiers Flutter runtime et 5 tests. Comparaison main → PR `1 ahead / 0 behind`. Aucun changement de schéma Drift, cibles, onboarding, moteur TIR, API, migrations.
- **Preuve CI :** HEAD de PR `fd7711c32c2fe4d66b6e6ccd0c80fcb39d5f3b6e` : **8/8 GitHub workflows SUCCESS** ; Flutter CI, audit responsive et UI browser screenshot certification [#41447113806](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41447113806), artefacts aux tailles **390×844**, **768×1024**, **1280×900**.
- **Merge vérifié :** GitHub `merged=true`, squash dans main `f78f0fad6f26b3a8cfc344cb22b87932e684f140`. Les **8 blobs postmerge** ont été comparés aux blobs testés sur la PR : **8/8 identiques**. Aucune nouvelle CI sur le SHA squash main observée (`0 runs`), donc ne pas inventer `8/8 CI main`.
- **Preview isolée :** [Vercel READY](https://iamina-review-56xzz915o-achraf-benmoussa-s-projects.vercel.app), deployment `dpl_HBy9AyjU6q6cCAFLcwDfEKrWZ2vJ`, SHA `fd7711c`, `target=null`.
- **Production Flutter :** [https://iamina-review.vercel.app](https://iamina-review.vercel.app) ; Vercel deployment `dpl_9NDSeoz18VLEdG6V4NNF1znFuFMv`, `target=production`, `READY`, git SHA `f78f0fa`. **GET Alias Vercel confirme `iamina-review.vercel.app` → `dpl_9NDSeoz18VLEdG6V4NNF1znFuFMv`**, projet `prj_AYaUi32KTDHak8I7dmdQpDrqd8SI`.
- **Backend :** `iamina-certified` non déployé ni modifié. Le script de build existant lie la production Web au backend actuel `https://iamina-certified.vercel.app`, sans changement de configuration.
- **Rollback identifié, non invoqué :** ancienne prod READY `dpl_DyVNLd3dA4EuUk4aiYaX1HRGqhSz`, commit `d4fdf6d4b2046b0633ca77c7de80be4d3b53bb60`. Opération Vercel `request_rollback` uniquement si incident, puis vérifier alias après action.

## Contrôle de périmètre et sécurité

Le composant visuel montre **rouge → orange → vert → orange → rouge** avec limite graphique générique 70–180 mg/dL et mention qu'il ne s'agit **pas** d'une cible personnalisée ; le warning de mesure basse historique est séparé. Les changements de présentation n'ajoutent pas de données cliniques ni de nouvelles tables. L'unité de brouillon mg/dL/mmol/L utilise le facteur historique `18.0` de la chaîne journal ; la mesure canonique pré-changement d'unité est préservée au moment du toggle. **Ne pas interpréter cela comme contrat scientifique global du facteur ou de provenance source**.

**Sources de référence externes :** [ADA Standards 2026, §6](https://doi.org/10.2337/dc26-s006) — cibles individualisées, TIR fondé sur CGM ; [FHIR Quantity R5](https://hl7.org/fhir/R5/datatypes.html) — unité explicite et code UCUM à la frontière ; [NIST Glucose](https://webbook.nist.gov/cgi/cbook.cgi?ID=50997) — masse molaire 180.1559, facteur théorique 18.01559 ; [CNDP Maroc](https://www.cndp.ma/conditions/) — obligations sur traitement de données relatives à la santé, qualification juridique spécifique dépendant de la finalité.

**Important :** Cette livraison de l'UI **ne certifie pas l'état clinique préexistant de main**. [PR clinique D22-B #1214](https://github.com/hraaaaf/IAMINA-MVP/pull/1214), [D22-A #1213](https://github.com/hraaaaf/IAMINA-MVP/pull/1213) et [D19 #920](https://github.com/hraaaaf/IAMINA-MVP/pull/920) sont restées OPEN/DRAFT/non fusionnées au dernier contrôle. G1/G4/G7 et FUE complets restent un travail distinct. Ne pas fusionner automatiquement #1214 après la fusion de #1218.

## Limites réelles / recette production restante

- **Prouvé :** build production READY, association domaine→deployment exact, branche merge et 8 blobs identiques.
- **Non prouvé :** recette navigateur réelle de l'URL publique sur iPhone **après production** : l'extracteur web renvoie `not accessible/empty_content` pour la SPA Flutter, et le conteneur ne résout pas le domaine (limite d'outil, pas preuve de panne). Ne pas affirmer un vrai smoke end-to-end hébergé.
- **Cases de recette propriétaire en prod sur mesure fictive uniquement :**
  - [ ] Ouvrir `Nouvelle mesure` ; un seul demi-camembert visible, sans +/− et sans slider secondaire.
  - [ ] Glisser sur l'arc : valeur change, **page immobile** ; hors cadran la page défile.
  - [ ] Éditer le nombre central au clavier ; bascule `140 mg/dL ↔ 7,8 mmol/L ↔ 140 mg/dL`.
  - [ ] À `40/80/140/170/240 mg/dL`, vérifier rouge/orange/vert/orange/rouge, ambiance et fluidité.
  - [ ] Enregistrer une mesure **fictive** sur compte de test, puis vérifier le Journal et l'absence de changement des données d'un autre compte.

## Closeout / suite

**Sous-lot UI :** `MERGED_AND_DEPLOYED_READY_ALIAS_VERIFIED`, **post-prod iPhone smoke = PENDING**.  
**Next exact :** retour du propriétaire sur les cinq cases en production ; incident si échec → diagnostiquer, rollback au deployment indiqué si nécessaire, puis retester. À défaut, accepter la livraison UI sans déclarer la décision clinique D22 certifiée.  
**Séquence clinique D22 distincte :** arbitrer provenance G1, contrat conversion/arrondi G4, protection legacy/isolation/backup G7, FUE risques élevés FR/AR et vraies métriques CGM ; revue proportionnée au risque avant un lot clinique.

**Git commit documentaire futur :** ce fichier est un closeout documentaire sur main ; n'est pas le SHA binaire de la production `f78f0fa`. Les auto-déploiements Vercel depuis Git sont désactivés.
