# IAMINA D22 Web — réglage précis du demi-cadran glycémie

**Date** : 2026-11-03.  
**Décision** : D22 — UX de saisie de glycémie (issue [#1252](https://github.com/hraaaaf/IAMINA-MVP/issues/1252)).  
**Statut** : **validé techniquement sur code HEAD `a7cc05138dab3c38311fbbe37aff99415368659c`** : 12/12 workflows GitHub SUCCESS, tests Flutter et captures Web FR/AR contrôlés. PR Draft #1253 non fusionnée, non déployée ; la recette iPhone du correctif reste à faire. Cette mise à jour est un commit documentaire post-test, pas une nouvelle version du code testée.

## Feedback terrain, BEFORE et cause
- Utilisateur iPhone sur la **vraie production** D12 : « Je peux pas aller précisément, ça vacille entre 126 et 127, c’est pas très intuitif. C’est le seul problème, tout le reste fonctionne. »
- Référence BEFORE fournie par archive de test FUE `d13-visual-chrome-20261103.zip` : `before-fr-390x844.png`, `before-ar-390x844.png`, `before-fr-768x1024.png`, `before-fr-1280x900.png`. La capture FR mobile montre un demi-arc, une mesure centrale « 126 », sans commandes de correction fine.
- Code vérifié : `glucose_half_dial_input.dart`, `_selectArc` calcule un angle pour chaque `PointerMoveEvent`, convertit un fractionnement continu en mg/dL, puis `.roundToDouble()` ; à la frontière entre deux entiers, de légères variations du doigt peuvent faire osciller 126/127. **Hypothèse technique fortement compatible** avec le retour utilisateur, et non une mesure physique instrumentée.
- Le nombre central était déjà `TextField` éditable, mais le fait qu'il faille passer du cadran au clavier pour ajuster une unité est peu intuitif.

## Goal / succès / preuve
- **Goal** : atteindre précisément toute mesure déjà saisie, au doigt, sans oscillation : `−` / `+` à pas de **1 mg/dL** ou **0,1 mmol/L**, tout en préservant la sélection rapide et le clavier au centre.
- **Succès observable** : 126 → + → 127 → − → 126 ; 7.0 → + → 7.1 → − → 7.0 ; passage mg/dL↔mmol/L sans dérive canonique ; aucune valeur créée par un pas sur champ vide ; valeurs saisies manuellement hors 40–320 non tronquées ; pas d'overflow Flutter visuel à 390, 768, 1280, FR/AR.
- **Preuves** : tests helpers + widget réel `NativeDatabase.memory()` FR/AR × 390×844, 768×1024, 1280×900, journal exactement une ligne 126 mg/dL. CI exact HEAD, captures AFTER aux mêmes viewports et score visuel fondé sur comparaison.

## Mockup/référence et décision UX
Concept validé comme direction d'implémentation (non comme test visuel) : conserver la carte verte, le demi-arc, le chiffre éditable et le bouton d'unité. Insérer **immédiatement sous le demi-arc et avant les repères** une rangée compacte :

```
[ − ]       RÉGLAGE PRÉCIS        [ + ]
                 1 mg/dL
```

- Surface d'appui minimale 48×48, `tooltip` FR/AR/EN, texte centré, `Row` sensible au RTL.
- Boutons **désactivés** sans mesure explicite, aucune valeur par défaut (le centre affiche « — »).
- Ne pas limiter la saisie directe à 40–320 mg/dL : ce n'est que l'échelle de dessin du cadran, pas une cible médicale.
- À changement d'unité, pas basé sur la valeur **affichée** arrondie au dixième ou à l'entier ; éviter l'accumulation d'erreurs flottantes. C'est une modification explicite du patient, qui remplace la mesure canonique uniquement après appui sur ±.
- Aucun nouveau seuil, diagnostic, couleur, calcul de traitement, API, DB ou backend.

## Réalisation et contrôle validé sur le code
- Nouvelle branche `fix/d22-web-glucose-fine-step-20261103` depuis **HEAD D12 après closeout documentaire** `05e49bf90bf019063fa7b0a5c8b92532ce924de5` ; le SHA Web réellement en production reste **`7697a179caec0b094e589fbb8775b967754853c4`** (même code applicatif, diff documentaire uniquement).
- `frontend/lib/features/dashboard/widgets/glucose_half_dial_input.dart` : helper `d22FineAdjustedMgdl` et deux `IconButton.outlined` accessibles, désactivés si mesure absente/invalides, labels localisés, instruction mise à jour.
- `frontend/test/features/dashboard/d22_glucose_fine_step_test.dart` : cas helper (absence, NaN/Inf, borne minimale positive, 126↔127, 7.0↔7.1, hors affichage 500) et 6 scénarios widget SQLite sur les trois viewports en FR/AR.
- **NEXT** : [PR Draft #1253](https://github.com/hraaaaf/IAMINA-MVP/pull/1253) **base D12 restaurée** après CI déclenchée temporairement contre `main` (déclencheur `ci.yml` limité à `main/dev`). Delta exact **3 fichiers** (composant + test + cette note), GitHub `mergeable:true`. Recette utilisateur iPhone sur futur déploiement D22 autorisé, sans nouvelle release ni merge avant GO explicite.

## AFTER : preuves visuelles et tests exact HEAD (03/11/2026)

- **Commit de code contrôlé** : `a7cc05138dab3c38311fbbe37aff99415368659c`.
- [CI complète #41715347268](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41715347268) **SUCCESS** : `flutter analyze`, **991 tests PASS / 7 skipped**, dont **7/7 nouveaux tests D22** (un test pur + 6 widgets Flutter FR/AR × 390×844, 768×1024, 1280×900 avec `NativeDatabase.memory()`), bundle PWA compilé et sorties vérifiées. Backend / PostgreSQL explicitement SKIPPED, car aucun changement backend.
- [FUE Chromium D13 #41715347157](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41715347157) **SUCCESS 6/6** : chaque cas FR/AR (390/768/1280) établit une sauvegarde Drift réelle bloquée, refus du retour app/navigateur, reçu et exactement une mesure 126 mg/dL après recharge. FUE confirmé sur ce code (preuve synthétique, non recette réelle iPhone).
- **12/12 workflows GitHub SUCCESS, zéro échec, zéro run actif** sur `a7cc051...`. PR issue [#1252](https://github.com/hraaaaf/IAMINA-MVP/issues/1252).
- **Comparaison BEFORE/AFTER vérifiée** à viewport identique grâce aux captures réelles des artifacts GitHub D13 : mobile FR/AR 390×844, tablette FR/AR 768×1024, desktop FR/AR 1280×900. BEFORE : arc à valeur centrale avec seulement clavier direct ; AFTER : commandes `−/+` visibles sous arc, libellés FR/AR, CTA Enregistrer conservé et sans collision/overflow observé. Après une première AFTER, un écart horizontal sur tablette/desktop a été corrigé par `Center(ConstrainedBox(maxWidth: 354))` et couvert par des assertions géométriques dans les six tests.
- **Score visuel évaluatif** : **8,5/10** (alignement cohérent, boutons 48×48, hiérarchie préservée, pas de chevauchement dans ces captures). Score **non automatisé** et **non certification iPhone Safari réel**, qui reste à tester. On conserve la hauteur additionnelle des commandes : c'est un compromis UX assumé.
- **Intégrité** : aucun seuil médical nouveau, aucun changement de DB, backend, navigation D13 ou validation D12. Sur champ vide les deux contrôles et l'action de lecteur d'écran sont inactifs, sans générer de mesure fictive. Contrats `126 + →127 −→126`, `7.0 + →7.1 −→7.0`, et une seule sauvegarde SQLite verte.
- **Gates restants** : QA réelle iPhone après déploiement explicite, revue indépendante, clinique D32 toujours hors portée. **Aucun GO de Vercel ni merge donné pour D22**. Prod actuelle D12 `dpl_AzTqctoykcFwtvSsTT1bomBn5i9h`, SHA `7697a179...`, demeure inchangée.
- **Traçabilité** : tout commit supplémentaire uniquement .md au-delà de `a7cc051...` doit être distingué du SHA de code validé ; ne pas déclarer tests exact HEAD post-documentaire sans revérification de ses workflows.

## Reprise
Source de reprise `docs/assessments/2026-11-03-d22-web-dial-precision.md` ; incident UX #1252. Ne pas confondre la publication antérieure D12 avec une autorisation pour publier D22. La recette réelle iPhone est la validation humaine finale.
