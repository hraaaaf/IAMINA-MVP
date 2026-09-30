# IAMINA — Groq E1–E5 Evidence Acquisition Runbook

Status: **READY FOR HUMAN/EXTERNAL EXECUTION — NO APPROVAL CLAIMED**

Verified: 2026-09-30

Purpose: convert the remaining Groq patient-data governance blockers into one
observable evidence checklist. This document is operational preparation, not legal
advice and not proof that any authorization or contract has been obtained.

## Current invariant

Do not:
- change `groq` from `PENDING`;
- send patient data to Groq;
- enable production provider traffic;
- treat public policy pages as IAMINA-specific approval evidence;
- store signed contracts, CNDP private correspondence, credentials or private audit
  material in source control.

Restricted evidence belongs in the approved private compliance repository. Git may
record only an opaque reference, status, accountable role and review dates.

## E1 — CNDP health-data processing authorization

### Official baseline

CNDP's current procedures page lists health-data processing under prior
authorization and publishes a health-processing route using form F-113 under
decision D-941-2025 for patient-monitoring treatments. The same page requires,
among other items, the consent/legal-basis collection document, patient
information notice, processor contract/confidentiality clauses where applicable,
and proof of signatory authority.

A separate CNDP authorization page also requires health-processing dossiers to
identify the persons responsible for processing and includes additional
health-data documentation requirements.

Official references:
- https://www.cndp.ma/procedures-de-notification-process/
- https://www.cndp.ma/notifier-une-demande-dautorisation-prealable/
- https://www.cndp.ma/notifier-un-traitement/

### IAMINA evidence required

PASS only when the private compliance repository contains an IAMINA-specific
CNDP receipt/authorization reference for the actual health-data processing and
the reviewer has confirmed that the filed route/form is applicable to the actual
IAMINA pilot.

Git evidence row:
- opaque authorization/receipt reference;
- controller legal entity reference;
- reviewed_on;
- review_due_on;
- reviewer role.

Do not mark PASS from a blank/form template, submission draft or generic CNDP page.

## E2 — CNDP foreign-transfer authorization / approved basis

### Official baseline

CNDP states that a foreign-transfer request uses F118 and that transfer
authorization is granted only after the underlying processing request has been
approved. The transfer dossier can require proof of signatory authority,
consent/information evidence, the underlying CNDP receipt/authorization and
contractual clauses.

Official reference:
- https://www.cndp.ma/transfert-de-donnees-a-letranger/

### IAMINA evidence required

PASS only with an IAMINA-specific F118/transfer authorization reference or a
documented alternative transfer basis that has been reviewed as applicable to
the exact IAMINA → Groq/U.S. flow.

Record:
- destination/country;
- processor;
- opaque authorization/basis reference;
- underlying E1 reference;
- reviewed_on;
- review_due_on;
- reviewer role.

Do not infer approval from Groq SCC language alone.

## E3 — IAMINA data-controller identity and signatory authority

### Current finding

Repo, Notion, Gmail and Drive searches performed on 2026-09-29/30 did not produce
a verified IAMINA legal-controller identity plus signatory-authority artifact.

### IAMINA evidence required

One authoritative legal artifact identifying:
- exact legal entity acting as data controller;
- registered/legal identifier where applicable;
- legal address;
- authorized signatory or delegated signing authority;
- artifact/date proving authority.

The public Git ledger must use only an opaque reference. Do not infer the
controller from a project owner, GitHub account, brand name, developer, clinic or
another company relationship.

## E4 — Groq contracting/DPA coverage for the exact IAMINA customer

### Official baseline

Groq's current DPA states that it is incorporated into the Groq Services
Agreement and applies to Groq processing personal data on behalf of the Customer.
The Services Agreement states that personal data in Customer Data is processed
according to the DPA.

Official references:
- https://console.groq.com/docs/legal/customer-data-processing-addendum
- https://console.groq.com/docs/legal/services-agreement

### IAMINA evidence required

PASS only when the exact Groq account/customer used for IAMINA is tied to the
verified E3 controller (or an explicitly approved contracting structure) and the
reviewer records evidence that the current Services Agreement/DPA applies to that
customer/account.

Capture privately:
- Groq organization/account identifier;
- contracting customer legal name;
- agreement/DPA acceptance or executed-order evidence;
- effective/version date;
- reviewer;
- review date.

Public pages establish terms content, not IAMINA-specific acceptance.

## E5 — Production Groq Zero Data Retention

### Official baseline

Groq's current data documentation says inference customer data is not retained by
default except limited reliability/abuse scenarios, and that organization admins
can enable Zero Data Retention in Data Controls. When ZDR is enabled, Groq says it
does not retain customer data for those reliability/abuse purposes; retention-
dependent features are disabled. Groq also states that retained customer data is
stored in U.S. GCP buckets.

Official reference:
- https://console.groq.com/docs/your-data

### IAMINA evidence required

PASS only with observable production-organization evidence showing ZDR enabled
for the exact Groq organization that will serve IAMINA.

Private evidence should capture:
- Groq organization/account identifier;
- Data Controls screen or equivalent provider evidence;
- ZDR enabled state;
- date/time;
- administrator/reviewer identity or role;
- any feature-level exception;
- model/API path intended for IAMINA.

Do not mark PASS from Groq's generic statement that ZDR is available.

## Recommended evidence order

1. E3 controller/signatory identity.
2. E1 health-processing filing/authorization route tied to E3.
3. E4 exact Groq customer/DPA coverage tied to E3.
4. E5 production Groq ZDR evidence.
5. E2 foreign-transfer filing/authorization using E1 + E3 + E4/E5 evidence as
   applicable.
6. E6 final processor/transfer-specific patient notice and re-consent after the
   approved legal/transfer facts are known.
7. Update governance registry only from reviewed opaque references.
8. Run `python manage.py audit_pilot_consent_governance --require-approved`.
9. Keep runtime fail-closed unless the full audit passes.

## Observable completion criterion

The Groq governance gate may be considered technically ready for policy promotion
only when every E1–E6 row has:
- status `approved`;
- non-empty opaque reference;
- accountable owner role;
- reviewed_on;
- non-expired review_due_on;

and the fail-closed governance audit passes on the exact release HEAD.

Until then: **NO-GO for patient-data egress.**
