# Pilot CNDP + provider evidence snapshot — 2026-08-18

## Goal

Record current official external evidence relevant to IAMINA's remaining Morocco pilot compliance gates without converting public information into legal, processor, privacy, security or deployment approval.

## Runtime processors in scope

`backend/core/pilot_consent_governance.py` currently requires evidence for three external-egress provider identities:

- `gemini`
- `kimi`
- `claude`

`fallback` and `quota-exhausted` are local/no-external-egress identities and are not foreign processors.

The executable governance gate still requires, for each external provider: processor identity, DPA/service terms, subprocessor register, processing regions, retention/deletion, training-use policy, security review, privacy review, CNDP health-processing authorization and CNDP foreign-transfer authorization.

## Morocco CNDP facts verified from official CNDP sources

### Health data

The CNDP currently states that health data are sensitive personal data and that processing involving health data requires prior authorization.

Current notification guidance also exposes a dedicated health-data path for patient follow-up under Délibération n° D-941-2025 du 28/11/2025, using the prior-authorization form F-113 and requiring, among other items, consent/legal-basis evidence, the information notice, subcontracting/confidentiality documentation where applicable and proof of signing authority.

Sources checked 2026-08-18:

- https://www.cndp.ma/formalites/
- https://www.cndp.ma/procedures-de-notification-process/
- https://www.cndp.ma/notifier-un-traitement/

### Foreign transfers

The CNDP states that a transfer of personal data abroad requires the applicable foreign-transfer process. The current page exposes form F-118 and states that authorization for foreign transfer is granted only after the underlying processing has itself been declared/authorized by the CNDP.

The published supporting-document list includes, where applicable, treatment authorization references, consent evidence and contractual/internal rules supporting the transfer.

Source checked 2026-08-18:

- https://www.cndp.ma/transfert-de-donnees-a-letranger/

### Consequence for IAMINA

The existing repository model is directionally correct: `cndp_health_processing_authorization` and `cndp_foreign_transfer_authorization` must remain separate fail-closed evidence fields. Public provider privacy pages cannot close either field.

No CNDP authorization number or transfer approval is currently recorded in repository evidence. Therefore the two fields remain `PENDING` for all external providers.

## Provider evidence snapshot

### `gemini`

Official Google Cloud material currently confirms that several Google Cloud AI/ML services can be configured for data location, including Generative AI on Vertex AI and multiple speech/vision/document services. Google also publishes a maintained Google Cloud subprocessor framework.

However IAMINA's provider key is only `gemini`. Repository evidence does not currently prove the exact production account, contracting entity, API product, model path or selected processing region. It would therefore be unsafe to infer that IAMINA uses a residency-eligible Vertex AI path merely from the provider label.

Verified public inputs:

- https://cloud.google.com/terms/data-residency
- https://cloud.google.com/terms/subprocessors

Current result: **PUBLIC EVIDENCE AVAILABLE / ACCOUNT-SPECIFIC APPROVAL STILL PENDING**.

Required next evidence before approval:

1. exact Google contracting entity and IAMINA account/project;
2. exact Gemini product/API path and model;
3. selected region/multi-region and proof that the chosen path is covered by the applicable data-location terms;
4. current account-specific DPA/service terms;
5. current subprocessor evidence tied to the applicable service;
6. retention/no-training configuration and evidence;
7. IAMINA privacy/security approvals;
8. CNDP health-processing authorization;
9. CNDP foreign-transfer authorization/basis for every actual foreign destination.

### `claude`

Anthropic's current commercial-product privacy material states that Anthropic API inputs/outputs are normally deleted from backend systems within 30 days, subject to stated exceptions and different contractual arrangements. Anthropic also states that commercial-product inputs/outputs are not used for model training by default. Zero-data-retention arrangements exist for some approved enterprise API customers and are not the default.

These are useful public review inputs but do not establish IAMINA's contracting entity, DPA, subprocessor set, processing geography or a ZDR arrangement.

Verified public inputs:

- https://privacy.anthropic.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data
- https://privacy.anthropic.com/en/articles/7996868-is-my-data-used-for-model-training
- https://privacy.anthropic.com/en/articles/8956058-i-have-a-zero-data-retention-agreement-with-anthropic-what-products-does-it-apply-to

Current result: **PUBLIC RETENTION/TRAINING EVIDENCE AVAILABLE / ACCOUNT-SPECIFIC APPROVAL STILL PENDING**.

Required next evidence before approval:

1. exact Anthropic commercial account and contracting entity;
2. executed DPA/current commercial terms;
3. current applicable subprocessor evidence;
4. processing-region evidence for the actual API path;
5. actual retention configuration, including whether a ZDR agreement exists;
6. IAMINA privacy/security approvals;
7. CNDP health-processing authorization;
8. CNDP foreign-transfer authorization/basis for every actual foreign destination.

### `kimi`

Repository evidence already marks the endpoint operator, contracting entity, subprocessors and processing regions as unapproved. During the 2026-08-18 evidence pass, no sufficiently authoritative current official processor/subprocessor/residency package was identified that could safely satisfy those account-specific fields.

This is not a claim that such documentation does not exist. It is a fail-closed evidence result: no suitable evidence is currently in hand.

Current result: **INSUFFICIENT AUTHORITATIVE EVIDENCE / PENDING**.

Required next evidence before approval:

1. exact Kimi/Moonshot API operator and contracting entity;
2. executed account-specific terms/DPA or equivalent processor contract;
3. official current subprocessor register;
4. exact processing/storage regions;
5. retention/deletion and model-training policy for the exact API account/product;
6. IAMINA privacy/security approvals;
7. CNDP health-processing authorization;
8. CNDP foreign-transfer authorization/basis for every actual foreign destination.

## Decision

No external processor can be marked approved from this snapshot.

The existing fail-closed command remains authoritative:

```bash
cd backend
python manage.py audit_pilot_consent_governance --require-approved
```

A non-zero result remains a STOP for real-patient pilot enablement.

## Shortest compliance path

1. Freeze the candidate deployment topology and exact provider/API choices.
2. Prepare the CNDP health-data authorization file using the current patient-follow-up procedure where applicable.
3. Obtain account-specific contractual/processor evidence only for providers actually intended for the pilot.
4. Prepare F-118 foreign-transfer evidence for each actual external destination after/with the underlying processing authorization as required by CNDP.
5. Record opaque approval references in the restricted evidence store, not secrets/contracts in Git.
6. Run both `audit_pilot_consent_governance --require-approved` and the deployment-residency gate against the exact release SHA.

## Non-claims

This snapshot is engineering/compliance preparation only. It is not legal advice, CNDP authorization, processor approval, privacy approval, security approval, deployment approval or pilot authorization.
