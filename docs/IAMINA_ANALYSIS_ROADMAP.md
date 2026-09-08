# IAMINA — ANALYSE CLINIQUE ≥9/10 — FICHIER CANONIQUE

> **Statut** : ACTIVE ROADMAP  
> **Créé le** : 2026-09-08  
> **Repo** : `hraaaaf/IAMINA-MVP`  
> **Branche canonique** : `main`  
> **Baseline audit statique** : ~7,9/10, non équivalent à une certification runtime  
> **Déploiement Vercel** : INTERDIT sans autorisation explicite  
> **Données patient** : aucune donnée patient réelle nécessaire

---

## 1. GOAL FINAL

Faire passer le moteur d’analyse IAMINA à **≥9,0/10 réellement certifié**, sans sacrifier sécurité clinique, incertitude, traçabilité, isolation patient ou architecture capsule.

### Succès final observable

Le chantier est CLOSED uniquement si :

1. les contrats d’entrée sont cohérents et fail-closed ;
2. chaque analyse expose `complete | partial | unavailable | insufficient_data` ;
3. aucune voie publique ne contourne l’autorité evidence-gated ;
4. chaque alerte déclarée est réellement atteignable et testée ;
5. aucune cible normative n’est appliquée sans provenance/applicabilité ;
6. TIR/CV/AGP/GMI/GRI restent bloqués tant que le contrat CGM requis n’est pas prouvé ;
7. la suffisance CGM peut prouver cadence, couverture et fenêtre ;
8. les analyses longitudinales restent descriptives sans validation causale/prédictive ;
9. tests ciblés + suites SQLite/PostgreSQL + CI finale sont verts ;
10. evidence registry, runtime et ce fichier sont cohérents ;
11. le re-audit pondéré final atteint **≥9,0/10** sans note artificielle.

### Preuve finale

`main` final + tests synthétiques non-patient + CI GitHub + re-audit item par item + présent fichier à jour.

---

## 2. ÉTAT DES LOTS

### ANALYSIS-0 — Integrity & observability gate — CLOSED ✅

**Goal** : distinguer données insuffisantes, analyse partielle et panne technique.

**Preuve** : PR #537 ; merge `ec18c9bc2c18e3d5cd87224902229c2a75227bdb` ; post-merge CI #34207685998 SUCCESS ; drift #34207685984 SUCCESS.

---

### ANALYSIS-1 — Canonical input contract — CLOSED ✅

**Goal** : une seule vérité d’entrée clinique runtime.

**Preuve** : PR #538 ; merge `4bc8c706186c5c581d941ec6c5eb556930365f3f` ; post-merge CI #34212026116 SUCCESS ; drift #34212026120 SUCCESS.

---

### ANALYSIS-2 — Alerting contract correctness — CLOSED ✅

**Goal** : chaque alerte déclarée doit être atteignable, déterministe et testée par le moteur public enregistré.

**Preuve** : PR #539 ; merge `f3da008a4390e839b65465f4e6faf59668023f68` ; post-merge CI #34232357895 SUCCESS + drift #34232357898 SUCCESS.

---

### ANALYSIS-3 — Single evidence authority — CLOSED ✅

**Goal** : aucune voie publique/production ne doit exposer KPI normatifs, patterns ou résumés cliniques hors de la frontière evidence-gated.

**Réalisé** :
- ancien `summary.py` clinique neutralisé fail-closed ;
- suppression du fallback contenant affirmations fabriquées et conseil d’augmentation d’insuline ;
- `validate_mg_dl()` aligné exclusivement sur `30–600 mg/dL` ;
- garde AST anti-import du `DiabetesEngine` brut hors wrapper evidence ;
- routes KPI/Companion/narrator/doctor brief auditées sans bypass normatif public prouvé ;
- `ModuleRegistry` verrouillé sur l’autorité evidence-gated + alerting.

**Preuve** : PR #540 ; merge `43188147455a4b26af9c59496d018b838aa076cb` ; post-merge CI #34237020000 SUCCESS ; drift #34237020046 SUCCESS.

---

### ANALYSIS-4 — Real CGM sufficiency contract — CLOSED ✅

**Goal** : prouver la qualité d’une fenêtre CGM depuis des faits persistés, pas seulement `source='cgm'`.

**Réalisé** :
- `CGMSensorSession` pseudonymisé : source, session opaque, début/fin, cadence attendue, timezone, raison de fin ;
- `CGMReadingRecord` peut être lié à une session ;
- `assess_cgm_window()` calcule une couverture conservatrice = fenêtre capteur active × capture réelle ;
- doublons temporels non inflationnistes ;
- multi-capteurs séquentiels supportés ;
- chevauchements ambigus, timezone absente, durée <14 jours et couverture <70% échouent fermés ;
- aucune promotion normative dans A4.

**Preuve** : PR #541 ; pré-merge HEAD `8b2bcb1ded53c24eb7686b1986af1d3b1ce20527` ; CI #34244731763 SUCCESS ; drift #34244731722 SUCCESS ; merge `71a8b86ac46a2b15ba782e9c8bde3f6e58dda779` ; post-merge CI #34247637204 SUCCESS ; drift #34247637242 SUCCESS.

---

### ANALYSIS-5 — Governed CGM analytics promotion — CLOSED ✅

**Goal** : promouvoir seulement des métriques recalculées sur des lectures CGM réellement certifiées par A4.

**Réalisé** :
- `compute_verified_cgm_metrics()` calcule sur `CGMReadingRecord` sessionnés uniquement ;
- lectures non liées, source/session incohérente ou hors intervalle session exclues ;
- timestamps dupliqués dédupliqués avant calcul ;
- TIR/TAR/TBR/CV publiés seulement si fenêtre A4 vérifiée + evidence `GOVERNED_RULE` + métrique CGM-native présente ;
- KPI `LogEntry` contradictoires restent descriptifs et ne peuvent pas fournir les métriques CGM promues ;
- `/kpis/` promeut seulement la plage standard 70–180 mg/dL ;
- moteur public `EvidenceGuardedDiabetesEngine` consomme la même frontière ;
- trend historique `LogEntry` reste fermé même lorsque le CGM est vérifié ;
- GMI/GRI restent `null` / candidate ;
- A5 garde les `tone_signals` cliniques à `None`, donc un TIR certifié ne peut pas générer seul un jugement « dans/hors cible » avant A6 ;
- tests synthétiques couvrent fenêtre valide, isolation vis-à-vis de `LogEntry`, fenêtre insuffisante, absence de payload CGM, GMI/GRI fermés et frontière A5→A6.

**Limitation runtime vérifiée** : le sync Nightscout actuel persiste des `CGMReadingRecord` sans `CGMSensorSession`. Aucune cadence/session n’est inférée à partir du champ `device`; ces données restent fail-closed tant qu’un provider ne fournit pas explicitement les faits de session nécessaires.

**Preuve** : PR #542 ; pré-merge HEAD `aac4b75302d12d740e76f4868253a519ff91947d` ; CI #34257276611 SUCCESS ; drift #34257276474 SUCCESS ; merge `9681b77ee2ac71c710120a26f4e98597645af927` ; post-merge CI #34272156304 SUCCESS ; drift #34272156421 SUCCESS.

---

### ANALYSIS-6 — Contextual targets & population applicability — ACTIVE 🟡

**Goal** : aucune phrase normative « dans/hors cible » sans target provenance + population/applicabilité valide.

**Branche** : `analysis/contextual-target-applicability`  
**PR** : #543 (draft)  
**Base** : `main@9681b77ee2ac71c710120a26f4e98597645af927`  
**HEAD code avant ce commit documentaire** : `d9f1f899df1cb24019e12adfe28a1079b114c714`

**Implémenté dans le diff** :
- métadonnées persistantes séparant plage configurée et autorité clinique : provenance, population explicite, objectif de temps dans la plage %, timestamp de confirmation ;
- toutes les lignes historiques restent `legacy_default` / `unknown`, donc aucune cible clinique n’est créée rétroactivement ;
- modification patient de la plage → `patient_declared`, population inconnue, objectif/confirmation effacés ;
- changement patient du type de diabète ou de la date de naissance → confirmation clinicien existante marquée stale et autorité effacée ;
- les champs internes d’autorité cible sont absents du modèle PATCH public et ne peuvent pas entrer dans son payload de mutation ; les extras restent ignorés pour préserver le contrat OpenAPI existant ;
- aucune population/cible guideline n’est auto-inférée depuis âge, type, sexe ou autre démographie ;
- une comparaison nécessite : provenance `clinician_confirmed` + diabète connu + population explicite + confirmation non future + plage valide + objectif % explicite + CGM A4 vérifié ;
- plage personnalisée calculée séparément du TIR standard A5 sous `target_range_pct` ;
- résultat structuré `meets_confirmed_goal | below_confirmed_goal | unavailable` ;
- la narration LLM ne reçoit le résultat que si tous les gates passent et rappelle explicitement qu’aucun changement de traitement/dose n’est autorisé ;
- panne du sous-calcul cible → analyse `partial`, métriques CGM valides conservées, jugement cible indisponible ;
- le ton relationnel reste cliniquement neutre ;
- OpenAPI public conservé stable.

**Tests ajoutés / adaptés** : legacy/default, patient-declared, population inconnue, confirmation future, objectif % invalide, cible clinicien valide, CGM insuffisant, champs internes hors payload PATCH, plage croisée, séparation TIR standard/plage personnelle, panne target metric partielle, unité A0 isolant explicitement l’absence de profil cible.

**Preuves intermédiaires vérifiées** :
- migration `0032_diabetesprofile_target_authority` appliquée avec succès sur PostgreSQL ;
- première suite PostgreSQL A6 : 2169 tests PASS, 1 échec hérité dû à un `SimpleTestCase` effectuant implicitement la nouvelle lecture de profil cible ; test corrigé explicitement, sans changement du comportement production ;
- Ruff, import-linter, anti-bypass LLM/egress et Bandit verts sur le premier HEAD code ;
- dérive OpenAPI initiale limitée à la docstring PATCH + `additionalProperties:false`, ensuite supprimée en restaurant le contrat public stable ;
- drift #34274302687 SUCCESS sur `d9f1f899...` ; CI #34274302666 était encore en cours au moment de ce commit documentaire.

**État de preuve** : ce commit documentaire devient le nouveau HEAD final à certifier. A6 n’est pas CLOSED avant CI + drift verts sur ce HEAD exact, branche 0 behind, absence de review thread bloquant, merge verrouillé et post-merge verts.

---

### ANALYSIS-7 — Richer personal analytics without fake causality — OPEN

**Goal** : ajouter de la valeur longitudinale sans causalité fictive.

**Audit de départ vérifié** : le Clinical Twin possède déjà recurrence, evidence density, baseline personnelle sur fenêtre, mouvement relatif à cette baseline, persistance/résolution et limites explicites anti-causalité. `personal_response.py` sait déjà identifier des contextes positifs répétés et des mesures `post_meal` par type de repas.

**Manque principal à traiter** : les patterns repas actuels comparent des mesures post-prandiales absolues à une baseline de fenêtre ; ils ne possèdent pas de lien explicite entre une mesure `pre_meal` et la mesure `post_meal` du même épisode.

**Direction minimale** :
- ajouter un identifiant opaque d’épisode repas explicite et optionnel ;
- calculer un delta pré→post uniquement pour des entrées partageant cet identifiant et satisfaisant un contrat temporel/qualité strict ;
- aucune association par simple proximité temporelle si l’identifiant manque ;
- exposer complétude/missingness, répétabilité et évolution descriptive des deltas ;
- réutiliser le Clinical Twin existant plutôt que créer une seconde autorité longitudinale.

Interdit : diagnostic, causalité, prescription, dose, optimisation thérapeutique, prédiction non validée, pseudo-probabilité de confiance.

---

### ANALYSIS-8 — Prediction / causal inference research gate — FUTURE

Hors chemin critique. `prediction.py` doit rester fail-closed et `correlations.py` désactivé tant qu’un protocole scientifique dédié n’est pas certifié.

---

## 3. ORDRE D’EXÉCUTION

`ANALYSIS-0 ✅ → ANALYSIS-1 ✅ → ANALYSIS-2 ✅ → ANALYSIS-3 ✅ → ANALYSIS-4 ✅ → ANALYSIS-5 ✅ → ANALYSIS-6 ACTIVE → ANALYSIS-7 → RECERTIFICATION FINALE`

ANALYSIS-8 reste hors chemin critique.

---

## 4. SCORING DE RECERTIFICATION

| Axe | Poids |
|---|---:|
| sécurité clinique / epistemic safety | 20% |
| qualité & exactitude analytique | 15% |
| evidence / provenance / applicability | 15% |
| intégrité des entrées | 10% |
| fiabilité / dégradation / observabilité | 10% |
| CGM sufficiency & analytics | 10% |
| longitudinal / Clinical Twin | 8% |
| proactive intelligence | 5% |
| LLM boundary | 4% |
| tests / CI / runtime proof | 3% |

Règles : aucune capacité absente ne reçoit un score fonctionnel positif ; fail-closed peut scorer en sécurité mais pas en capacité ; aucun 10/10 sans preuve ; runtime non testé = non certifié ; docs seules ≠ comportement runtime.

---

## 5. TEST MATRIX MINIMALE FINALE

- unités/bornes/timestamps glucose ;
- isolation patient ;
- SQL analytics ;
- SQL/detector failures + états partial/unavailable ;
- toutes branches d’alertes ;
- Clinical Twin reconciliation après modification/suppression ;
- CGM incomplete/valid/multi-sensor ;
- gates TIR/CV/AGP/GMI/GRI ;
- population/targets + provenance cible ;
- paires repas explicites + missingness + absence d’appariement implicite ;
- plafond d’evidence LLM ;
- fallback offline ;
- langues critiques ;
- aucune causalité/diagnostic/dose inventée ;
- CI complète sur HEAD final.

---

## 6. ÉTAT DE REPRISE

### CLOSED
- ANALYSIS-0 — PR #537 — post-merge certifié.
- ANALYSIS-1 — PR #538 — post-merge certifié.
- ANALYSIS-2 — PR #539 — post-merge certifié.
- ANALYSIS-3 — PR #540 — post-merge certifié.
- ANALYSIS-4 — PR #541 — merge `71a8b86ac46a2b15ba782e9c8bde3f6e58dda779` — post-merge CI #34247637204 SUCCESS + drift #34247637242 SUCCESS.
- ANALYSIS-5 — PR #542 — merge `9681b77ee2ac71c710120a26f4e98597645af927` — post-merge CI #34272156304 SUCCESS + drift #34272156421 SUCCESS.

### ACTIVE
- ANALYSIS-6 — PR #543 — contextual target applicability.

### OPEN
- ANALYSIS-7 ;
- recertification finale.

### NEXT EXACT

Certifier le HEAD final ANALYSIS-6 par CI + drift → corriger tout échec → vérifier branche 0 behind `main` + review threads → READY #543 → merge verrouillé → post-merge → ANALYSIS-7.

### Séquence restante

A6 final CI/drift → ready/merge/post-merge → A7 → re-audit pondéré → cohérence evidence/docs → CI finale → closeout canonique.

---

## 7. RÈGLES DE SÉCURITÉ

- fixtures synthétiques uniquement ;
- aucune prescription/modification de dose ;
- aucune activation de prédiction sans validation séparée ;
- aucune promotion implicite d’une candidate evidence rule ;
- aucun Vercel sans autorisation explicite ;
- ne jamais déclarer ≥9/10 avant recertification complète.

---

**FICHIER CANONIQUE : `docs/IAMINA_ANALYSIS_ROADMAP.md`**
