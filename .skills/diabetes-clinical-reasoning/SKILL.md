# Skill — Diabetes Clinical Reasoning

## Purpose
Apply diabetologist-grade reasoning discipline to diabetes data, approved deterministic observations and patient questions without turning IAmina into a diagnostic or prescribing system.

This skill is mandatory for LOTs that change diabetes clinical reasoning, interpretation, clinician-facing synthesis, patient-facing explanation of diabetes observations, or the semantic meaning of diabetes analytics.

## Authority order
1. Repository canonical safety/product contracts (`AGENTS.md`, `docs/MEDICAL_DATA_PLAN.md`, current ADRs/specs).
2. Deterministic emergency, normalization, eligibility and domain logic.
3. Versioned evidence accepted through `.skills/diabetes-evidence-intelligence/SKILL.md`.
4. Observed/patient-entered facts and deterministic derivations with provenance.
5. Generative narration of already-approved structured output.

A model, prompt, paper, guideline sentence or this skill may never override a deterministic safety gate or promote inference into patient fact.

## Clinical competency map
Reason explicitly across the relevant domains rather than reducing diabetes to glucose alone:

- diabetes classification and diagnostic context, while never diagnosing from incomplete app data;
- A1C, BGM and CGM metrics, including TIR/TAR/TBR, GMI, mean glucose, variability and data-coverage eligibility;
- hypoglycemia, hyperglycemia and hyperglycemic-crisis safety context;
- insulin, non-insulin glucose-lowering medicines and glucagon as treatment context only, never autonomous prescribing/dose optimization;
- CGM, pumps, connected pens and automated insulin delivery, including device limitations and data quality;
- cardiovascular risk, blood pressure, lipids, heart failure and ASCVD context;
- kidney function, eGFR, albuminuria and diabetes/CKD context;
- retinopathy, neuropathy, foot risk and other diabetes complications;
- obesity, nutrition, activity, sleep and smoking/substance exposure when explicitly known;
- pregnancy and preconception context;
- children, adolescents and young adults using population-specific evidence;
- older adults, frailty, cognition, function and caregiver context;
- psychosocial burden, diabetes distress, fear of hypoglycemia, adherence and access barriers;
- intercurrent illness, travel, heat, shift work and other explicitly observed context;
- religious fasting/Ramadan using current fasting-specific evidence and jurisdiction/cultural context;
- screening, prevention, remission terminology and disease-progression context;
- atypical/secondary diabetes forms only when supported by confirmed patient facts or clinician-provided information.

## Required reasoning sequence
For every clinical interpretation:

1. **Inventory provenance.** Separate observed data, explicit patient claims, deterministic derivations, clinician-entered facts, preferences and model inference.
2. **Check applicability.** Confirm the evidence population fits known age group, pregnancy status, diabetes type/context, treatment context, comorbidity context, modality and jurisdiction. Unknown stays unknown.
3. **Check eligibility.** Validate units, time window, data density/coverage, sensor modality, temporal alignment and missingness before applying any threshold or reference range.
4. **Describe before explaining.** State the evidence-qualified observation first. Do not jump from temporal association to mechanism or cause.
5. **Separate explanations from facts.** Possible explanations must be labeled as possibilities and must not be persisted as patient truth.
6. **Assess clinical relevance only within evidence.** Use current accepted sources and individualized context; never copy a population target into a personalized command.
7. **Choose an allowed action class.** Education, monitor, collect missing data, prepare a clinician discussion, clinician handoff, or deterministic emergency routing. No diagnosis, prescription, dose calculation or treatment optimization.
8. **Expose uncertainty.** State what is known, what is missing, confidence/evidence density and why the conclusion is bounded.

## Structured reasoning contract
When creating or changing an insight schema, preserve these concepts even if field names differ:

- `observation`
- `provenance`
- `evidence_window`
- `evidence_density`
- `population_applicability`
- `possible_explanations`
- `missing_data`
- `limitations`
- `confidence_or_maturity`
- `allowed_next_step`
- `escalation_class`
- `source_version`

Do not invent a numeric confidence score unless it is validated, calibrated and defined by a governed rule.

## Hard stops
Block the LOT if any reachable behavior:

- diagnoses a condition or complication from insufficient app data;
- recommends starting, stopping, switching or titrating medication;
- calculates or optimizes an insulin/medication dose;
- treats GMI as identical to laboratory A1C;
- applies adult targets to pregnancy, pediatrics, older/frail adults or another special population without applicability checks;
- interprets sparse/manual data as validated CGM assessment;
- turns one temporal association into causality;
- treats sensor artifact or insufficient coverage as a clinical trend;
- fabricates age, pregnancy, renal function, treatment, symptoms, adherence or any other missing patient fact;
- presents investigational evidence as current standard of care.

## Evidence dependency
Load `.skills/diabetes-evidence-intelligence/SKILL.md` for any clinical rule, threshold, guideline statement, treatment-context claim, technology claim or research-horizon claim. Core source status is indexed in `.skills/diabetes-evidence-intelligence/CORE_SOURCES.md`.
