# Plan d'analyse médicale — Données et guidance prédictive

> Rédigé en consultation avec le Conseiller médical senior (TEAM.md §6) et les directives ADA Standards of Care 2025.
> Date : 2026-04-08

---

## 1. Fréquence d'échantillonnage par type de diabète

| Type de diabète | Cible logging quotidien | Min pour analyse | Min pour estimation GMI/HbA1c |
|-----------------|------------------------|------------------|-------------------------------|
| **Type 1** | 4-6x/jour (chaque repas + à jeun + coucher) | 5 entrées/semaine | **14 jours** (≥70 lectures) |
| **Type 2 (insuline)** | 3-4x/jour (à jeun + post-repas) | 5 entrées/semaine | 14 jours |
| **Type 2 (médicaments oraux)** | 2-3x/jour (à jeun + 1-2 post-repas) | 5 entrées/semaine | 14 jours |
| **Gestationnel** | 4x/jour minimum (à jeun + post chaque repas) — cibles plus strictes (95/140) | 7 entrées/semaine | 10 jours (urgence grossesse) |
| **Prédiabète** | 1-2x/jour (à jeun + post-déjeuner) | 3 entrées/semaine | 21 jours (progression lente) |

---

## 2. Fiabilité de la prédiction GMI/HbA1c

Formule ADA : `GMI (%) = 3.31 + 0.02392 × glycémie_moyenne (mg/dL)`

| Volume de données | Fiabilité GMI | Seuil actuel dans le code | Action recommandée |
|-------------------|--------------|---------------------------|--------------------|
| < 5 entrées | Non calculable | ✅ Déjà bloqué (`if len(values) >= 5`) | Aucune |
| 5-30 entrées | Faible confiance | Affiché sans avertissement | Ajouter badge « Estimation préliminaire » |
| 30-70 entrées (7-14 jours) | Confiance modérée | Affiché sans avertissement | Ajouter badge « Estimation en cours » |
| **70+ entrées (14+ jours)** | **Fiable cliniquement** | Pas de distinction | Ajouter badge « Estimation fiable » |
| 200+ entrées (30+ jours) | Haute confiance — comparable HbA1c labo | Pas de distinction | Badge « Haute confiance » |

**Implémentation :** Ajouter un indicateur de confiance au composant GMI dans `ai_summary.html`, basé sur le nombre de lectures dans la période d'analyse.

---

## 3. Métriques prédictives — au-delà de l'HbA1c

### Données quotidiennes (calculées à chaque visite IAmina)

| Métrique | Ce qu'elle prédit | Données nécessaires | Fréquence de mise à jour |
|----------|-------------------|---------------------|--------------------------|
| **GMI (estimation HbA1c)** | Contrôle glycémique long terme, risque de complications | Glycémie moyenne sur 14+ jours | Hebdomadaire |
| **TIR (Time in Range)** | Qualité du contrôle quotidien, risque hypo/hyper | Toutes les lectures sur 7-21 jours | Quotidien |
| **CV (Coefficient de Variation)** | Instabilité glycémique → risque hypo (CV > 36% = danger) | ≥ 5 entrées | Hebdomadaire |
| **Score phénomène de l'aube** | Résistance à l'insuline matinale → ajustement basale | Lectures à jeun + coucher × 3 jours | Hebdomadaire |
| **Corrélation stress-glycémie** | Impact du stress sur la glycémie pour *ce* patient | Données stress + glycémie × 7 jours | Hebdomadaire |
| **Corrélation sommeil-glycémie** | Impact du sommeil sur la glycémie à jeun | Données sommeil + lectures matinales × 7 jours | Hebdomadaire |
| **Pattern de pics post-repas** | Quels repas causent les pires pics → guidance diététique | Type de repas + glycémie 2h post-repas | En continu |
| **Corrélation fatigue-glycémie** | Fatigue comme signal d'alerte précoce de dérégulation | Données fatigue + glycémie × 7 jours | Hebdomadaire |
| **Impact maladie** | Quantifier comment la maladie élève la glycémie | Données maladie + glycémie × 3 jours malades | Par épisode |
| **Tendance hebdomadaire** | Direction de l'évolution glycémique (amélioration/dégradation) | 2+ semaines de données | Hebdomadaire |

### Données mensuelles (bilan mensuel à implémenter)

| Donnée | Pourquoi | Statut actuel |
|--------|----------|---------------|
| **Poids** | Les variations de poids affectent la sensibilité à l'insuline | Dans le profil, mais jamais re-demandé |
| **Changements de traitement** | Les ajustements de dose affectent toutes les prédictions | Dans le profil, mais statique |
| **HbA1c labo** | Vérité terrain pour calibrer les prédictions GMI | **Non suivi** |
| **Tension artérielle** | Co-facteur de risque cardiovasculaire | **Non suivi** |

**Implémentation recommandée :** Ajouter un prompt mensuel « Bilan du mois » qui demande : mise à jour du poids, changements de traitement, résultats labo récents (HbA1c si disponible). Cela permettrait à IAmina de comparer sa prédiction GMI avec la vraie HbA1c et d'améliorer la précision.

---

## 4. Guidance prédictive par type de diabète

### Type 1
- Optimisation des doses d'insuline (ratio insuline/glucides)
- Détection de l'effet Somogyi (rebond nocturne)
- Risque d'hypoglycémie post-exercice
- Patterns de débit basal (phénomène de l'aube)
- Alerte variabilité glycémique élevée (CV > 36%)

### Type 2
- Suivi d'efficacité des médicaments (tendance glycémique sous traitement)
- Indicateurs de progression (besoin d'ajuster ou ajouter un traitement)
- Classement de sensibilité aux repas (quels repas causent les pires pics)
- Corrélation exercice → amélioration (quantifier le bénéfice)
- Score de contrôle global (combinaison TIR + GMI + CV)

### Gestationnel
- Conformité aux cibles strictes (95/140 mg/dL vs 70/180 standard)
- Tendance hebdomadaire vers le besoin d'insuline
- Alertes précoces de dégradation du contrôle
- Impact du stress et du sommeil (particulièrement important pendant la grossesse)

### Prédiabète
- Score d'impact du mode de vie (exercice + alimentation → tendance glycémique)
- Alerte risque de progression vers le diabète de type 2
- Feedback positif sur les améliorations (encourager le maintien des efforts)
- Corrélation poids → glycémie (si suivi mensuel du poids)

---

## 5. Détecteurs cliniques existants vs à ajouter

### Existants (clinical_engine.py)
1. ✅ Phénomène de l'aube (`detect_dawn_phenomenon`)
2. ✅ Hypoglycémie post-exercice (`detect_post_exercise_hypo`)
3. ✅ Corrélation stress → hyperglycémie (`detect_stress_correlation`)
4. ✅ Impact du sommeil (`detect_sleep_impact`)
5. ✅ Variabilité glycémique élevée (`detect_high_variability`)
6. ✅ Sensibilité alimentaire (`detect_food_sensitivity`)
7. ✅ Effet Somogyi (`detect_somogyi_rebound`)

### À ajouter (avec les nouveaux champs fatigue_level et is_sick)
8. 🔲 `detect_fatigue_correlation` — Fatigue comme marqueur de dérégulation glycémique
9. 🔲 `detect_illness_impact` — Quantifier l'hyperglycémie induite par la maladie
10. 🔲 `detect_weekly_trend` — Tendance d'amélioration ou dégradation sur 2+ semaines
11. 🔲 `detect_meal_type_ranking` — Classement des types de repas par pic glycémique moyen

### À ajouter (bilan mensuel, post-POC)
12. 🔲 `detect_weight_impact` — Corrélation poids → sensibilité à l'insuline
13. 🔲 `compare_gmi_vs_lab` — Calibrer GMI avec HbA1c labo réelle
14. 🔲 `detect_treatment_response` — Évaluer l'efficacité après changement de traitement

---

## 6. Facteurs affectant la glycémie — référence complète

Basé sur les directives ADA 2025 et le Conseiller médical senior (TEAM.md §6).

### Facteurs quotidiens (trackés par l'app)
| Facteur | Mécanisme | Impact typique | Suivi actuel |
|---------|-----------|----------------|--------------|
| **Alimentation** | Apport glucidique → pic glycémique | +30-100 mg/dL post-repas | ✅ meal_type, meal_description |
| **Exercice** | Sensibilité insuline ↑ → glycémie ↓ | -20-50 mg/dL pendant 24h | ✅ exercised |
| **Sommeil** | Mauvais sommeil → résistance insuline ↑ | +15-30 mg/dL à jeun | ✅ sleep_quality |
| **Stress** | Cortisol → production glucose hépatique ↑ | +20-50 mg/dL | ✅ stressed |
| **Fatigue** | Marqueur de dérégulation, corrélé au sommeil | Variable | ✅ fatigue_level (nouveau) |
| **Maladie** | Hormones de stress → glucose ↑↑ | +50-150 mg/dL | ✅ is_sick (nouveau) |
| **Insuline** | Régulation directe de la glycémie | Variable selon dose | ✅ insulin_units |

### Facteurs mensuels (à implémenter)
| Facteur | Mécanisme | Impact | Suivi actuel |
|---------|-----------|--------|--------------|
| **Poids** | Prise de poids → résistance insuline ↑ | Long terme | 🔲 Bilan mensuel |
| **Traitement** | Changements de médicaments/doses | Majeur | 🔲 Bilan mensuel |
| **HbA1c labo** | Vérité terrain du contrôle 3 mois | Référence | 🔲 Bilan mensuel |

### Facteurs non trackés (hors scope POC)
- Hydratation (difficile à quantifier en binaire)
- Alcool (sujet sensible, hors directives du conseiller médical)
- Cycle menstruel (impact sur la résistance à l'insuline)
- Médicaments concomitants (corticoïdes, etc.)
- Température ambiante (impact mineur)

---

## 7. Prochaines étapes d'implémentation

> **Note :** ces jalons cliniques **M0/M1/M2** sont propres au contenu médical (détecteurs,
> métriques) et **n'ont aucun rapport avec les phases plateforme P0–P8 / Phases 18–26** de
> `docs/ROADMAP.md`. C'est une backlog clinique, pas un tracker de phases.

### M0 — Court terme (pendant le POC)
1. Implémenter les détecteurs `detect_fatigue_correlation` et `detect_illness_impact`
2. ~~Ajouter un badge de confiance au composant GMI~~ ✅ FAIT (tiers high/medium/low + badges Flutter)
3. Adapter les seuils d'analyse par type de diabète

### M1 — Moyen terme (fin du POC)
4. Implémenter `detect_weekly_trend` et `detect_meal_type_ranking`
5. Créer le flux « Bilan mensuel » (poids, traitement, HbA1c labo)
6. Personnaliser les recommandations IAmina par type de diabète

### M2 — Post-POC
7. Implémenter les détecteurs mensuels (poids, traitement, calibration GMI)
8. Ajouter des graphiques de tendance (évolution TIR, GMI sur plusieurs semaines)
9. Système de notifications/alertes pour les patterns critiques
