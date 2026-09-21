# IAMINA — External Anonymization Gateway

Status: technical defense-in-depth layer. **Not a legal certification of anonymisation.**

## Goal

Reduce re-identification risk in text that could eventually leave IAMINA for an
external model, without weakening any existing control.

The execution order for network-capable text providers is:

1. governed deterministic context;
2. generative-context sanitizer;
3. PHI pseudonymizer;
4. **External Anonymization Gateway**;
5. final DLP / exact payload authorization;
6. processor policy;
7. FinOps / provider guards;
8. external provider.

Local fallbacks do not pass through this gateway because they perform no external
egress.

## What the gateway does

The implementation is deterministic and creates no reversible lookup table.

It currently:

- removes direct/stable identifiers that survive upstream masking;
- coarsens exact calendar dates and clock times;
- converts exact age to a broad age band;
- withholds exact clinical measurements carrying units;
- removes coordinates and explicitly-labelled locations;
- removes explicit identifier fields;
- re-scans its own output and fails closed if a known high-risk pattern remains.

The returned `AnonymizationResult.certified_anonymous` is intentionally always
`False`. No application code may interpret successful minimization as proof that
the text has become anonymous in the legal sense.

## Why this is not sufficient on its own

Pseudonymisation and anonymisation are different controls. Removing names or
replacing identifiers does not prove that a person can no longer be singled out,
linked across data, or inferred from combinations of remaining attributes.

For that reason, this gateway does **not** remove the existing processor-policy,
consent, DLP, CNDP, contractual, residency, retention or ZDR gates.

Groq remains `PENDING` for patient-data egress. This layer must not be used to
bypass the approval conditions merged in PR #721.

## Validation criteria

A provider-bound payload passes this technical layer only when:

- exact payload shape is `system_prompt` + `user_prompt`;
- known direct/stable identifier patterns are absent after transformation;
- precise date/time, exact age, coordinates and exact unit-bearing clinical values
  are absent after transformation;
- no known residual high-risk pattern survives;
- the result is immutable and deterministic;
- the layer never marks the payload as legally certified anonymous.

## External privacy references

Primary/reference material reviewed for this design:

- CNIL — *L’anonymisation de données personnelles*:
  https://www.cnil.fr/fr/technologies/lanonymisation-de-donnees-personnelles
  (individualisation, corrélation, inférence as effectiveness criteria).
- European Data Protection Board — *Guidelines 02/2026 on Anonymisation*:
  https://www.edpb.europa.eu/public-consultations/guidelines-022026-on-anonymisation_en
  (current 2026 guidance; under public consultation at the time of this design).
- European Data Protection Board — *Anonymisation / pseudonymisation*:
  https://www.edpb.europa.eu/topics/ai-and-technology/anonymisation-pseudonymisation_en
  (distinction between unlinkable anonymised data and pseudonymised personal data).

These references inform the technical threat model; they do not by themselves
establish compliance for IAMINA or authorize international patient-data transfer.
