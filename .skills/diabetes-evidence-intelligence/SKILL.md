# Skill — Diabetes Evidence Intelligence

## Purpose
Keep IAmina's diabetes knowledge current, source-traceable and explicitly separated by evidence maturity so that new papers, guidelines, products or draft recommendations cannot silently become patient authority.

This skill is mandatory for LOTs that add or change a diabetes threshold, clinical rule, population target, treatment-context statement, device/technology claim, research-horizon claim, Ramadan/fasting rule, clinician-summary knowledge or evidence registry.

## Evidence classes
Every externally sourced clinical claim must be placed in exactly one class:

### `STANDARD_OF_CARE`
A current final guideline, regulator-approved indication/safety requirement, or repository-accepted normative consensus appropriate to the population/jurisdiction.

### `EMERGING_EVIDENCE`
Peer-reviewed evidence or a draft/updated consensus that may inform research, review or clinician discussion but has not crossed IAmina's promotion gate into patient rule authority.

### `INVESTIGATIONAL`
Preprints, early trials, exploratory biomarkers/models, unapproved indications/devices or future-facing hypotheses. These may be tracked by horizon-scanning work only.

A newer publication date alone does not promote evidence maturity.

## Source hierarchy
Prefer, in order appropriate to the question:

1. Current final clinical-practice guidelines and consensus from authoritative professional bodies (for example ADA, ISPAD, KDIGO, IDF/DaR).
2. Regulators and official product labeling for approved indications, contraindications, warnings and jurisdictional availability.
3. High-quality systematic reviews/meta-analyses and pivotal peer-reviewed randomized or prospective studies.
4. Peer-reviewed observational/real-world evidence with explicit limitations.
5. Official device/manufacturer documentation for device behavior and compatibility, never as an independent clinical-effectiveness authority.
6. Preprints/conference material only as `INVESTIGATIONAL` unless independently promoted through the governed evidence process.

Marketing pages, unsourced summaries and generic web content are not normative clinical sources.

## Mandatory freshness procedure
Before changing a clinical claim that could have changed:

1. Verify the current source online; do not rely on model memory.
2. Record publication/version date and whether the source is final, corrected, updated, draft or superseded.
3. Check for errata/corrections when the rule contains a numeric threshold or score.
4. Confirm the population: diabetes type, age, pregnancy, CKD/comorbidity context, treatment/device context and care setting.
5. Confirm jurisdiction/regulatory scope where applicable.
6. Compare against the repository's current rule and identify whether the proposed change is additive, superseding or only horizon evidence.
7. Require clinical-safety review and regression evidence before a patient-facing rule changes.

If source status is uncertain, fail closed to the less authoritative evidence class.

## Evidence record contract
A governed evidence item should be able to express:

- `topic`
- `claim_or_rule`
- `evidence_class`
- `source_organization`
- `source_title`
- `identifier` (DOI/PMID/guideline/version when available)
- `publication_or_version_date`
- `finality_status`
- `population`
- `modality_or_device_context`
- `jurisdiction`
- `evidence_grade_or_strength` when the source provides one
- `reviewed_at`
- `supersedes`
- `superseded_by`
- `clinical_authority` (`none`, `narrative_only`, `governed_rule_candidate`, `governed_rule`)
- `limitations`

## Promotion gate
No paper, guideline update or horizon item may directly change a patient-facing deterministic rule merely because it is newer.

Promotion to a governed rule requires:

1. source/finality verification;
2. population and jurisdiction applicability;
3. explicit mapping to the existing rule/contract;
4. Clinical Safety Reviewer approval;
5. positive and negative regression cases including insufficient-data behavior;
6. exact-head repository gates;
7. canonical documentation update when the durable contract changes.

Draft guidance remains non-authoritative until final unless a human owner and clinical-safety process explicitly adopts a narrowly justified interim rule that repository policy permits.

## Special handling — fast-moving areas
Apply extra freshness scrutiny to:

- CGM/AID/device capabilities and availability;
- pharmacotherapy indications and safety labeling;
- cardiovascular and kidney outcome evidence;
- obesity/incretin therapies;
- type 1 diabetes disease-modifying therapies;
- pregnancy technology/therapy evidence;
- pediatric technology/therapy evidence;
- religious fasting/Ramadan risk assessment;
- AI/ML glucose prediction and decision support.

## Research-horizon rule
For emerging/investigational items, explicitly state:

- what the study actually showed;
- design/population and major limitation;
- whether findings are replicated;
- regulatory/guideline status;
- what would be required before IAmina could use it clinically.

Do not translate statistical prediction into a patient-specific clinical forecast without a separately validated model and release gate.

## Current core source index
Use `.skills/diabetes-evidence-intelligence/CORE_SOURCES.md` as the starting source map. It is not a substitute for freshness verification; its dates/status must be rechecked when a LOT depends on them.

## Hard stops
Block the LOT if it:

- presents a draft guideline as final;
- uses a superseded or corrected numeric rule without checking the update;
- copies an adult target into a special population without applicability checks;
- treats device marketing as clinical validation;
- treats a preprint as standard of care;
- lets a research-horizon item silently change deterministic patient behavior;
- omits provenance/version from a new governed clinical rule;
- claims jurisdictional approval or availability without an authoritative current source.
