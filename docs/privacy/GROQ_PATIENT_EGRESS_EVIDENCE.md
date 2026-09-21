# IAMINA — Groq patient-egress evidence pack

Status: **BLOCKED_EXTERNAL / HUMAN EVIDENCE REQUIRED**

This document is an evidence checklist for enabling an external generative provider
on authenticated patient paths. It is not legal advice and it does not itself
authorize any patient-data transfer.

## Goal

Permit Groq on authenticated IAMINA patient text only after every contractual,
regulatory, product-consent and deployment-specific condition is evidenced.

## Success

Success is observable only when all mandatory rows below have:
- an IAMINA-specific artifact or official reference;
- date;
- responsible legal/controller entity;
- immutable URL/file reference or SHA256 where applicable;
- reviewer;
- PASS status.

Until then, Groq must remain PENDING in processor policy.

## Existing technical controls already verified

- governed deterministic context;
- generative-context sanitizer;
- PHI pseudonymizer;
- External Anonymization Gateway;
- exact-payload DLP;
- explicit AI consent gate;
- processor policy;
- capability gate;
- FinOps/throttle/circuit breaker;
- response safety/fallback.

These controls reduce risk. They do **not** replace the evidence below.

## Mandatory evidence matrix

| ID | Condition | Minimum acceptable evidence | Status |
| --- | --- | --- | --- |
| E1 | CNDP health-processing basis/authorization | CNDP receipt/authorization reference for the IAMINA treatment, plus copy/link of the approved filing | MISSING |
| E2 | CNDP cross-border transfer basis | F118/reference or other expressly applicable CNDP-approved transfer basis tied to the same underlying treatment | MISSING |
| E3 | IAMINA controller identity | Legal entity/name that is the data controller and signatory authority evidence | MISSING |
| E4 | Groq DPA coverage | Evidence that the IAMINA controller is covered by/has accepted the current GroqCloud DPA/Services Agreement | MISSING |
| E5 | Groq production ZDR | Observable production-org evidence showing Zero Data Retention enabled and retention-dependent features disabled for the exact org used by IAMINA | MISSING |
| E6 | Patient notice + re-consent | Versioned IAMINA notice naming the external processor/transfer context and a tested re-consent path bound to the notice hash | MISSING |

## CNDP evidence notes

CNDP currently states that:
- processing involving health data is subject to prior authorization;
- the treatment must be notified before implementation;
- foreign transfer has a dedicated formal process and F118 form;
- CNDP's foreign-transfer page says transfer authorization is granted only after
  the underlying treatment request/declaration has been approved;
- CNDP's patient-follow-up procedure lists F-113 under its health-data process,
  with supporting documents such as consent/legal basis, information notice,
  subcontracting/confidentiality contract where applicable, and signatory authority.

Applicability of a particular simplified/model form to IAMINA's exact deployment
must be confirmed against the actual controller, purposes and CNDP filing. Do not
infer approval from a generic public form.

Primary sources:
- https://www.cndp.ma/conditions/
- https://www.cndp.ma/notifier-un-traitement/
- https://www.cndp.ma/procedures-de-notification-process/
- https://www.cndp.ma/transfert-de-donnees-a-letranger/
- https://www.cndp.ma/wp-content/uploads/2025/09/CNDP-Transfert-Etranger-F118.pdf

## Groq evidence notes

Groq's current public documentation states that:
- inference customer data is not retained by default;
- inputs/outputs may still be temporarily logged for reliability/abuse cases for
  up to 30 days unless ZDR is enabled;
- organization admins can enable ZDR in Data Controls;
- ZDR disables features that require retention;
- retained customer data is stored in U.S. GCP buckets;
- Groq publishes a Customer Data Processing Addendum incorporated into its
  Services Agreement.

Public documentation cannot prove that IAMINA's production organization actually
has ZDR enabled or that the correct IAMINA legal entity is the contracting customer.

Primary sources:
- https://console.groq.com/docs/your-data
- https://console.groq.com/docs/legal/customer-data-processing-addendum
- https://console.groq.com/docs/legal/services-agreement

## Evidence capture contract

For E1/E2:
- capture exact CNDP reference number;
- document date;
- controller/legal entity;
- exact treatment purpose;
- if transfer-specific, destination/provider/recipient scope where present;
- retain source PDF/official receipt privately; repository documentation should
  record references, not patient data.

For E4:
- identify the exact Groq contracting customer;
- retain accepted agreement/DPA evidence, account/org name and effective date;
- do not rely on a generic public DPA URL as proof of customer coverage.

For E5:
- capture the Groq Data Controls screen for the exact production organization;
- screenshot must show the org/account context and ZDR enabled;
- verify batch/fine-tuning/other retention-dependent features are disabled where
  required by ZDR;
- record capture date;
- do not expose API keys or secrets.

For E6:
- increment IAMINA consent notice version;
- name the actual external processor and international transfer context approved
  by legal/product;
- recompute locale notice hashes;
- require re-consent from existing users before external egress;
- test old consent fail-closed;
- retain UI/behavior evidence at canonical viewports if presentation changes.

## Activation sequence

Do not change order:

1. E1–E5 evidence reviewed and accepted.
2. Legal/product approves exact E6 wording.
3. Implement E6 and any exact policy metadata/references.
4. Keep Groq PENDING until all policy conditions are cleared by evidence.
5. Exact-head CI and PostgreSQL full suite.
6. Merge with expected-head lock.
7. Obtain explicit Vercel production deployment authorization.
8. Configure exact production provider/model/org only after approval.
9. Synthetic production smoke first; no real PHI.
10. Inspect logs for provider success, no DLP bypass, no fallback.
11. Run the agreed 10-turn benign continuity certification.
12. Close out in Notion with immutable evidence references.

## Current verified search result — 2026-09-21

Searched:
- IAMINA Notion workspace;
- connected Google Drive;
- connected Gmail account used for IAMINA/Groq;
- public CNDP/Groq primary documentation.

Result:
- no IAMINA-specific CNDP receipt/F118 evidence found;
- no Groq DPA acceptance evidence found;
- no production-org ZDR evidence found;
- Gmail contains Groq operational/model-deprecation messages, not contractual/ZDR proof.

Therefore E1–E6 remain **MISSING** unless a separate artifact is supplied and verified.
