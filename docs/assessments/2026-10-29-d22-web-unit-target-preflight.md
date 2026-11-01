# IAMINA — Urgence B / D22 Web : préflight unités et cibles (non clinique)

**Date :** 29 octobre 2026. **Base contrôlée :** `main@3c99f1401844d3da6dac8d7298425492eb255751`. **Statut historique de prémerge : PREPARED. Préflight test-only MERGED dans main ; D22 décision produit OPEN / FUE_NO_GO, D19 GATE HUMAIN.** Le présent lot ne touche ni aux valeurs cliniques, ni aux écrans, ni aux données patients. D22 est la prochaine décision du chantier B après D7 ; issue P0 [#1165](https://github.com/hraaaaf/IAMINA-MVP/issues/1165).

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

Conversion documentaire du glucose : `mmol/L ≈ (mg/dL) ÷ 18` ; `mg/dL ≈ (mmol/L) × 18`. Le helper actuel utilise 18.018, mais **D19 / PR #920 (DRAFT)** propose 18.016 pour l'aligner avec le backend ; ce différentiel de précision est **une décision de contrat NON encore approuvée**, donc le test du préflight ne fixe pas l'une de ces deux valeurs. Sources indépendantes : [American Diabetes Association, Diabetes Care (2023)](https://diabetesjournals.org/care/article/46/10/e151/153425/) et [B. Braun, Blood Glucose Conversion Table](https://www.bbraun.co.uk/en/patient-care/services/home-care/blood-glucose-conversion-table.html). Exemple de **conversion mathématique seulement**, pas de prescription : 90 mg/dL → 5.0 mmol/L ; 126 → 7.0 ; 180 → 10.0 (arrondi affiché à une décimale). Le test Flutter couvre ces exemples, l'immuabilité des valeurs brutes et des limites de graphe. **Ces nombres ne constituent pas des objectifs à appliquer à un patient.**

## Contrat candidat D22 — soumis à D19, NON ACTIVÉ

1. **Proposition A (recommandée comme orientation technique, non comme validation clinique) :** stocker les quantités de glycémie et les **bornes de cibles explicitement validées** dans une unité canonique connue, par exemple `mg/dL`, tout en portant la provenance, la validation et l'identité du patient. Une préférence `mmol/L` n'est qu'un choix d'affichage ; toute entrée dans cette unité est convertie **une fois** avant persistance avec contrôle d'arrondi. Distinguer quantité enregistrée, valeur affichée et origine d'objectif.
2. **Proposition B :** ajouter une unité explicite **pour chaque borne/objectif** et effectuer les conversions à la frontière affichage/calcul, avec migrations et audits supplémentaires. Plus robuste pour un legacy très mélangé, mais plus coûteux.
3. **Choix non autorisé :** déduire que les anciennes valeurs 70/180, 3.9/10.0, ou tout autre nombre ambigu représentent une cible validée, corriger silencieusement les lignes legacy, ou proposer des objectifs médicaux par type de diabète.

**Gate clinique/humain réel :** [D19 / PR #920](https://github.com/hraaaaf/IAMINA-MVP/pull/920) reste **OPEN / DRAFT**. Il faut décider la représentation d'autorité, le **facteur de précision partagé (18.018 main vs 18.016 PR #920),** la provenance clinique des cibles, le sort des lignes ambiguës, les règles d'arrondi et migration/rollback, ainsi que le comportement pour patient sans cible documentée. L'unité de mesure peut être une préférence, **jamais une présomption d'objectif de soin**. Aucune entrée patient, sauvegarde ou synchronisation D22 modifiée par le présent préflight.

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

- **Présent préflight :** test/dossier seulement, non corrigeant ; PR #1173 MERGED et CI prémerge/postmerge exactes SUCCESS. Aucun Vercel, DB, API ou produit modifié.
- **D22 total : OPEN / FUE_NO_GO**, BLOQUÉ côté changement clinique par D19. **Next exact :** obtenir les arbitrages qualifiés G1–G7 sur [la fiche de décision D19→D22](2026-10-29-d19-d22-web-clinical-decision-gate.md), puis seulement implémenter le lot UI/stockage D22 avec vrai BEFORE/AFTER et FUE complète.
- **Fichier canonique provisoire :** ce document, subordonné au suivi [GitHub #1165](https://github.com/hraaaaf/IAMINA-MVP/issues/1165) et à `docs/ROADMAP.md`. Ne pas inventer de pourcentage global.

## Closeout technique du préflight — 29 octobre 2026

- **Prémerge exact :** [PR #1173](https://github.com/hraaaaf/IAMINA-MVP/pull/1173), candidate `834a61e6f8d0e66b7ee816eb0fd6371a9e99a654`, [CI #40845031719](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40845031719) **SUCCESS**. Les jobs analyse Flutter, tests Flutter et build PWA ont exécuté et réussi ; secrets/scope ont réussi ; backend non sélectionné par la classification de portée (test frontend + documentation uniquement).
- **Merge vérifié :** squash `d5d95c6fcfef4ce1e4254c280bcd7a0fae114fd9` vers `main` le 29/10/2026 à 08:56 UTC. [Commit](https://github.com/hraaaaf/IAMINA-MVP/commit/d5d95c6fcfef4ce1e4254c280bcd7a0fae114fd9). Diff exact : un test Flutter et ce rapport de risques ; **zéro fichier runtime clinique/UI/backend/DB modifié**.
- **Postmerge `main@d5d95c6` :** [CI #40845836231](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40845836231) **SUCCESS** à 09:03Z sur le SHA exact du merge ; Flutter analyze/tests/PWA build, contrôle de secrets et classification de portée ont conclu avec succès. Backend hors périmètre correctement ignoré. Pas de déploiement Vercel.
- **Audit complémentaire sans mutation :** [issue #1165](https://github.com/hraaaaf/IAMINA-MVP/issues/1165#issuecomment-6492412675). Le profil sauvegarde `low/high` sans normalisation, le dashboard Premium classe les mesures brutes avec ces bornes brutes, et les rapports font de même. Une borne saisie en mmol/L peut donc être utilisée comme mg/dL pour une classification ; **risque de code**, sans preuve d'un affichage patient réel. Unités 18.0 (dashboard/rapports), 18.018 (formatter actuel) et 18.016 (D19 proposé) non harmonisées. `ClinicalEngine.calcTIR` étiquette une fraction d'entrées manuelles comme TIR : dépend de la revue CAL/D19.
- **Pass adversarial périmètre étroit :** tests de formatage indépendant d'une valeur de facteur au millième, mais aucune vérification FUE, provenance historique, synchronisation ou statut clinique ; ne pas interpréter la réussite de CI comme validation des objectifs. Révision d'approbation indépendante non revendiquée. La décision D22 reste bloquée, en attente de gate D19/clinicien et FUE Web réelle.
- **Prochaine étape :** fermer la preuve postmerge CI de ce préflight, puis arbitrer humainement D19 le contrat (unité intrinsèque des bornes, provenance, arrondi, legacy inconnu, migration/rollback) avant tout patch fonctionnel D22.

### Scoring / certification — deux périmètres non interchangeables

**Préflight test-only (sans changement patient) :** Goal : caractérisation reproductible de la conversion d'affichage et consignation des risques. Success : diff limité à 2 fichiers, CI prémerge et postmerge exacts SUCCESS, aucun code runtime touché. Preuve : [#1173](https://github.com/hraaaaf/IAMINA-MVP/pull/1173), [#40845031719](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40845031719), [#40845836231](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40845836231) et commit `d5d95c6`. Dimensions : portée/test/sécurité des changements documentaires OK ; FUE clinique non applicable à ce sous-lot **uniquement**. `EXECUTION_SCORE: 9.1/10`, `ADVERSARIAL_SCORE: 9.0/10`, écart `0.1`, cap même exécutant `9.4`, `RETAINED_SCORE: 9.0/10`. Cette évaluation est une **revue critique du même exécutant**, pas une revue indépendante. Perfection Pass : périmètre relu ; aucun changement d'algorithme, schéma, patient ou écran ; les contrôles de source et la future FUE restent explicitement hors du GO limité. **GO technique du préflight uniquement.**

**Décision produit D22 : `BLOCKED / FUE_NO_GO`**, pas `VERIFIED`. Le risque d'interprétation clinique, le gate humain D19 et toutes les vérifications Web marquées `NOT_RUN` restent des blockers binaires. Le sous-lot de test ne fournit **aucune certification clinique ni livraison fonctionnelle D22**. Les scores du préflight ne se transfèrent pas à la décision D22.

## Handover après closeout documentaire

- **CI postmerge #1174 :** [#40848461692](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40848461692) **SUCCESS**, SHA exact `main@278159a2988c860861e24301c6db37588f1b4eb8` ; closeout du préflight documentaire achevé, sans changement de code clinique.
- **Gate suivant documenté (NON APPROUVÉ) :** [Fiche D19→D22 : G1–G7, oracles F01–F07, signataires et séquence restante](2026-10-29-d19-d22-web-clinical-decision-gate.md). Le présent fichier reste canonique pour D22 ; l'autre fiche est le dossier de décision soumis aux humains. PR #920 reste DRAFT ; D22 FUE_NO_GO.


## 01/11/2026 — Reprise D22 après validation propriétaire D7 (lecture seule)

**Décision et objectif :** ouvrir le prochain dossier de priorité Chantier B, D22 « unité de mesure avant objectifs glycémiques », sans activer un changement patient ni anticiper le gate clinique D19. Le propriétaire atteste avoir testé et accepté 7/7 scénarios de recette manuelle D7 ; cette attestation n'est pas un signoff clinic/privacy indépendant et ne clos pas la certification globale D7. La roadmap B confirmée demeure `D7 → D22 → D8`, puis D10 ; D8 dépend de D22 et D5.

**Contrôle actuel `main`, sans modification :**
- `onboarding_chat_screen.dart` blob `a54de29c3b0b2c17c32ed64330bc449425c79c5d` : choix `mg/dL` / `mmol/L` (lignes 437–443) ; enregistrement de `unitPreference: _unit` mais `targetRangeLow: 70`, `targetRangeHigh: 180` (lignes 205–207) sans contrat de provenance/stockage explicite.
- `profile_screen.dart` blob `d6ab40a135ee4218c430fe6e2f78874c4dcafe21` : lecture `targetRangeLow/High.toStringAsFixed(0)` (117–118), sauvegarde brute `targetRangeLow/High` et `unitPreference` (718–720), sans conversion démontrée.
- `profile_screen_presentation.dart` blob `0bd06f5141f627a90b6eec647746b0dacd595353` : la section `glucoseTarget` (223) précède `measureUnit` (251), contrairement à D22.
- `glucose_formatter.dart` blob `9932d16e358511f1f0ebd37e896e9760317f32d7` : facteur d'affichage `18.018` (ligne 4). Choix de facteur source D19 non encore approuvé ; aucune conversion de cible déduite de cet helper.

**Arbitrage D19 vérifié le 01/11 :** [PR #920](https://github.com/hraaaaf/IAMINA-MVP/pull/920) `OPEN` / `DRAFT` / `MERGED=false` / `MERGEABLE=false`, HEAD annoncé `81bf4d6ac4e182f3058ca6ff52b504ce8404beb9`. Les sept décisions G1–G7 de [la fiche clinique](2026-10-29-d19-d22-web-clinical-decision-gate.md) restent sans signataires enregistrés : unité canonique (G1), source/validation de la cible (G2), legacy inconnu (G3), facteur/arrondi (G4), classement/TIR des mesures (G5), texte et parcours FR/AR (G6), rollback/scope/migration (G7). La documentation existante recommande à titre technique un stockage canonique explicite avec provenance et un fail-closed sur legacy non sûr, **pas une validation médicale ni une prescription**.

**Constat / risque :** une préférence `mmol/L` associée à des bornes nues `70/180` représente une ambiguïté susceptible d'affecter affichage et classification. C'est un **défaut de contrat source actuel**, non un incident patient démontré. Ne jamais réécrire ces bornes ni convertir des dossiers historiques sans preuve d'origine.

**Succès de ce sous-lot :** revue source actuelle exacte, dossier D19/G1–G7 réidentifié, aucun changement runtime/DB/clinical/API/UI, aucune CI clinique ni score FUE inventés. La CI existante du préflight [#40845836231](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40845836231) porte sur un ancien SHA ; elle n'est pas une preuve du comportement actuel hébergé. **`D22_PRODUCT=BLOCKED_D19` ; `D22_FUE=NOT_RUN`.**

**Next exact :** obtenir une décision signée et datée de clinicien/endocrinologue, ingénierie calcul et privacy sur G1–G7 ; en attendant, préparer uniquement tests et maquettes non prescriptives hors production. Dès approbation : BEFORE 390/768/1280, mockup unité→cible, implémentation bornée avec migration réversible, AFTER mêmes états/viewports, FUE FR/AR clavier/offline/A→B→A, CI exact SHA, contre-revue, Perfection Pass ; fusion/déploiement Vercel uniquement sur GO distinct explicite. Ne pas toucher à la production avec cette préparation.


## 01/11/2026 — Mockup fonctionnel candidat Web, D19 PENDING

**Goal UI/UX (en attente d'approbation clinique G1–G7) :** rendre l'unité explicite **avant** toute cible et empêcher qu'une plage numérique sans provenance soit présentée comme un objectif médical validé. Aucun écran de production ni patient data n'est modifié dans cette préparation.

**BEFORE vérifié par source (pas par capture) :** `profile_screen_presentation.dart` affiche `glucoseTarget` avant `measureUnit` ; `profile_screen.dart` lit les bornes brutes au format entier et sauvegarde brutes ; `onboarding_chat_screen.dart` écrit 70/180 malgré `unitPreference='mmol/L'`. Captures BEFORE aux tailles 390/768/1280 **NON COLLECTÉES**, donc aucun score visuel ni assurance de rendu.

**Référence/wireframe texte uniquement (PROPOSITION, pas une implémentation ni capture) :**

```text
FR, écran Profil / Suivi médical
┌─────────────────────────────────────┐
│ Unité de mesure                     │
│ (●) mg/dL   ( ) mmol/L              │
├─────────────────────────────────────┤
│ Objectifs glycémiques personnels    │
│ Statut : Non défini / À confirmer   │
│ [Aucune cible validée affichable]   │
│                                     │
│ Une cible ne peut être utilisée     │
│ pour un calcul qu'avec sa source,   │
│ son unité et sa validation.         │
└─────────────────────────────────────┘

AR, structure RTL à valider par relecteur arabophone
┌─────────────────────────────────────┐
│                      وحدة القياس    │
│              mmol/L  |  mg/dL       │
├─────────────────────────────────────┤
│           الأهداف الشخصية للغلوكوز   │
│            غير محددة / قيد التحقق   │
│ [لا توجد أهداف مؤكدة لعرضها]        │
└─────────────────────────────────────┘
```

**Oracles visuels et accessibilité à créer après gate :** FR/AR RTL à 390×844, 768×1024 et 1280×900 ; ordre réel des champs, focus Tab/Shift+Tab, labels et unités visibles, aucun débordement, police 200 %, app-lock et reload, ligne legacy inconnue sans réinterprétation. Avant implémentation, enregistrer screenshots BEFORE du **même SHA** dans les trois viewports ; après correction obtenir AFTER aux mêmes états, comparaison Target↔Render, score visuel et revue linguistique native.

**Proposition de contrat de données séparée de l'UI :**
- `unitPreference` est un choix d'affichage. `sourceUnit` décrit l'unité de la quantité originelle ; ne pas les fusionner.
- Les anciennes bornes sans provenance doivent rester brutes et être marquées d'un statut distinct jusqu'à examen qualifié. Les mots « objectif validé » ne découlent jamais de `70/180`.
- Les valeurs affichées arrondies ne sont **pas** une nouvelle saisie clinique ; un save sans modification ne doit pas écraser le brut.
- Aucune classification, aucun TIR dérivé de relevés manuels, ni aucun export d'objectif clinique à partir d'une plage inconnue.
- **Tous ces choix restent CANDIDATS.** Référence candidate de tests uniquement : [PR #1211 DRAFT](https://github.com/hraaaaf/IAMINA-MVP/pull/1211), où l'oracle est privé au test, sans preuve que le produit actuel le satisfait.

**Sources externes à vérifier pour revue humaine :** [ADA Standards of Care 2026 §6](https://doi.org/10.2337/dc26-s006) (objectifs individualisés ; métriques CGM/TIR) ; [ADA patient education](https://diabetes.org/living-with-diabetes/treatment-care/checking-your-blood-sugar) ; [Alberta Health Services, conversion blood glucose](https://www.albertahealthservices.ca/assets/info/hp/edu/if-hp-edu-er-nursing-blood-glucose-conversion-chart.pdf) (conversion usuelle affichée ~18). Ces sources ne tranchent pas le facteur/arrondi logiciel G4 ni l'approbation de cibles individuelles.

**Human gate :** G1–G7 signés (D19), revue FR/AR native, sécurité/privacy et produit. **Tant qu'absent : MOCKUP_CANDIDATE uniquement**, aucune implémentation D22, aucune certification FUE ou note visuelle.


## 01/11/2026 — G4 : base métrologique primaire vérifiée, arbitrage toujours ouvert

**Référence primaire** : [NIST Chemistry WebBook — D-Glucose, SRD 69](https://webbook.nist.gov/cgi/cbook.cgi?ID=C50997&Mask=26D), masse molaire 180.1559 g/mol ; [PubChem NIH — D-Glucose](https://pubchem.ncbi.nlm.nih.gov/compound/D-Glucose), masse molaire arrondie 180.16 g/mol. Pour une **concentration de masse de glucose** exprimée en mg/dL et une concentration de quantité en mmol/L, l'algèbre dimensionnelle donne :

```text
1 mmol/L glucose = 0.1801559 g/L
                 = 18.01559 mg/dL
mmol/L = mg/dL / 18.01559    [référence théorique à partir de NIST]
```

**Précision constatée des variantes applicatives** : le `18.016` proposé par D19 approxime cette valeur physique ; `18.018` (helper actuel) et `18.0` (certains écrans) sont d'autres approximations. À titre purement numérique, `180 mg/dL / 18.01559 = 9.99135 mmol/L`, contre `180 / 18.018 = 9.99001 mmol/L` ; une décimale affichée masque souvent l'écart mais **ne suffit pas** à fixer le contrat d'édition, d'arrondi et les classements près des frontières.

**Recommandation ingénierie SOUMISE À G4, non signée :** adopter une constante/version commune compatible avec la référence métrologique, définir les décimales par surface et préserver systématiquement la valeur brute en stockage sans double conversion. Les limites patient et le choix d'unité canonique restent **G1/G2/G5 à valider** ; aucun seuil, plage, précision/arrondi réglementaire ou valeur patient n'est autorisé par cette démonstration.


## 01/11/2026 — D22 safe-preflight closeout: #1211 oracle + #1210 mockup merged

**D22 Goal / success / proof (preparation only):** make the source-origin ambiguity of `unitPreference` and target numeric bounds explicit, prepare a candidate non-prescriptive unit-first UI and unit/provenance test contract, without altering any production patient path. Success here is source + exact GitHub CI + two **nonruntime** merges; **D22 clinical success is NOT claimed**.

**GitHub closes two safe independent preparatory items:**
1. [#1211 test candidate](https://github.com/hraaaaf/IAMINA-MVP/pull/1211): squash MERGED to `main@c44233022bf7cafcc5ac1f746666ccef7fa923ed` (one test Dart file, six synthetic gate cases, no application import of oracle). PR HEAD `420dfa95facd3dd334eaa234b72ed8122dd56a8f` had CI [#41261674295](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41261674295) `COMPLETED/SUCCESS`: Flutter analyze/test/PWA build SUCCESS; backend/Postgres SKIPPED by scope.
2. [#1210 nonclinical D22 mockup/document](https://github.com/hraaaaf/IAMINA-MVP/pull/1210): squash MERGED to `main@df42460b1966125176a9ad3c6be216bc324fac0d` (this Markdown only). PR HEAD `4bdeb3a945e292b6a18bbad31e329c5ce82e6c1f` had CI [#41261901535](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41261901535) `COMPLETED/SUCCESS`, docs-only, Flutter/backend intentionally SKIPPED. Git compare with `main` immediately after showed `identical`.
3. No D22 Flutter production code/DB/API/unit conversion logic deployed or merged. A passing **synthetic internal oracle** does not assert the current application meets its proposed contract.

**Owner priority decision / counters:** owner explicitly accepts D7 as working and asks to mark 1/17 and advance. Record `CHANTIER_B_OWNER_ACCEPTED=1/17 (5.88%)` separately from `CHANTIER_B_FORMALLY_D_CERTIFIED=0/17`. Product D7 on Production is released; its independent clinical/privacy certification remains open (do not invent expert review). D22 is next active item, not completed.

**Current real block and next exact:** [D19 gate G1–G7](2026-10-29-d19-d22-web-clinical-decision-gate.md) remains unsigned; [#920](https://github.com/hraaaaf/IAMINA-MVP/pull/920) OPEN/DRAFT/nonmergeable. Source `main` still writes `70/180` regardless of `mmol/L`, target before unit in profile, raw `toStringAsFixed(0)` display and raw save; do **not** authorize a medical refactor while G1–G7 pending. Next **human gate**: qualified clinical and data/privacy review/approvals on unit authority, personalized target provenance, legacy and migration, factor/rounding, permissible classifications and FR/AR RTL wording. After those decisions, collect actual BEFORE screenshots at 390/768/1280 → target mockup → bounded implementation → AFTER identical viewports + tests and owner safety review → score/perfection → merge/release only if authorized. D22 `BLOCKED_D19`, FUE `NOT_RUN`.


## 01/11/2026 — D22-A Web : candidat d'ordre visuel isolé, NON LIVRÉ

**Décision :** implémenter un seul sous-ensemble non clinique de D22 sur branche isolée, sans merge ni activation de cibles : le choix « Unité de mesure » précède désormais le bloc « Objectifs glycémiques » dans `_buildMedicalSection` du Profil. **Goal** : éliminer l'inversion visuelle connue sans modifier les valeurs, l'interprétation, les données patients ou les règles cliniques.

- **Base contrôlée** : `main@cb60a2fdc04d52b028770cd783eb8f0ec45f7d05`.
- **Branche candidate** : `fix/d22-web-unit-first-candidate-20261101`.
- **Diff préliminaire** : `frontend/lib/features/profile/profile_screen_presentation.dart` (déplacement du bloc UI existant, sans changement de ses contrôleurs/handlers), plus `frontend/test/d22_profile_unit_before_target_source_contract_test.dart` (deux tests de contrat **statique source uniquement**).
- **Preuve de lecture GitHub** : la branche contient `l10n.measureUnit` avant `l10n.glucoseTarget`, dans la même section et avec les deux champs Low/High préservés. Aucun run Flutter/Chrome n'a encore été prouvé pour ce candidat à la date de création de cette note.
- **BEFORE/AFTER réels** : `NOT_RUN` (aucune capture Web 390/768/1280 FR/AR et aucune comparaison de rendu).
- **Risque persistant critique** : l'onboarding écrit toujours `70/180` quel que soit `mmol/L` ; Profile lit et écrit les bornes brutes ; les rapports et classifications demandent une revue d'autorité. La seule inversion visuelle **ne sécurise pas la glycémie**.
- **Gates** : G1–G7 cliniques/DB/privacy/RTL toujours `PENDING`. D22 `FUE_NO_GO`, `RELEASE_NO_GO`. Aucune conversion ni migration, aucun déploiement Vercel autorisé. Ne pas fusionner ce candidat seul en donnant l'impression d'une correction globale.
- **Next exact** : obtenir les arbitrages humains, puis traiter les conversions et la provenance sur le même contrat approuvé ; tests runtime Flutter + FUE navigateur, BEFORE/AFTER, scoring et certification. Le présent candidat est révisable/abandonnable si G6 impose un autre parcours.


### 01/11/2026 — D22-A : test de rendu Flutter FR/AR × 3 ajouté (en attente de preuve CI)

- **Code ajouté à la PR candidate #1213** : `frontend/test/features/profile/d22_web_unit_first_widget_test.dart`, six scénarios synthétiques réutilisant le vrai `ProfileScreen` avec coffre patient fictif et `ExpansionTile` médicale dépliée, en FR/AR aux tailles 390×844, 768×1024, 1280×900.
- Les assertions ciblent l'existence des titres localisés, leur ordre vertical réellement calculé par Flutter et le sens RTL/LTR ; elles ne changent **aucune** borne glycémiques ou autorité clinique.
- **Statut probatoire à la création** : widget tests nouveaux **non encore exécutés par une CI vérifiée** ; aucun parcours Chrome FUE D22 spécifique, aucune comparaison BEFORE/AFTER signée. Les runs verts du SHA précédent `5933bb9f` deviennent historiques pour cette branche.
- **Maintien du NO-GO** : ni les six tests widget ni la CI ne peuvent remplacer G1–G7, la correction `onboarding 70/180` et la FUE réelle ; PR reste Draft sans merge/déploiement.


## 01/11/2026 — décision propriétaire D22 G2–G5 produit approuvée ; travaux techniques sûrs

**Goal :** figer explicitement les quatre principes G2–G5 au niveau produit, sans jamais les représenter comme des recommandations médicales ni comme un contrat numérique clinique signé.

**Validé par le propriétaire (produit uniquement) :** G2 absence de cible automatiquement autorisée ; G3 legacy inconnu conservé brut sans conversion/classification ; G4 préférence d'affichage séparée de l'intégrité des valeurs, facteur/arrondi précis encore en revue ; G5 aucune classe cible sans autorité individuelle ni faux TIR CGM à partir de relevés manuels.

**Gates inchangés :** G1, G6, G7 restent PENDING. Revue clinique spécialisée des G2–G5 et facteur numérique G4 restent PENDING. L'onboarding conserve toujours le défaut 70/180 et le profil la saisie brute ; ce commit de préparation NE les corrige PAS. Pas de migration et pas de Vercel.

**Preuve déjà établie avant ce changement :** PR #1213 HEAD 5e16882, CI #41314664294 SUCCESS, 8/8 tests spécifiques D22 réussis, mais FUE réelle D22 Chrome/BEFORE-AFTER NOT_RUN ; une automatisation D5 hors périmètre a échoué. Ces preuves précédentes ne certifient pas le futur SHA.

**Préparation technique supplémentaire :** enrichir l'oracle D22 test-only pour refuser explicitement les lectures manuelles / sources inconnues en tant que preuve de TIR CGM et pour exiger une fenêtre temporelle documentée et une règle de métrique revue. Aucun seuil, facteur, valeur patient ou comportement de production modifié. Le produit complet demeure FUE_NO_GO / RELEASE_NO_GO.

**Next exact :** CI exacte du nouveau HEAD, review G1/G6/G7 et revue clinique des principes approuvés, puis implémentation du modèle vérifié, tests négatifs/migrations et FUE Web FR/AR 390/768/1280. 
