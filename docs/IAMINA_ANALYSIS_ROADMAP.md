# IAMINA — ANALYSE CLINIQUE ≥9/10 — FICHIER CANONIQUE

> **Statut** : ACTIVE ROADMAP  
> **Créé le** : 2026-09-08  
> **Repo** : `hraaaaf/IAMINA-MVP`  
> **Branche canonique** : `main`  
> **HEAD de départ vérifié** : `2e1348afa9d293fcc0f585e5582200a38e0d6f5e`  
> **Déploiement Vercel** : INTERDIT sans autorisation explicite  
> **Données patient** : aucune donnée patient nécessaire pour ce chantier

---

## 1. GOAL FINAL

Faire passer le moteur d'analyse IAMINA d'un **socle statique audité ~7,9/10** à un moteur **≥9/10 réellement certifié**, sans sacrifier la sécurité clinique, l'incertitude, la traçabilité ou l'architecture capsule.

Le score 7,9/10 est un **baseline d'audit statique**, pas une certification runtime.

### Succès final observable

Le chantier est CLOSED uniquement si :

1. les contrats d'entrée clinique sont cohérents et fail-closed ;
2. toute analyse expose un état explicite `complete | partial | unavailable | insufficient_data` ;
3. aucun moteur legacy ne peut contourner la frontière d'evidence publique ;
4. les alertes déterministes réellement déclarées sont atteignables et testées ;
5. les cibles glycémiques normatives ne sont appliquées qu'avec contexte/population admissible ;
6. TIR/CV/AGP/GMI/GRI restent bloqués tant que le contrat CGM réel n'est pas prouvé ;
7. un vrai contrat CGM peut prouver cadence, wear-time et fenêtre d'analyse avant toute promotion normative ;
8. les nouvelles analyses longitudinales restent descriptives tant qu'aucune validation causale/prédictive n'existe ;
9. tests unitaires + intégration + comportement runtime observé sont verts ;
10. la documentation canonique et le registre d'evidence sont cohérents avec le runtime ;
11. un audit final atteint **≥9,0/10** sans note artificielle ni fonction annoncée mais inactive.

### Preuve finale

- code `main` ;
- tests ciblés verts ;
- CI GitHub verte sur le HEAD final ;
- preuves runtime synthétiques non-patient ;
- aucun champ normatif exposé sans gate d'evidence ;
- re-audit final item par item ;
- ce fichier mis à jour avec les preuves exactes.

---

## 2. BASELINE AUDIT 2026-09-08

### Forces vérifiées

- architecture capsule diabète réelle ;
- `EvidenceGuardedDiabetesEngine` enregistré comme moteur public ;
- calculs SQL-first, LLM non autoritaire ;
- evidence registry versionné et immutable ;
- fail-closed CGM actuel ;
- Clinical Twin longitudinal ;
- mémoire personnelle 90 jours ;
- proactive intelligence + attention budget ;
- LLM limité à narration/explication ;
- prédiction glycémique et corrélations non validées volontairement désactivées ;
- GRI volontairement non publié ;
- suppression/modification des sources réconcilie la mémoire clinique.

### Gaps vérifiés / importants

1. **CGM contract absent** : `source='cgm'` ne prouve pas wear-time/cadence ;
2. **analysis degradation opaque** : erreurs de calcul/détecteur peuvent devenir silencieusement “vide” ;
3. **alerte hyper soutenue** : branche nécessitant `recent_readings`, non alimentée par le wrapper principal observé ;
4. **contrats glucose divergents** : middleware 20–700 vs API/DB 30–600 mg/dL ;
5. **timestamps futurs** : borne haute explicite non prouvée sur les écritures/analytics ;
6. **schemas contextuels trop permissifs** : plusieurs champs métier sont de simples `str` ;
7. **targets personnalisées non injectées dans le moteur evidence-gated principal** ;
8. **AGP brut interne** existe sans contrat CGM clinique complet ;
9. **legacy `DiabetesEngine`** reste présent comme classe utilisable ;
10. **corrélation/prédiction** volontairement absentes : ne pas réactiver sans validation dédiée.

---

# 3. ROADMAP ORDonnée

## ANALYSIS-0 — Integrity & observability gate

**Priorité** : P1  
**Goal** : rendre impossible la confusion entre absence de donnée, analyse partielle et panne technique.

### À faire

- introduire un statut d'analyse explicite :
  - `complete`
  - `partial`
  - `unavailable`
  - `insufficient_data`
- transporter les raisons de dégradation sous forme non clinique et non-PHI ;
- quand un détecteur échoue, marquer l'analyse `partial` ;
- quand SQL/KPI échoue, ne jamais transformer la panne en simple “pas assez de données” ;
- ajouter télémétrie non sensible : moteur, étape, code d'erreur, version de règle.

### Succès

Un échec synthétique SQL ou détecteur produit un état explicite et testable sans exposer de donnée patient.

### Preuve

Tests fault-injection + endpoint/runtime synthétique.

---

## ANALYSIS-1 — Canonical input contract

**Priorité** : P1  
**Goal** : une seule vérité pour les entrées cliniques.

### À faire

- unifier les bornes glucose entre middleware, schema API et DB ;
- normaliser `mg/dL`, `mmol/L`, `g/L` au même contrat ;
- empêcher `logged_at > now + tolerance` ;
- empêcher dates absurdes/out-of-domain ;
- remplacer les `str` métier par enums/Literals versionnés :
  - source ;
  - glycemic_context ;
  - meal_type ;
  - stressed ;
  - exercised ;
  - sleep_quality ;
  - fatigue_level ;
  - is_sick ;
- tests API/DB/middleware identiques.

### Succès

Le même payload obtient la même décision de validation à chaque frontière.

### Preuve

Matrice de tests de conversion + boundary values + timestamps + enums.

---

## ANALYSIS-2 — Alerting contract correctness

**Priorité** : P1  
**Goal** : chaque alerte déclarée est réellement atteignable, déterministe et testée.

### À faire

- corriger l'alerte `HYPER_SUSTAINED` : injecter l'historique requis ou retirer la règle du contrat public ;
- verrouiller ordre/priorité : hypo sévère > hypo > hyper sévère > hyper soutenue ;
- tester valeurs frontières exactes ;
- vérifier cohérence avec triage vital et emergency routing ;
- vérifier langues supportées sans inventer de numéro d'urgence.

### Succès

Chaque règle du state machine a au moins un test runtime qui l'atteint par le chemin public réel.

### Preuve

Tests intégration route → engine → alert + golden cases.

---

## ANALYSIS-3 — Single evidence authority

**Priorité** : P1  
**Goal** : aucune voie ne peut exposer des KPI normatifs ou patterns hors de la frontière evidence-gated.

### À faire

- retirer ou rendre non-public le legacy `DiabetesEngine.analyze()` ;
- interdire tout wiring vers l'ancien moteur hors tests de compatibilité ;
- auditer toutes routes/API/summary/companion/doctor brief/LLM context ;
- imposer `project_public_kpis()` / `guard_normative_kpis()` comme frontière unique ;
- ajouter contrat anti-régression : impossible d'exposer TIR/CV/GMI/GRI non gouverné.

### Succès

Une recherche repo + tests architecture prouvent une seule autorité clinique publique.

### Preuve

Import-linter/architecture test + tests de fuite normative.

---

## ANALYSIS-4 — Real CGM sufficiency contract

**Priorité** : P1 critique avant toute promotion CGM  
**Goal** : pouvoir prouver la qualité d'une fenêtre CGM, pas simplement son étiquette de provenance.

### Données minimales à modéliser

- device/sensor identity pseudonymisée ;
- session/sensor start-end ;
- sampling cadence attendue ;
- readings attendues vs reçues ;
- active intervals ;
- wear-time / coverage calculable ;
- source/provider ;
- timezone et fenêtres cohérentes ;
- déduplication/idempotence ;
- trous de données distingués d'un arrêt capteur.

### À faire

- définir le contrat ingestion CGM canonique ;
- créer calcul de sufficiency vérifiable ;
- conserver `verified=False` tant que la preuve n'est pas complète ;
- tests synthétiques : 14j/70%, trous, doublons, cadence irrégulière, timezone, multi-sensor ;
- aucune activation GMI/GRI automatique.

### Succès

Une fenêtre synthétique admissible devient `verified=True`; toutes les fenêtres incomplètes restent `False` avec raison exacte.

### Preuve

Tests unitaires + intégration + fixtures synthétiques non-patient.

---

## ANALYSIS-5 — Governed CGM analytics promotion

**Priorité** : après ANALYSIS-4 uniquement  
**Goal** : exposer progressivement les métriques CGM seulement si evidence + population + sufficiency passent.

### Ordre de promotion

1. TIR/TAR/TBR ;
2. CV ;
3. AGP ;
4. GMI après décision explicite sur formule/version ;
5. GRI seulement après validation propre.

### Conditions

- contrat population/applicabilité ;
- target range individualisé si nécessaire ;
- evidence registry `GOVERNED_RULE` ;
- aucune candidate rule promue implicitement ;
- UI/LLM distinguent : recorded fractions vs true CGM metrics.

### Succès

Chaque métrique possède : evidence ID, population, modalité, limitations, sufficiency gate, tests et wording patient/clinician.

### Preuve

Golden fixtures + registry tests + API projection + narration test.

---

## ANALYSIS-6 — Contextual targets & population applicability

**Priorité** : P1 avant toute notion “dans la cible” normative  
**Goal** : empêcher l'application aveugle de 70–180 ou d'une population générale à tout patient.

### À faire

- définir source de vérité des targets ;
- brancher les targets de profil quand elles sont gouvernées ;
- distinguer cible utilisateur, cible clinicien, cible standard ;
- ajouter population/applicability gate ;
- fail closed pour grossesse, pédiatrie, populations spéciales non gouvernées ;
- ne jamais produire de conseil thérapeutique à partir d'un dépassement de cible.

### Succès

Aucune phrase normative “dans/hors cible” sans target provenance + applicability valide.

### Preuve

Tests population/target + narration anti-overclaim.

---

## ANALYSIS-7 — Richer personal analytics without fake causality

**Priorité** : P2 après fermeture des P1  
**Goal** : augmenter la valeur analytique personnelle sans transformer association en causalité.

### Candidats sûrs

- paires pré/post-prandiales mieux structurées ;
- réponse répétée par type de repas ;
- détection de données manquantes utile ;
- évolution des patterns dans le temps ;
- comparaison à baseline personnelle ;
- robustness checks : minimum N, distinct days, repeatability ;
- visualisation de l'incertitude ;
- `COLLECT_MISSING_DATA` ;
- `LEARN` ;
- `FOLLOW_UP_RECORD` lorsque leurs autorités existent.

### Interdit dans ce lot

- causalité ;
- recommandation de dose ;
- prescription ;
- optimisation de traitement ;
- prédiction glycémique future non validée ;
- score de “confidence” probabiliste inventé.

### Succès

Les nouvelles observations ajoutent une utilité mesurable sans augmenter les claims cliniques autorisés.

### Preuve

Evals synthétiques + evidence registry + tests anti-causalité + audit humain.

---

## ANALYSIS-8 — Prediction / causal inference research gate

**Priorité** : FUTURE / séparé  
**Goal** : ne réactiver aucune prédiction ou causalité sans validation scientifique dédiée.

### Gate minimum

- protocole défini avant implémentation patient-facing ;
- dataset représentatif et légalement utilisable ;
- calibration prospective ;
- métriques discrimination + calibration + erreurs dangereuses ;
- validation population/modality ;
- gestion abstention/OOD ;
- clinical review ;
- evidence registry ;
- lot sécurité séparé.

### Règle

`prediction.py` doit continuer à retourner `None` et `correlations.py` `[]` jusqu'à clôture explicite de ce gate.

---

# 4. ORDRE D'EXÉCUTION CANONIQUE

Chemin critique :

`ANALYSIS-0 → ANALYSIS-1 → ANALYSIS-2 → ANALYSIS-3 → ANALYSIS-4 → ANALYSIS-5 → ANALYSIS-6 → ANALYSIS-7`

`ANALYSIS-8` reste hors chemin critique et ne doit jamais bloquer l'objectif ≥9/10.

---

# 5. SCORING DE RECERTIFICATION

Le score final doit être recalculé sur preuves, avec au minimum :

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

### Règles du score

- aucune capacité absente ne peut recevoir un score fonctionnel positif ;
- une fonctionnalité volontairement fail-closed peut recevoir un bon score de sécurité mais pas de capacité ;
- aucun “10/10” sans preuve ;
- runtime non testé = non certifié ;
- CI absente/en cours ≠ verte ;
- fallback ≠ preuve provider réelle ;
- documentation seule ≠ comportement runtime.

---

# 6. TEST MATRIX MINIMALE

Avant closeout final :

- entrée glucose : unités + frontières + timestamps ;
- patient isolation ;
- calculs SQL ;
- detector failure ;
- SQL failure ;
- partial analysis ;
- alertes toutes branches ;
- suppression/modification → Clinical Twin reconciliation ;
- CGM incomplete/valid/multi-sensor ;
- evidence-gated TIR/CV/AGP/GMI/GRI ;
- population applicability ;
- targets personnalisées ;
- LLM prompt evidence ceiling ;
- fallback offline ;
- FR / ar-MA / ar / en sur les sorties critiques ;
- aucune causalité/diagnostic/dose inventée ;
- CI complète sur HEAD final.

---

# 7. RÈGLES DE SÉCURITÉ DU CHANTIER

- aucune donnée patient réelle nécessaire ;
- utiliser fixtures synthétiques ;
- aucune prescription, modification de dose ou optimisation thérapeutique ;
- aucune activation de prédiction sans lot de validation séparé ;
- aucune promotion de candidate evidence rule par simple présence dans le code ;
- aucun déploiement Vercel sans autorisation explicite ;
- ne jamais déclarer ≥9/10 tant que la recertification complète n'est pas prouvée.

---

# 8. ÉTAT DE REPRISE

### CLOSED

- audit statique initial du moteur d'analyse ;
- identification du moteur public evidence-gated ;
- baseline forces/gaps ;
- définition de la roadmap ≥9/10.

### OPEN

- ANALYSIS-0 à ANALYSIS-7 ;
- recertification finale.

### NEXT EXACT

**ANALYSIS-0 — Integrity & observability gate** : auditer les types/consommateurs de `DomainContext`, définir le contrat `analysis_status`, écrire les tests de fault injection avant modification runtime.

### Séquence restante

ANALYSIS-0 → tests → closeout lot → ANALYSIS-1 → ANALYSIS-2 → ANALYSIS-3 → ANALYSIS-4 → ANALYSIS-5 → ANALYSIS-6 → ANALYSIS-7 → audit final pondéré → docs/evidence registry coherence → CI final → closeout canonique.

---

# 9. CLOSEOUT FINAL OBLIGATOIRE

Le chantier ne peut être déclaré CLOSED qu'après :

1. tous les lots nécessaires fermés ;
2. tests ciblés + suite pertinente verts ;
3. CI finale verte ;
4. aucune régression clinique connue ;
5. evidence registry cohérent ;
6. ce fichier mis à jour avec HEAD/PR/runs exacts ;
7. score final recalculé et ≥9,0/10 ;
8. vérification post-merge si travail effectué par PR.

---

**FICHIER CANONIQUE : `docs/IAMINA_ANALYSIS_ROADMAP.md`**
