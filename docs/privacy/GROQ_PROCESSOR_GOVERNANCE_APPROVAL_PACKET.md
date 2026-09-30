# IAMINA — Groq Processor Governance Approval Packet

Status: **PREPARED / BLOCKED ON EXTERNAL EVIDENCE**

Date: 2026-09-29

## Goal

Create the shortest auditable path from the current fail-closed Groq policy to a
future processor-governance decision without changing runtime authorization.

## Success criterion

This packet is complete only when E1–E6 each have an IAMINA-specific immutable
reference, accountable owner, review date and PASS decision. Public webpages alone are
not sufficient evidence of account/controller-specific approval.

## Current state

Runtime policy:
- provider: `groq`
- status: `PENDING`
- patient-data egress: denied
- promotion gate: blocked
- patient-visible output: deterministic

## Mandatory evidence

| ID | Evidence | Current status | Exact artifact required |
| --- | --- | --- | --- |
| E1 | CNDP health-data processing authorization | MISSING | IAMINA treatment authorization/receipt reference and private copy of approved filing |
| E2 | CNDP foreign-transfer basis/authorization | MISSING | F118/transfer reference or other expressly applicable CNDP-approved basis tied to IAMINA treatment |
| E3 | IAMINA controller identity/signatory | MISSING | legal controller identity plus evidence of authority to bind that entity |
| E4 | Groq DPA/account coverage | MISSING | proof the exact IAMINA contracting customer accepted/is covered by current Groq Services Agreement + DPA |
| E5 | Production Groq ZDR | MISSING | dated production-org Data Controls evidence showing ZDR enabled for the exact organization and incompatible retention features disabled |
| E6 | Patient notice + re-consent | MISSING | approved notice naming Groq and U.S./international transfer context, version/hash, and tested fail-closed re-consent path |

## Public facts verified 2026-09-29

Groq public documentation:
- inference customer data is not retained by default;
- reliability/abuse logging can retain input/output data up to 30 days unless ZDR is enabled;
- ZDR is configurable in organization Data Controls;
- retained customer data is stored in U.S. GCP buckets;
- the current Groq DPA is incorporated into the Services Agreement and covers processor/subprocessor obligations.

CNDP public documentation:
- health data is sensitive and requires prior authorization;
- transfer abroad has a dedicated procedure;
- CNDP states the underlying treatment must be approved/notified before foreign-transfer authorization;
- the notification procedure lists F-118 for foreign transfer.

References:
- https://console.groq.com/docs/your-data
- https://console.groq.com/docs/legal/customer-data-processing-addendum
- https://console.groq.com/docs/legal/services-agreement
- https://www.cndp.ma/notifier-une-demande-dautorisation-prealable/
- https://www.cndp.ma/transfert-de-donnees-a-letranger/
- https://www.cndp.ma/procedures-de-notification-process/

## Evidence search result

Connected Gmail and Google Drive were searched on 2026-09-29 using Groq/DPA/ZDR and
CNDP/F118/IAMINA terms. No IAMINA-specific artifact satisfying E1–E5 was found.

Repository evidence still identifies E6 as missing because the current patient notice
does not name Groq or the U.S. transfer context.

## Fail-closed decision

Current decision: **NO-GO FOR PATIENT-DATA EGRESS**.

Do not:
- change `groq` status to `APPROVED`;
- remove any `approval_conditions`;
- enable production protected-provider shadow;
- send real patient data to Groq;
- treat generic public legal pages as IAMINA-specific contractual/CNDP evidence.

## Approval sequence once artifacts exist

1. Verify E1–E5 against the exact controller/account/deployment.
2. Record opaque references only in source control; keep private artifacts in the approved compliance repository.
3. Obtain legal/product-approved E6 wording.
4. Implement versioned notice + re-consent and prove old consent fails closed.
5. Update processor evidence registry with reviewed references and expiry/review dates.
6. Update Groq processor policy metadata only when all blockers are cleared.
7. Run `audit_pilot_consent_governance --require-approved`.
8. Run exact-head CI + migration/full relevant tests.
9. Merge with expected-head lock.
10. Production deployment remains a separate explicit authorization.
11. Synthetic smoke first; real patient traffic remains separately gated.

## Human evidence gate

No further runtime activation is technically or governance-valid until E1–E6 evidence
is supplied and independently reviewed. This document prepares the decision; it does
not make it.
