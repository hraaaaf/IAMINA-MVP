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

## Recette production — acceptation propriétaire du 02/11/2026

**Preuve directe :** le propriétaire a confirmé explicitement **les cinq vérifications sur la production `f78f0fa`, 5/5 validés, 0 non validé, « Observations : aucune »**. Il ne s'agit plus d'une simple Preview. Ces observations correspondent exactement à la checklist qui lui a été présentée, sans test supplémentaire supposé.

- [x] Le demi-camembert apparaît dans **Nouvelle mesure**, sans boutons `−/+`.
- [x] Le curseur suit le doigt **sans faire défiler la page pendant ce geste**.
- [x] La saisie centrale et la bascule `140 mg/dL ↔ 7,8 mmol/L` fonctionnent.
- [x] Les cinq couleurs et leurs transitions sont correctes.
- [x] Une **mesure fictive** est enregistrée et apparaît dans le **Journal**.

**Niveau de preuve :** `USER_REPORTED_PUBLIC_IPHONE_SMOKE_PASS_5_OF_5`. Le contrôle automatisé d'accès à la SPA publique était auparavant indisponible (extracteur `empty_content`) ; il **n'a pas été exécuté avec succès depuis un navigateur indépendant**. Le retour utilisateur est une preuve fonctionnelle de recette réelle, pas une télémétrie instrumentée, ni un test clinique.

**Non affirmé :** isolation des dossiers entre deux comptes (test A→B), preuve de consentement, capture AFTER indépendante, origine/autorité de chaque cible, précision de conversion clinique globale, homologation sécurité/privacy/CGM. L'app peut conserver des comportements préexistants hors du périmètre de ces cinq vérifications. Si un incident est remonté, reprendre le diagnostic et éventuellement le rollback au déploiement READY identifié.

## Closeout / suite

**Sous-lot UI :** `MERGED_AND_PRODUCTION_READY_ALIAS_VERIFIED` + `USER_IPHONE_SMOKE_ACCEPTED_5_OF_5` — **CLOS pour ce périmètre produit Web**.  
**Next exact hors sous-lot UI :** garder l'écran validé et reprendre la décision clinique D22 avec arbitrages documentés G1 provenance, G4 unité/conversion/arrondi, G7 legacy/isolation/backup/rollback, puis FUE FR/AR, validation humaine proportionnée au risque avant activation de tout traitement clinique.  
**Ne pas confondre :** PR clinique D22-B #1214 toujours DRAFT/non mergée ; aucune certification clinique globale ni 17/17 décisions produit certifiées n'est impliquée.

**Git commit documentaire futur :** ce fichier est un closeout documentaire sur main ; n'est pas le SHA binaire de la production `f78f0fa`. Les auto-déploiements Vercel depuis Git sont désactivés.
