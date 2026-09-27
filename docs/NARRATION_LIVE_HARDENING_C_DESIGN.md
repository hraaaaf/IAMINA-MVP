# IAMINA — Narration Live Hardening C — Design

Base conceptuelle : Hardening A + B.

## Goal

Garantir qu'aucune limitation clinique obligatoire ne puisse être omise, reformulée, affaiblie ou traduite librement par le LLM.

## Décision d'architecture

Les `AdviceDecision.limitations` restent des identifiants de gouvernance internes.

Le LLM :
- ne traduit pas ces identifiants ;
- ne décide pas lesquels montrer ;
- ne paraphrase pas les limitations obligatoires ;
- ne peut pas supprimer une limitation.

Le rendu patient des limitations obligatoires est produit **localement et déterministiquement** par la capsule clinique.

## Pipeline cible

`AdviceDecision`
→ classification locale des limitations patient-visibles
→ lookup déterministe `limitation_id + locale → patient clause`
→ `NarrationEnvelope` provider view sans texte clinique exact
→ LLM = enveloppe linguistique uniquement
→ fact token verification
→ local fact reinjection
→ local mandatory-clause composition
→ family semantic verifier
→ output/safety/dialect guards
→ réponse patient.

## Fail-closed

Une narration live doit retomber sur `fallback_reply` si :
- une limitation marquée patient-visible n'a pas de mapping local ;
- la locale demandée n'a pas de rendu certifié ;
- un mapping retourne une chaîne vide ;
- deux limitations se contredisent ;
- le family verifier rejette le résultat final ;
- une limitation obligatoire disparaît après composition.

Aucun fallback LLM secondaire.

## Séparation des limitations

Toutes les limitations ne doivent pas automatiquement être montrées au patient.

Deux classes doivent être explicites :

1. `INTERNAL_GUARDRAIL`
   - gouverne le moteur/verifier ;
   - jamais exposée telle quelle au patient.

2. `PATIENT_REQUIRED`
   - doit être présente dans la réponse finale ;
   - rendu local déterministe obligatoire.

La classification appartient à la capsule/rule family, pas au châssis générique.

## Première intégration recommandée

Commencer avec une seule rule family à sémantique fermée :
`CLINICIAN_PREP` ou `MONITORING_INTERPRETATION`.

Ne pas activer plusieurs familles simultanément.

### Monitoring examples

IDs existants :
- `descriptive_monitoring_only`
- `recorded_readings_are_not_automatically_validated_cgm_time_metrics`
- `no_diagnosis_or_treatment_change`

Les formulations patient doivent être des copies locales certifiées FR/EN/ar-MA/ar-* et non des traductions runtime.

### Clinician prep examples

IDs existants :
- `consultation_brief_structured_fields_only`
- `clinician_remains_medical_decision_authority`
- `no_diagnosis_causality_dose_or_treatment_change`

## Invariants de test

- missing patient-required mapping → fallback déterministe ;
- locale manquante → fallback ;
- internal-only limitation non exposée ;
- patient-required limitation toujours présente exactement une fois ;
- LLM candidate sans limitation → clause ajoutée localement ;
- LLM candidate tentant de contredire la limitation → family verifier rejette ;
- ordre stable des clauses ;
- aucun ID interne brut dans la réponse patient ;
- aucune nouvelle donnée clinique ou action patient.

## Hors scope

- activation live ;
- changement de règle clinique ;
- nouveau provider ;
- UI/DB/Vercel ;
- certification réglementaire.

## Gate de sortie

Hardening C n'est clos que si :
- catalog local versionné ;
- classification patient-visible/internal explicitement testée ;
- composition locale obligatoire testée ;
- family verifier final testé après composition ;
- exact-head CI + post-merge verts.
