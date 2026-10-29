# IAMINA — Urgence B / D22 Web : préflight unités et cibles (non clinique)

**Date :** 29 octobre 2026. **Base contrôlée :** `main@3c99f1401844d3da6dac8d7298425492eb255751`. **Statut : PREPARED / D22 NO-GO, D19 GATE HUMAIN.** Le présent lot ne touche ni aux valeurs cliniques, ni aux écrans, ni aux données patients. D22 est la prochaine décision du chantier B après D7 ; issue P0 [#1165](https://github.com/hraaaaf/IAMINA-MVP/issues/1165).

## Goal / critère / preuve du préflight

- **Goal précis :** relever tous les passages dangereux entre mg/dL, mmol/L et cibles, fixer les assertions de conversion d'affichage existantes et préparer le contrat à faire valider, sans prescrire ou réinterpréter des objectifs patients.
- **Succès observable de ce préflight uniquement :** test Flutter ciblé `frontend/test/core/utils/d22_glucose_unit_conversion_preflight_test.dart` et CI exacte verts ; aucune modification runtime clinique, aucune cible fixée, aucun service externe contacté ; matrice D22/FUE et décision clinique requise clairement établies.
- **Preuve source BEFORE :** captures des extraits des fichiers existants, branches/SHAs, issue GitHub #1165 ; preuve AFTER limitée au test ajouté. **Pas de différence d'écran** et donc pas de prétendue comparaison visuelle Target→Render avant une réelle modification Web.

## BEFORE : incohérences vérifiées dans main

| Origine | Constat exact | Risque / limite |
|---|---|---|
| `frontend/lib/features/auth/onboarding_chat_screen.dart` | `_unit` accepte `mg/dL` ou `mmol/L`, puis `_finish` écrit inconditionnellement `targetRangeLow: 70` et `targetRangeHigh: 180` avec `unitPreference: _unit` | Aucune liaison explicite des deux nombres à une unité **de stockage** ; ne pas les interpréter comme cibles mmol/L |
| `frontend/lib/features/profile/profile_screen.dart` | `_loadProfile` écrit les nombres stockés dans les deux contrôleurs avec `toStringAsFixed(0)`, indépendamment de `profile.unitPreference` | Perte de précision et affichage brut si l'unité de préférence est mmol/L |
| `frontend/lib/features/profile/profile_screen.dart` | `_saveProfile` vérifie seulement finitude/positivité/ordre, puis écrit `targetRangeLow/High` et `unitPreference: _unit`, sans conversion | Un simple changement d'unité peut réinterpréter des nombres déjà saisis au lieu de convertir une quantité |
| `frontend/lib/features/profile/profile_screen_presentation.dart` | Le bloc `glucoseTarget` précède `measureUnit` ; callback unité modifie seulement `_unit` | Ordre inverse de D22 et transition sans protocole de conversion |
| `frontend/lib/data/drift/database.dart` | `targetRangeLow/High` sont des colonnes `real` avec valeurs par défaut 70/180 ; `unitPreference` est une colonne séparée | Les lignes historiques sont **potentiellement ambiguës**, car le schéma ne porte pas l'unité intrinsèque du nombre ni sa provenance |
| `frontend/lib/core/utils/glucose_formatter.dart` | Le helper existant dit « valeur brute en mg/dL », utilise `mgdlToMmolFactor = 18.018` pour **l'affichage** | Le facteur arithmétique existe ; **rien n'établit que l'édition des cibles l'utilise** |

Le problème est un **risque de mauvaise association valeur↔unité**, pas la preuve d'une recommandation clinique effectivement faite à une personne. Aucun patient réel n'est utilisé.

## Vérification de calcul, sans cible médicale

Conversion documentaire du glucose : `mmol/L ≈ (mg/dL) ÷ 18` ; `mg/dL ≈ (mmol/L) × 18`. Le helper utilise 18.018. Sources indépendantes : [American Diabetes Association, Diabetes Care (2023)](https://diabetesjournals.org/care/article/46/10/e151/153425/) et [B. Braun, Blood Glucose Conversion Table](https://www.bbraun.co.uk/en/patient-care/services/home-care/blood-glucose-conversion-table.html). Exemple de **conversion mathématique seulement**, pas de prescription : 90 mg/dL → 5.0 mmol/L ; 126 → 7.0 ; 180 → 10.0 (arrondi affiché à une décimale). Le test Flutter couvre ces exemples, l'immuabilité des valeurs brutes et des limites de graphe. **Ces nombres ne constituent pas des objectifs à appliquer à un patient.**

## Contrat candidat D22 — soumis à D19, NON ACTIVÉ

1. **Proposition A (recommandée sous revue clinique et migration) :** stocker les quantités de glycémie et les **bornes de cibles explicitement validées** dans une unité canonique connue, par exemple `mg/dL`, tout en portant la provenance, la validation et l'identité du patient. Une préférence `mmol/L` n'est qu'un choix d'affichage ; toute entrée dans cette unité est convertie **une fois** avant persistance avec contrôle d'arrondi. Distinguer quantité enregistrée, valeur affichée et origine d'objectif.
2. **Proposition B :** ajouter une unité explicite **pour chaque borne/objectif** et effectuer les conversions à la frontière affichage/calcul, avec migrations et audits supplémentaires. Plus robuste pour un legacy très mélangé, mais plus coûteux.
3. **Choix non autorisé :** déduire que les anciennes valeurs 70/180, 3.9/10.0, ou tout autre nombre ambigu représentent une cible validée, corriger silencieusement les lignes legacy, ou proposer des objectifs médicaux par type de diabète.

**Gate clinique/humain réel :** [D19 / PR #920](https://github.com/hraaaaf/IAMINA-MVP/pull/920) reste **OPEN / DRAFT**. Il faut décider la représentation d'autorité, la provenance clinique des cibles, le sort des lignes ambiguës, les règles d'arrondi et migration/rollback, ainsi que le comportement pour patient sans cible documentée. L'unité de mesure peut être une préférence, **jamais une présomption d'objectif de soin**. Aucune entrée patient, sauvegarde ou synchronisation D22 modifiée par le présent préflight.

## FUE exigée pour D22 final — encore NOT_RUN

| Test utilisateur | FR | AR/RTL | Web 390 / 768 / 1280 | Persistance/reprise | Statut |
|---|---|---|---|---|---|
| Onboarding neuf : unité avant cibles ; aucune cible non validée attribuée implicitement | requis | requis | requis | requis | NOT_RUN |
| Profil : sélection mg/dL→mmol/L→mg/dL sans changer la quantité | requis | requis | requis | requis | NOT_RUN |
| Conversion explicite d'une **cible validée** et arrondis cohérents | requis | requis | requis | requis | NOT_RUN |
| Historique avec unité/provenance ambiguë : fail-closed sans réécriture | requis | requis | requis | requis | NOT_RUN |
| Invalidité, erreur, offline, reload, sortie et retour, compte A→logout→B | requis | requis | requis | requis | NOT_RUN |
| Affichage identique sur graphiques / résumés / exports après autorité confirmée | requis | requis | requis | requis | NOT_RUN |
| Clavier Tab/Shift+Tab, lecture écran, scroll et contraste | requis | requis | requis | requis | NOT_RUN |

**Cible UI, quand l'autorité D19 sera adoptée :** « Unité de mesure » **avant** « Objectifs glycémiques », valeurs explicitement libellées selon l'unité choisie, avertissement/absence plutôt qu'une fausse cible pour le legacy ambigu. BEFORE réel → maquette → code → AFTER mêmes viewports → revue clinique/privacy + score selon `docs/QUALITY_SCORING_POLICY.md`.

## Statut et chemin restant

- **Présent préflight :** test/dossier seulement, non corrigeant ; verdict exact HEAD CI à compléter. Aucun Vercel, DB, API ou produit modifié.
- **D22 total : OPEN / FUE_NO_GO**, BLOQUÉ côté changement clinique par D19. **Next exact :** vérifier le test et CI du préflight ; audit ciblé des modèles/exports si indépendant ; soumettre la décision A/B, revue clinique D19, puis implémenter le lot UI/stockage D22 avec vrai BEFORE/AFTER et FUE complète.
- **Fichier canonique provisoire :** ce document, subordonné au suivi [GitHub #1165](https://github.com/hraaaaf/IAMINA-MVP/issues/1165) et à `docs/ROADMAP.md`. Ne pas inventer de pourcentage global.
