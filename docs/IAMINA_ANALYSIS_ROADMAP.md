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

**Réalisé** :
- `analysis_status = complete | partial | unavailable | insufficient_data` ;
- codes de dégradation stables, non-PHI ;
- panne KPI → `unavailable` ;
- panne détecteur → `partial` ;
- insuffisance réelle → `insufficient_data`.

**Preuve** : PR #537 ; merge `ec18c9bc2c18e3d5cd87224902229c2a75227bdb` ; post-merge CI #34207685998 SUCCESS ; drift #34207685984 SUCCESS.

---

### ANALYSIS-1 — Canonical input contract — CLOSED ✅

**Goal** : une seule vérité d’entrée clinique runtime.

**Réalisé** :
- contrat glucose runtime `30–600 mg/dL` ;
- conversion canonique `mg/dL | mmol/L | g/L` ;
- unités inconnues et valeurs non finies rejetées ;
- `logged_at` futur >5 min rejeté ;
- lignes futures exclues KPI/daily/AGP/fallback CV ;
- contextes/source inconnus rejetés aux frontières runtime ;
- matrice de tests bornes/conversions/timestamps/catégories.

**Preuve** : PR #538 ; merge `4bc8c706186c5c581d941ec6c5eb556930365f3f` ; post-merge CI #34212026116 SUCCESS ; drift #34212026120 SUCCESS.

**Note** : le dernier shim direct UnitGuard `20–700` est supprimé dans ANALYSIS-3 ; il délègue désormais au contrat canonique `30–600`.

---

### ANALYSIS-2 — Alerting contract correctness — CLOSED ✅

**Goal** : chaque alerte déclarée doit être atteignable, déterministe et testée par le moteur public enregistré.

**Réalisé** :
- moteur public `EvidenceGuardedAlertingDiabetesEngine` ;
- `HYPER_SUSTAINED` alimenté par les deux mesures antérieures du même patient ;
- isolation inter-patient ;
- priorité des alertes courantes sur l’historique ;
- seuils exacts testés ;
- FR / ar / ar-MA ;
- aucun numéro d’urgence national inventé ;
- warnings non bloquants journalisés comme `alert`, critical/emergency comme `emergency`.

**Preuve** : PR #539 ; merge `f3da008a4390e839b65465f4e6faf59668023f68` ; pré-merge CI #34218965389 SUCCESS + drift #34218965478 SUCCESS ; post-merge CI #34232357895 SUCCESS + drift #34232357898 SUCCESS.

---

### ANALYSIS-3 — Single evidence authority — ACTIVE 🟡

**Goal** : aucune voie publique/production ne doit exposer KPI normatifs, patterns ou résumés cliniques hors de la frontière evidence-gated.

**Branche** : `analysis/single-evidence-authority`  
**PR** : #540 (draft)  
**Dernier HEAD connu avant ce commit documentaire** : `7824052b0bcafbe3eeaf89138d370513ec006f79`

**Réalisé et vérifié dans le diff** :
- `backend/diabetes/services/summary.py` est neutralisé fail-closed ;
- suppression du fallback hardcodé qui contenait des affirmations fabriquées et un conseil d’augmentation d’insuline ;
- anciens symboles conservés uniquement pour compatibilité d’import et lèvent `LegacyClinicalSummaryDisabled` ;
- aucun appel LLM ni écriture `AISummary` possible via ces anciens points d’entrée ;
- `validate_mg_dl()` ne possède plus de plage secondaire `20–700` et délègue au contrat canonique `30–600` ;
- tests legacy mis à jour sur `30–600` ;
- test d’architecture AST : aucun import production de `DiabetesEngine` brut hors `evidence_engine.py` ;
- `ModuleRegistry` reste verrouillé sur l’autorité evidence-gated + alerting ;
- `/kpis/` projette via `project_public_kpis()` ;
- Companion/narrator obtient ses données via `get_domain_context()` et le moteur enregistré ;
- routes `analytics`, `cgm`, `companion` auditées sans bypass normatif prouvé.

**Preuves intermédiaires** :
- HEAD `b59bf51488141026123a0ba2505a3d0279037958` : CI #34234067575 SUCCESS + drift #34234067565 SUCCESS ;
- HEAD `7824052b0bcafbe3eeaf89138d370513ec006f79` : drift #34234793208 SUCCESS ; CI #34234793266 encore queued au moment de cette mise à jour.

**Succès** : recherche repo + tests d’architecture + tests runtime prouvent une seule autorité clinique publique ; aucune sortie legacy dangereuse ne reste callable.

**Preuve restante avant READY** : CI complète verte sur le HEAD final incluant ce closeout documentaire, puis branche 0 behind `main`.

---

### ANALYSIS-4 — Real CGM sufficiency contract — OPEN

**Goal** : prouver la qualité d’une fenêtre CGM, pas seulement `source='cgm'`.

À construire : identité/session capteur pseudonymisée, cadence attendue, readings attendues/reçues, active intervals, couverture/wear-time, timezone, déduplication, trous vs arrêt capteur, multi-sensor.

**Succès** : une fixture synthétique admissible devient `verified=True`; les fenêtres incomplètes restent `False` avec raison exacte.

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

`ANALYSIS-0 ✅ → ANALYSIS-1 ✅ → ANALYSIS-2 ✅ → ANALYSIS-3 ACTIVE → ANALYSIS-4 → ANALYSIS-5 → ANALYSIS-6 → ANALYSIS-7 → RECERTIFICATION FINALE`

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

### ACTIVE
- ANALYSIS-3 — PR #540.

### OPEN
- ANALYSIS-4 à ANALYSIS-7 ;
- recertification finale.

### NEXT EXACT

Obtenir CI + drift verts sur le HEAD final ANALYSIS-3 incluant ce fichier → vérifier branche 0 behind `main` → passer #540 ready → merge avec expected HEAD → vérifier `main` + CI/drift post-merge → marquer ANALYSIS-3 CLOSED → ouvrir ANALYSIS-4.

### Séquence restante

A3 final CI/drift → ready/merge/post-merge → A4 → A5 → A6 → A7 → re-audit pondéré → cohérence evidence/docs → CI finale → closeout canonique.

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
