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
6. TIR/CV/AGP/GMI/GRI restent bloqués tant que leur contrat requis n’est pas prouvé ;
7. la suffisance CGM peut prouver cadence, couverture et fenêtre ;
8. les analyses longitudinales restent descriptives sans causalité/prédiction fictive ;
9. tests ciblés + suites SQLite/PostgreSQL + CI finale sont verts ;
10. evidence registry, runtime et présent fichier sont cohérents ;
11. le re-audit pondéré final atteint **≥9,0/10** sans note artificielle.

### Preuve finale

`main` final + tests synthétiques non-patient + CI GitHub + re-audit item par item + présent fichier à jour.

---

## 2. ÉTAT DES LOTS

### ANALYSIS-0 — Integrity & observability gate — CLOSED ✅

**Goal** : distinguer données insuffisantes, analyse partielle et panne technique.  
**Preuve** : PR #537 ; merge `ec18c9bc2c18e3d5cd87224902229c2a75227bdb` ; post-merge CI #34207685998 SUCCESS ; drift #34207685984 SUCCESS.

### ANALYSIS-1 — Canonical input contract — CLOSED ✅

**Goal** : une seule vérité d’entrée clinique runtime.  
**Preuve** : PR #538 ; merge `4bc8c706186c5c581d941ec6c5eb556930365f3f` ; post-merge CI #34212026116 SUCCESS ; drift #34212026120 SUCCESS.

### ANALYSIS-2 — Alerting contract correctness — CLOSED ✅

**Goal** : chaque alerte déclarée doit être atteignable, déterministe et testée par le moteur public enregistré.  
**Preuve** : PR #539 ; merge `f3da008a4390e839b65465f4e6faf59668023f68` ; post-merge CI #34232357895 SUCCESS ; drift #34232357898 SUCCESS.

### ANALYSIS-3 — Single evidence authority — CLOSED ✅

**Goal** : aucune voie publique/production ne doit exposer KPI normatifs, patterns ou résumés cliniques hors de la frontière evidence-gated.

**Réalisé** : ancien `summary.py` neutralisé fail-closed ; plage glucose runtime unifiée `30–600 mg/dL` ; garde AST anti-import du moteur brut ; routes publiques auditées ; `ModuleRegistry` verrouillé sur l’autorité evidence-gated + alerting.  
**Preuve** : PR #540 ; merge `43188147455a4b26af9c59496d018b838aa076cb` ; post-merge CI #34237020000 SUCCESS ; drift #34237020046 SUCCESS.

### ANALYSIS-4 — Real CGM sufficiency contract — CLOSED ✅

**Goal** : prouver la qualité d’une fenêtre CGM depuis des faits persistés, pas seulement `source='cgm'`.

**Réalisé** : session capteur pseudonymisée, cadence attendue, fenêtre active, couverture conservatrice, déduplication temporelle, multi-capteurs séquentiels, échec fermé sur chevauchement/timezone/durée/couverture insuffisants.  
**Preuve** : PR #541 ; merge `71a8b86ac46a2b15ba782e9c8bde3f6e58dda779` ; post-merge CI #34247637204 SUCCESS ; drift #34247637242 SUCCESS.

### ANALYSIS-5 — Governed CGM analytics promotion — CLOSED ✅

**Goal** : promouvoir seulement des métriques recalculées sur des lectures CGM certifiées par A4.

**Réalisé** : calcul CGM natif sur lectures sessionnées ; TIR/TAR/TBR/CV seulement après fenêtre A4 + evidence gouvernée ; KPI `LogEntry` contradictoires restent descriptifs ; GMI/GRI restent fermés/candidats ; ton clinique neutre avant A6.  
**Limitation runtime** : Nightscout actuel n’apporte pas encore les faits de session nécessaires et reste fail-closed pour la promotion.  
**Preuve** : PR #542 ; pré-merge `aac4b75302d12d740e76f4868253a519ff91947d` ; CI #34257276611 SUCCESS ; drift #34257276474 SUCCESS ; merge `9681b77ee2ac71c710120a26f4e98597645af927` ; post-merge CI #34272156304 SUCCESS ; drift #34272156421 SUCCESS.

### ANALYSIS-6 — Contextual targets & population applicability — CLOSED ✅

**Goal** : aucune phrase normative « dans/hors cible » sans provenance de cible + population/applicabilité valides.

**Réalisé** :
- provenance, population, objectif de temps dans plage et timestamp de confirmation persistés séparément ;
- legacy `70–180` reste descriptif ;
- modification patient de la plage retire l’autorité clinique ;
- changement de type/date de naissance rend une confirmation existante stale ;
- champs internes d’autorité absents du payload PATCH public ;
- aucune cible/population guideline auto-inférée depuis la démographie ;
- comparaison autorisée uniquement après confirmation clinicien + population explicite + objectif % + plage valide + confirmation non future + CGM A4 vérifié ;
- plage personnalisée séparée du TIR standard A5 ;
- panne du sous-calcul cible → analyse `partial`, sans faux verdict ;
- narration et ton restent non prescriptifs/neutres.

**Preuve** : PR #543 ; pré-merge HEAD `314855b7463ace3ea33bec93ddcb3e32c137d4fb` ; CI #34274613150 SUCCESS ; drift #34274613219 SUCCESS ; merge `c829eb7092a365f92a021768806a809508d4e70f` ; post-merge CI #34279210367 SUCCESS (backend SQLite/PostgreSQL verts) ; drift #34279210339 SUCCESS.

### ANALYSIS-7 — Richer personal analytics without fake causality — ACTIVE 🟡

**Goal** : ajouter de la valeur longitudinale personnelle sans appariement, causalité, prescription ou prédiction inventés.

**Audit de départ** : le Clinical Twin couvre déjà récidive, densité d’évidence, baseline personnelle, mouvement relatif à cette baseline, persistance et résolution. Le manque principal est l’absence de lien exact entre une mesure `pre_meal` et la mesure `post_meal` du même épisode.

**Branche** : `analysis/paired-meal-response`  
**PR** : #544 (draft)  
**Base** : `main@c829eb7092a365f92a021768806a809508d4e70f`  
**HEAD code avant ce commit documentaire** : `7c73a2f347692f7a64fc46ece646182c8f5bbeba`

**Implémenté dans le diff** :
- `LogEntry.meal_episode_id` UUID nullable et indexé ;
- contrainte DB : un seul rôle `pre_meal` et un seul rôle `post_meal` par patient + épisode ;
- anciens `pre_meal/post_meal` sans UUID restent valides mais ne sont jamais appariés implicitement ;
- contrat canonique : UUID d’épisode seulement avec contexte `pre_meal|post_meal` et type de repas explicite supporté ;
- create/batch/PATCH passent par ce contrat ; un lien erroné peut être explicitement retiré ;
- savepoint par ligne dans le batch afin qu’un conflit d’intégrité n’empoisonne pas les lignes suivantes ;
- `compute_paired_meal_response()` groupe uniquement par UUID explicite, même patient, même type de repas, exactement un pré + un post, post strictement après pré ;
- aucune fenêtre temporelle clinique n’est inventée : seul l’ordre est requis ;
- exclusion `demo` et des lignes futures ;
- exposition descriptive : pré, post, delta mg/dL, temps écoulé ;
- delta négatif conservé comme fait observé ;
- agrégat par type de repas seulement après le plancher produit existant `3 paires / 2 jours` ; densité d’évidence = répétabilité, jamais probabilité ;
- endpoint patient-scoped `/personal-response/paired-meals/` ;
- aucun nouveau moteur longitudinal parallèle au Clinical Twin.

**Tests synthétiques ajoutés** : paire exacte, absence d’UUID, épisode incomplet, types incohérents, ordre invalide, isolation patient, doublon rôle DB, exclusion demo, agrégat multi-jours, delta négatif, validation create/PATCH, retrait de lien, conflit batch suivi d’une ligne valide.

**État de preuve** : PR #544 ouverte en draft. Les premiers workflows sont en cours ; ce commit documentaire devient le HEAD à certifier. A7 n’est pas CLOSED avant CI + drift verts sur le HEAD final, OpenAPI cohérent, branche mergeable, absence de review thread bloquant, merge verrouillé et post-merge verts.

### ANALYSIS-8 — Prediction / causal inference research gate — FUTURE

Hors chemin critique. `prediction.py` doit rester fail-closed et `correlations.py` désactivé tant qu’un protocole scientifique dédié n’est pas certifié.

---

## 3. ORDRE D’EXÉCUTION

`ANALYSIS-0 ✅ → A1 ✅ → A2 ✅ → A3 ✅ → A4 ✅ → A5 ✅ → A6 ✅ → A7 ACTIVE → RECERTIFICATION FINALE`

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

Règles : capacité absente = aucun score fonctionnel positif ; fail-closed peut scorer en sécurité mais pas en capacité ; aucun 10/10 sans preuve ; runtime non testé = non certifié ; docs seules ≠ comportement runtime.

---

## 5. TEST MATRIX MINIMALE FINALE

- unités/bornes/timestamps glucose ;
- isolation patient ;
- SQL analytics et dégradations ;
- toutes branches d’alertes ;
- Clinical Twin reconciliation après modification/suppression ;
- CGM incomplete/valid/multi-sensor ;
- gates TIR/CV/AGP/GMI/GRI ;
- population/targets + provenance cible ;
- paires repas explicites + missingness + absence d’appariement implicite ;
- evidence/LLM boundary ;
- fallback offline et langues critiques ;
- aucune causalité/diagnostic/dose/prédiction inventée ;
- CI complète sur HEAD final.

---

## 6. ÉTAT DE REPRISE

### CLOSED
- A0 — PR #537 — post-merge certifié.
- A1 — PR #538 — post-merge certifié.
- A2 — PR #539 — post-merge certifié.
- A3 — PR #540 — post-merge certifié.
- A4 — PR #541 — post-merge certifié.
- A5 — PR #542 — post-merge certifié.
- A6 — PR #543 — merge `c829eb7092a365f92a021768806a809508d4e70f` — post-merge CI #34279210367 SUCCESS + drift #34279210339 SUCCESS.

### ACTIVE
- A7 — PR #544 — explicit paired meal response.

### OPEN
- recertification finale pondérée + cohérence evidence/docs + CI finale.

### NEXT EXACT

Certifier le HEAD final A7 par CI + drift → corriger tout échec → OpenAPI cohérent → vérifier mergeability/reviews → READY #544 → merge verrouillé → post-merge → re-audit pondéré item par item.

### Séquence restante

A7 final CI/drift → ready/merge/post-merge → re-audit pondéré → corrections si score <9 ou preuve manquante → cohérence evidence/docs → CI finale → closeout canonique.

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
