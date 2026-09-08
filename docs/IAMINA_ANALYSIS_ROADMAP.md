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

### ANALYSIS-4 — Real CGM sufficiency contract — ACTIVE 🟡

**Goal** : prouver la qualité d’une fenêtre CGM depuis des faits persistés, pas seulement `source='cgm'`.

**Branche** : `analysis/real-cgm-sufficiency-contract`  
**PR** : #541 (draft)  
**HEAD avant ce commit documentaire** : `62ca51126c0abbfb1277b9d7b073a5313b61c2e0`

**Réalisé dans le diff** :
- ajout de `CGMSensorSession` pseudonymisé avec source, identifiant session, début/fin, cadence attendue, timezone et raison de fin ;
- liaison optionnelle des `CGMReadingRecord` à une session capteur ;
- conservation de la déduplication patient/source existante ;
- `assess_cgm_window()` calcule une couverture conservatrice à partir de la fraction de fenêtre active et du ratio lectures uniques reçues/attendues ;
- doublons temporels non inflationnistes ;
- multi-capteurs séquentiels supportés ;
- chevauchement de sessions ambigu fail-closed ;
- fenêtre timezone-naive fail-closed ;
- fenêtre <14 jours fail-closed ;
- seuil de couverture 70% testé ;
- aucune promotion normative TIR/CV/AGP/GMI/GRI dans ce lot, réservée à ANALYSIS-5.

**Preuves actuelles** :
- migration `0031_cgmsensorsession_cgmreadingrecord_session.py` ajoutée ;
- CI initiale #34238548505 : PostgreSQL source-of-truth + validation migration SUCCESS, mais job Ruff en échec uniquement pour ordre d’import du nouveau test ;
- correction Ruff poussée en `62ca51126c0abbfb1277b9d7b073a5313b61c2e0` ;
- drift final #34238832688 SUCCESS ;
- CI finale #34238832498 encore in_progress au moment de cette mise à jour ;
- PR #541 mergeable=true, aucun review thread ouvert ;
- branche 0 behind `main` avant ce commit documentaire.

**Succès** : une fixture synthétique admissible sur 14 jours peut devenir `verified=True`; les fenêtres incomplètes/ambiguës restent `False` avec raison exacte.

**Preuve restante avant READY** : CI complète verte sur le HEAD final incluant ce closeout documentaire, puis merge + preuve post-merge.

---

### ANALYSIS-5 — Governed CGM analytics promotion — OPEN

**Goal** : promouvoir progressivement les métriques CGM uniquement si evidence + population + sufficiency passent.

Ordre : TIR/TAR/TBR → CV → AGP → GMI après décision version/formule → GRI après validation propre.

---

### ANALYSIS-6 — Contextual targets & population applicability — OPEN

**Goal** : aucune phrase normative “dans/hors cible” sans target provenance + population/applicabilité valide.

Fail-closed requis pour populations non gouvernées ; aucune recommandation thérapeutique dérivée du dépassement d’une cible.

---

### ANALYSIS-7 — Richer personal analytics without fake causality — OPEN

**Goal** : ajouter de la valeur longitudinale sans causalité fictive.

Candidats : paires pré/post-prandiales structurées, répétabilité, baseline personnelle, évolution des patterns, données manquantes utiles, visualisation explicite de l’incertitude.

Interdit : diagnostic, causalité, prescription, dose, optimisation thérapeutique, prédiction non validée, pseudo-probabilité de confiance.

---

### ANALYSIS-8 — Prediction / causal inference research gate — FUTURE

Hors chemin critique. `prediction.py` doit rester fail-closed et `correlations.py` désactivé tant qu’un protocole scientifique dédié n’est pas certifié.

---

## 3. ORDRE D’EXÉCUTION

`ANALYSIS-0 ✅ → ANALYSIS-1 ✅ → ANALYSIS-2 ✅ → ANALYSIS-3 ✅ → ANALYSIS-4 ACTIVE → ANALYSIS-5 → ANALYSIS-6 → ANALYSIS-7 → RECERTIFICATION FINALE`

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
- population/targets ;
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
- ANALYSIS-3 — PR #540 — merge `43188147455a4b26af9c59496d018b838aa076cb` — post-merge CI #34237020000 SUCCESS + drift #34237020046 SUCCESS.

### ACTIVE
- ANALYSIS-4 — PR #541 — real CGM sufficiency contract.

### OPEN
- ANALYSIS-5 à ANALYSIS-7 ;
- recertification finale.

### NEXT EXACT

Obtenir CI + drift verts sur le HEAD final ANALYSIS-4 incluant ce fichier → vérifier branche 0 behind `main` → passer #541 ready → merge avec expected HEAD → vérifier `main` + CI/drift post-merge → marquer ANALYSIS-4 CLOSED → ouvrir ANALYSIS-5.

### Séquence restante

A4 final CI/drift → ready/merge/post-merge → A5 → A6 → A7 → re-audit pondéré → cohérence evidence/docs → CI finale → closeout canonique.

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
