# P3-HORIZON — Evidence Horizon Scanner Contract

Status: CERTIFIED / CLOSED

## Objective

Discover and classify external diabetes evidence that may deserve human review while keeping discovery strictly separate from the release-governed evidence registry and all patient-facing runtime behavior.

## Existing authority boundary

The current `evidence_registry.py` remains the only code-first registry that can authorize evidence used by governed runtime rules. Existing `evidence_engine.py` and `evidence_projection.py` remain unchanged by horizon discovery.

## Scanner authority

The horizon scanner may:

- discover candidate publications or guidance updates;
- record source identity, publication/version date, finality, population, modality, jurisdiction and retrieval provenance;
- classify a candidate for review as standard-of-care, emerging evidence or investigational;
- detect possible supersession or topic overlap;
- emit a review queue and deterministic diff against known source identifiers.

The scanner may not:

- edit `evidence_registry.py` automatically;
- create or upgrade runtime clinical authority;
- change a governed rule, threshold, formula, patient KPI, pattern, suggestion or emergency behavior;
- treat a preprint, draft, press release, abstract-only record or search snippet as final evidence;
- infer applicability to a patient from publication metadata alone;
- silently replace an existing source because a newer publication exists.

## Candidate record minimum fields

Every candidate must preserve at least:

- stable candidate fingerprint;
- topic;
- source organization;
- source title;
- canonical identifier when available;
- publication/version date;
- finality status;
- proposed evidence maturity;
- population;
- modality;
- jurisdiction;
- regulatory status when relevant;
- retrieval timestamp;
- source URL or canonical locator;
- limitations / missing verification data;
- relationship to any known registry evidence ID.

## Fail-closed rules

- Missing canonical source identity => candidate remains unverified.
- Unknown finality => candidate cannot be proposed as final guidance.
- Conflicting versions => preserve both and require review.
- Newer date alone never means supersession.
- Candidate maturity never grants runtime authority.
- Network/search failure produces an incomplete scan state, never an empty "no updates" conclusion.

## Promotion gate

Promotion is a separate reviewed repository change. A promoted item must receive a stable evidence ID in `evidence_registry.py`, explicit maturity/finality/applicability metadata and normal CI/review certification. Any governed-rule change remains a separate promotion decision even when supported by a newly admitted source.

## Initial implementation sequence

1. P3-HORIZON-0 — contract + deterministic candidate schema.
2. P3-HORIZON-1 — read-only scanner adapters and normalized candidate output.
3. P3-HORIZON-2 — known-registry comparison, supersession hints and review queue.
4. P3-HORIZON-3 — source verification and failure-state certification.
5. Closeout before P3-EVALS.

## Certified implementation

- H0 candidate contract/schema: merge `098f87dc…`; post-merge CI #1988 + drift #1800 green.
- H1 read-only complete/incomplete scan semantics: merge `074dc414…`; post-merge CI #1990 + drift #1802 green.
- H2 source-only comparison and review hints: merge `9c54e3cf…`; post-merge CI #2002 + drift #1814 green.
- H3 fail-closed verification state: merge `100445b2…`; post-merge CI #2007 + drift #1819 green.

No horizon component mutates the governed registry, promotes a candidate or changes runtime authority. Promotion remains a separate reviewed repository change.

## Next

P3-EVALS — Companion Intelligence Evals.
