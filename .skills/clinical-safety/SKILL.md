# Skill — Clinical Safety Review

## Purpose
Review changes that can alter patient-facing medical meaning, clinical calculations, safety handling or claims.

## Required checks
- Identify the normative source/contract for any clinical rule touched.
- Confirm deterministic safety logic remains authoritative and upstream of generative output.
- Confirm no diagnosis, prescription, dose calculation or treatment optimization is introduced.
- Verify units, eligibility thresholds, insufficient-data behavior and uncertainty/limitations.
- Test positive and negative guardrail cases.
- Confirm patient-facing wording does not overstate precision, causality, validation or availability.
- For locale/safety changes, require parity evidence appropriate to the enabled locale; native human review remains mandatory where the roadmap requires it.

## Blockers
Any fabricated patient fact, unsafe fail-open path, unreferenced clinical threshold presented as authoritative, hidden uncertainty, or generative model becoming the decision authority.