# IAMINA — Handover canonique V1-03 / OCR glucose unit provenance #923 / PR #932

**Date :** 2026-10-11. **Chantier :** V1-03 / sûreté clinique des unités d'OCR. **Source de priorité :** `docs/ROADMAP.md`. Le présent lot n'est ni une approbation clinique, ni un déblocage du flux externe multimédia.

## Goal / succès / preuve
- **Goal :** les lectures numériques issues de l'OCR d'un lecteur glycémique doivent échouer de façon sûre si l'unité affichée n'est pas explicitement et univoquement reconnue. Aucun `>30 mg/dL` ni `≤30 mmol/L` implicite ; aucune unité par défaut conduisant à une valeur interprétable.
- **Succès observable :** backend image fallback ne produit `value != null` que si `unit` est l'une des deux étiquettes reconnues ; Flutter OCR local ne propose pas de `value` pour nombre seul ou double étiquette. Les valeurs explicites et la conversion mmol/L restent fonctionnelles ; tests négatifs et positifs CI exacte verts.
- **Preuve actuelle :** diff de branche [DRAFT #932](https://github.com/hraaaaf/IAMINA-MVP/pull/932), code SHA `4fabb9f66ba9baaf6a5830466a6e9c05b068d136` : 4 fichiers vs parent #931, 2 commits ahead / 0 behind. **La CI documentaire exact-head reste à passer et son SHA sera distinct**, pas de statut CERTIFIED/VERIFIED avant ce verdict et la revue humaine clinique.

## Source du risque / implémentation
1. `backend/media/vision.py` demandait au provider de deviner l'unité sur magnitude et retombait sur mg/dL si `unit` était absente ou invalide. Désormais prompt explicite d'abstention et garde déterministe (`value is None`, unité absente/invalide, booléen, NaN ou infini : fallback). Le fallback conserve `unit:"mg/dL"` **seulement avec `value:null`** pour stabilité de contrat, jamais comme lecture validée. Le fait qu'un modèle affirme avoir lu une étiquette n'est **pas une preuve d'origine optique**.
2. `frontend/lib/core/clinical/glucose_ocr_shield.dart` choisissait auparavant mg/dL en l'absence de `mmol`. Désormais il détecte explicitement `mg/dL` ou `mmol/L`; unité absente ou ambivalente → résultat sans nombre, confiance nulle et UI de correction nécessaire. Le comportement spécial HI/LO préexistant reste hors de ce sous-lot ; l'analyse de toutes les voies UI actives et des cas cliniques doit être conduite.
3. Tests `backend/media/tests/test_vision_provider_boundary.py` : faux provider, cas sans unité, nulle, invalide, vide, nombre absent, chaîne nan, booléen, racine tableau ; positifs mg/dL/mmol/L. Tests Flutter `frontend/test/glucose_ocr_unit_provenance_test.dart` : 120 et 6.5 sans unité, étiquette incomplète, conflit double unité, valeurs explicites et conversion. Aucune image patient, aucun appel live ni données personnelles. Diff final cible 6 fichiers incluant ce handover et roadmap.

## Limites et gates
- Les tests de reconnaissance simulés vérifient **l'output shield**, pas l'exactitude de la vision du modèle ni des pixels. Le provider Gemini media reste derrière les garde-fous de consentement et egress V1-03 ; il ne devient pas autorisé par ce patch.
- Ni reachability exacte du helper Flutter depuis la production, ni tous les OCR/combinaisons de nombres, ni le geste de correction et sauvegarde UI, ni FR/AR/Darija/RTL/a11y ne sont certifiés. Échantillonnage et captures BEFORE/AFTER nécessaires **si un flux UI existant ou nouveau est modifié**. Aucun changement d'écran n'a été introduit dans ce diff.
- [Issue #924](https://github.com/hraaaaf/IAMINA-MVP/issues/924) opt-out session/global, parent sécurité #928, logging #931, processeurs/CNDP, garde clinique/essai pilote toujours ouverts. **Revue humaine indépendante clinique/privacy reportée à la fin du chantier par l'utilisateur, jamais approuvée**.
- **NO-GO pour merge, release, données patients et Vercel** tant que gate humain/certificateur n'est pas satisfait. Aucune blessure ou fuite patient observée ; il s'agit d'une correction préventive.

## NEXT EXACT / séquence
1. Examiner la CI GitHub exacte HEAD après le commit de docs sur la base temporaire main; si rouge, diagnostiquer, corriger, relancer sans affaiblir les gardes.
2. Restacker PR #932 sur `security/v1-03-strip-client-curl-logger-20261011` (#931), vérifier SHA/ahead/behind/diff 6 fichiers/DRAFT/mergeable, sans commit supplémentaire.
3. Synchroniser PR #932, issue #923 et Notion sur le statut effectivement prouvé sans relancer CI ; consigner les gaps optiques/UI/humains.
4. Continuer le prochain lot indépendant V1-03 ; à la fin du chantier, revue de sûreté clinique et privacy indépendante, certifieur, merge autorisé et post-merge. Aucun Vercel sans autorisation explicite.

**Statut :** correction implémentée, CI documentaire à établir ; clinical and release NO-GO / NON MERGÉ / NON DÉPLOYÉ.
