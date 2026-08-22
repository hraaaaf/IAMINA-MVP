# Canonical Clinical Data Layer & PHI Boundary

Status: implementation candidate, pending exact-head CI and release certification.

## Goal

Normalize every clinical input into one disease-neutral internal fact contract while
keeping patient identity inside IAMINA's privacy boundary.

Target flow:

`raw input -> source adapter -> CanonicalClinicalFact -> validation/review -> capsule -> patient DB`

External AI/OCR is a separate egress boundary and must never be treated as a
persistence layer.

## CanonicalClinicalFact

The chassis contract lives in `core.contracts.clinical_fact` and carries:

- internal patient subject reference;
- normalized concept and value;
- normalized unit plus an optional proven coding system;
- clinically effective time;
- source type and source reference;
- optional terminology codings;
- confidence and review decision;
- immutable attributes;
- provenance.

The shape is intentionally smaller than FHIR. It is designed to map cleanly to
FHIR Observation concepts (`code`, `subject`, `effective[x]`, `value[x]`) and may
carry LOINC or UCUM identifiers only when the adapter has enough semantics to
justify them.

No adapter may invent a LOINC code when specimen/method semantics are not known.
An arbitrary unit string must never be labelled UCUM automatically.

A canonical fact uses the most conservative review decision among the source
fields actually promoted into that fact. A rejected supporting field is omitted;
a used `review_required` timestamp/context/attribute keeps the resulting fact in
`review_required` rather than silently upgrading it to `accepted`.

## Existing diabetes adapters

`diabetes.services.canonical_facts` maps the current source families without
changing their clinical values:

- manual / voice / historical import `LogEntry`;
- normalized live `CGMReadingRecord`;
- neutral Pulper `DocumentExtraction`.

Pulper provenance is carried through source hash/reference, extractor/version,
schema version, extractor/parser model, prompt version and evidence-verification
state when present.

These adapters are a compatibility layer. They do not yet replace the existing
persistence models.

## PHI boundary

Internal clinical data remains patient-linked. The egress path is different:

1. known identity values are redacted from the current patient context;
2. generic identifiers such as CIN, email and Moroccan phone numbers are masked;
3. the centralized `core.ai_egress` text-payload boundary independently resolves
   the scoped patient's identity and rejects a final payload if a known direct
   identifier still survives.

The central last-mile check covers bare names/usernames/date-of-birth values even
when they are not preceded by labels such as `Nom:`. It therefore does not rely
on every caller remembering to instantiate or calibrate `PHIPseudonymizer`.

This closes the Pulper failure mode where `PHIPseudonymizer.mask()` was called
without an explicit `calibrate()` while preserving the existing generic DLP as a
second independent deny layer.

## Image OCR rule

A patient medical-document image can contain direct identity before OCR. Text
redaction after a cloud OCR call is therefore too late.

Until IAMINA has a qualified local de-identification/OCR lane, patient
`document_ingest` images must fail closed instead of sending raw image bytes to a
cloud OCR provider.

## Acceptance evidence

This lot is creditable only when exact-head evidence proves:

- canonical contract invariants;
- manual/import/CGM/document adapter equivalence where semantics match;
- review-required supporting metadata cannot be silently promoted to accepted;
- unknown units are not falsely labelled UCUM and LOINC is not invented;
- patient name, date of birth, email, CIN and phone do not survive text masking;
- the central text-egress boundary rejects surviving current-patient identity;
- clinical values survive masking;
- patient document images cannot select raw cloud OCR;
- existing Pulper, OCR routing, egress and pseudonymizer regressions remain green;
- architecture/import, anti-bypass, SAST, PostgreSQL and migration-drift gates pass.
