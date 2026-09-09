# IAMINA — ANALYSE CLINIQUE ≥9/10 — FICHIER CANONIQUE

> **Statut** : CLOSED ✅  
> **Date de recertification** : 2026-09-09  
> **Repo** : `hraaaaf/IAMINA-MVP`  
> **Base certifiée finale** : `main@b0b9aa773049c02c2f161febb1d6983b5d4645cc`  
> **Baseline initiale** : ~7,9/10 statique, non-runtime  
> **Score pondéré final** : **9,46/10**  
> **Déploiement Vercel** : aucun déploiement effectué  
> **Données patient** : fixtures synthétiques uniquement

---

## 1. GOAL FINAL — ATTEINT ✅

Faire passer le moteur d’analyse IAMINA à **≥9,0/10 réellement certifié**, sans sacrifier sécurité clinique, incertitude, traçabilité, isolation patient ou architecture capsule.

### Succès observable

Le Goal est atteint et clos :

1. contrats d’entrée cohérents et fail-closed ;
2. états explicites `complete | partial | unavailable | insufficient_data` ;
3. autorité evidence-gated unique pour les sorties normatives ;
4. alertes publiques déterministes et testées ;
5. aucune cible normative sans provenance/applicabilité ;
6. métriques CGM promues uniquement après preuve de suffisance ;
7. cadence/couverture/fenêtre CGM persistées et vérifiées ;
8. longitudinal descriptif sans causalité/prédiction fictive ;
9. paires repas pré→post uniquement par épisode explicitement lié ;
10. suites SQLite/PostgreSQL + contrôles architecture/sécurité/OpenAPI verts sur le merge A7 ;
11. recertification pondérée finale à **9,46/10** ;
12. PR de closeout #545 mergée et CI post-merge #34330851746 **SUCCESS**.

---

## 2. LOTS CERTIFIÉS

| Lot | Statut | Preuve principale |
|---|---|---|
| A0 — Integrity & observability | ✅ CLOSED | PR #537 ; merge `ec18c9b` ; post-merge CI #34207685998 ; drift #34207685984 |
| A1 — Canonical input contract | ✅ CLOSED | PR #538 ; merge `4bc8c70` ; CI #34212026116 ; drift #34212026120 |
| A2 — Alerting correctness | ✅ CLOSED | PR #539 ; merge `f3da008` ; CI #34232357895 ; drift #34232357898 |
| A3 — Single evidence authority | ✅ CLOSED | PR #540 ; merge `4318814` ; CI #34237020000 ; drift #34237020046 |
| A4 — Real CGM sufficiency | ✅ CLOSED | PR #541 ; merge `71a8b86` ; CI #34247637204 ; drift #34247637242 |
| A5 — Governed CGM promotion | ✅ CLOSED | PR #542 ; merge `9681b77` ; CI #34272156304 ; drift #34272156421 |
| A6 — Contextual targets | ✅ CLOSED | PR #543 ; merge `c829eb7` ; CI #34279210367 ; drift #34279210339 |
| A7 — Explicit paired meal response | ✅ CLOSED | PR #544 ; merge `e7b4502` ; pre-merge CI #34291940119 + drift #34291940184 ; post-merge CI #34330374819 + drift #34330374844 |
| Final recertification closeout | ✅ CLOSED | PR #545 ; merge `b0b9aa7` ; pre-merge CI #34330776155 ; post-merge CI #34330851746 |

### A7 final

A7 ajoute `meal_episode_id` explicite, unicité d’un rôle pré/post par patient+épisode, validation canonique, savepoints create/batch, calcul pré/post/delta uniquement sur UUID partagé et même type de repas, exclusion demo/futur et endpoint patient-scoped. Aucun appariement temporel implicite, aucune causalité, aucune prédiction, aucun seuil thérapeutique inventé.

Le dernier défaut trouvé par CI avant merge était transactionnel : un conflit d’unicité retournait bien le conflit attendu mais cassait la transaction Django. Il a été corrigé par savepoint explicite puis recertifié sur SQLite et PostgreSQL.

---

## 3. RECERTIFICATION PONDÉRÉE

| Axe | Poids | Score /10 | Contribution | Preuve / limite |
|---|---:|---:|---:|---|
| Sécurité clinique / epistemic safety | 20% | **9,7** | 1,940 | fail-closed, pas de diagnostic/dose/causalité/prédiction, cibles gouvernées |
| Qualité & exactitude analytique | 15% | **9,2** | 1,380 | SQL déterministe, CGM natif, paires repas exactes ; pas de stats causales avancées |
| Evidence / provenance / applicability | 15% | **9,7** | 1,455 | autorité unique, provenance cible, population gate, candidate rules fermées |
| Intégrité des entrées | 10% | **9,7** | 0,970 | contrat canonique, unités/bornes/timestamps, UUID épisode, contraintes DB |
| Fiabilité / dégradation / observabilité | 10% | **9,4** | 0,940 | états explicites, dégradations partielles, transactions isolées |
| CGM sufficiency & analytics | 10% | **9,3** | 0,930 | sessions/cadence/couverture + TIR/TAR/TBR/CV gouvernés ; Nightscout reste fail-closed sans session |
| Longitudinal / Clinical Twin | 8% | **9,2** | 0,736 | baseline, récidive, résolution, change-since-review + paires repas explicites |
| Proactive intelligence | 5% | **8,4** | 0,420 | change-since-review déterministe et priorisation existante ; pas de prédiction |
| LLM boundary | 4% | **9,8** | 0,392 | gateway + egress anti-bypass verts, legacy summary neutralisé |
| Tests / CI / runtime proof | 3% | **9,8** | 0,294 | suites SQLite/PostgreSQL, drift, Ruff, import-linter, Bandit, OpenAPI |
| **TOTAL** | **100%** |  | **9,457 ≈ 9,46/10** | |

### Interprétation

**Score certifié : 9,46/10.** Le seuil ≥9 est dépassé sans crédit artificiel pour des capacités absentes.

Ce qui empêche une note proche de 10 :
- pas de causalité ni prédiction clinique, volontairement ;
- pas de multivarié/statistique probabiliste avancé ;
- GMI/GRI restent candidates/non promues ;
- Nightscout actuel ne fournit pas le contrat de session suffisant pour promotion CGM ;
- proactive intelligence reste déterministe et prudente plutôt que prédictive.

---

## 4. CAPACITÉS RÉELLEMENT CERTIFIÉES

IAMINA sait désormais :
- analyser descriptivement les glycémies et leur évolution ;
- distinguer analyse complète, partielle, indisponible et données insuffisantes ;
- produire des alertes déterministes gouvernées ;
- maintenir un Clinical Twin longitudinal avec baseline personnelle, récidive, persistance, amélioration/résolution et comparaison depuis revue explicite ;
- certifier une fenêtre CGM par sessions, cadence, couverture et durée ;
- exposer TIR/TAR/TBR/CV seulement derrière le contrat CGM gouverné ;
- interpréter une cible uniquement avec provenance, population et confirmation valides ;
- calculer une réponse repas pré→post uniquement lorsque l’épisode est explicitement partagé ;
- rester neutre/fail-closed lorsqu’une preuve requise manque.

IAMINA ne prétend toujours pas :
- diagnostiquer ;
- inférer qu’un aliment, stress, sommeil ou activité **cause** une variation ;
- prédire une glycémie future ;
- recommander/modifier une dose ou un traitement ;
- fournir une confiance probabiliste clinique ;
- promouvoir GMI/GRI sans gouvernance dédiée.

---

## 5. ANALYSIS-8 — RESEARCH GATE

**FUTURE / hors chemin critique.**

`prediction.py` et toute corrélation causale doivent rester fail-closed/désactivés tant qu’un protocole scientifique, une validation clinique et une gouvernance dédiée ne sont pas certifiés.

A8 n’est pas nécessaire pour le Goal ≥9, car l’absence volontaire de prédiction est comptée comme limite fonctionnelle et comme force de sécurité, jamais comme capacité présente.

---

## 6. CLOSEOUT FINAL — CLOSED ✅

### Preuve A7 post-merge
- `main@e7b450214e9b375e77bb517bbffb9653dcb60d4f`
- CI push #34330374819 : **SUCCESS**
- drift #34330374844 : **SUCCESS**

### Preuve recertification / closeout
- PR #545 : mergée
- merge closeout : `main@b0b9aa773049c02c2f161febb1d6983b5d4645cc`
- CI pré-merge #34330776155 : **SUCCESS**
- CI post-merge #34330851746 : **SUCCESS**
- scope docs-only : backend/frontend correctement skipped sur le commit documentaire final

### Next exact

Aucune action restante dans ce chantier. Toute amélioration future relève d’un nouveau lot, notamment A8 research gate si un protocole scientifique dédié est lancé.

---

**FICHIER CANONIQUE : `docs/IAMINA_ANALYSIS_ROADMAP.md`**
