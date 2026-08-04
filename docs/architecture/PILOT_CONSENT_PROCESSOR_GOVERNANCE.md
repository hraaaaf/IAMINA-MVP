# Pilot consent and processor governance

**Status:** engineering preparation complete only after CI; legal/privacy/processor approval remains external.

**Policy version:** `2026-08-04.1`

**Pilot country:** Morocco

## 1. Invariant

No single fact authorizes patient-data egress.

The following gates are independent and all must be satisfied where applicable:

1. the patient received the approved notice;
2. the patient gave base AI consent;
3. raw audio, image or document use has an exact purpose/modality grant;
4. the health-data treatment has the required CNDP authorization;
5. any foreign transfer has the required CNDP authorization or an approved documented basis;
6. the exact processor, account, product, model and deployment region are approved;
7. the current DPA, processor terms and subprocessor evidence are approved;
8. retention, deletion and training-use terms are approved;
9. security and privacy owners approved the deployment.

Patient consent does not replace CNDP authorization, contractual evidence, security review or processor approval.

## 2. Morocco source baseline

Official CNDP material reviewed on 2026-08-04 states that:

- health data is sensitive and its processing is subject to prior authorization;
- processing must have a precise disclosed purpose and use necessary, proportionate data;
- the controller must contractually and operationally ensure processors comply with Law 09-08;
- a foreign transfer requires a separate transfer procedure or applicable approved basis;
- the underlying treatment must itself have been notified/authorized before a foreign-transfer authorization is granted;
- notification files require the applicable patient notice/consent basis and processor confidentiality clauses.

Official references:

- `https://www.cndp.ma/conditions/`
- `https://www.cndp.ma/notifier-une-demande-dautorisation-prealable/`
- `https://www.cndp.ma/transfert-de-donnees-a-letranger/`
- `https://www.cndp.ma/procedures-de-notification-process/`

These references are an engineering evidence baseline, not legal advice or proof that IAMINA has received an authorization.

## 3. Executable matrix

`backend/core/pilot_consent_governance.py` derives its matrix from every purpose/modality currently registered in `ai_processor_policy.py`.

Permanent invariants:

- a new runtime purpose or modality creates matrix drift until explicitly covered;
- every audio, image and document path requires granular consent;
- every external processor path requires base AI consent, health-data authorization, foreign-transfer clearance and processor approval;
- a provider cannot become runtime `approved` while the governance registry has blockers;
- local fallback paths are explicitly no-external-egress and cannot be reused to authorize network calls.

## 4. Processor evidence registry

The registry covers every runtime processor identifier:

- `gemini` — pending deployment-specific Google contracting, subprocessor, region, retention, training, security, privacy and CNDP evidence;
- `claude` — pending deployment-specific Anthropic evidence;
- `kimi` — pending processor identity and all deployment-specific evidence;
- `fallback` and `quota-exhausted` — approved local-only identities with all foreign-processor fields explicitly not applicable.

Official provider pages are pointers for review, not approval:

- Google Cloud data residency: `https://cloud.google.com/terms/data-residency`
- Google Cloud subprocessors: `https://cloud.google.com/terms/subprocessors`
- OpenAI subprocessors, for future candidate evaluation only: `https://openai.com/policies/sub-processor-list/`

The approved ledger must record the exact account and product terms actually used. A generic public webpage cannot prove account-specific retention, no-training configuration, selected region or contractual acceptance.

## 5. Commands

Structural audit, expected to report pending external approvals:

```bash
cd backend
python manage.py audit_pilot_consent_governance
```

Fail-closed real-pilot gate:

```bash
cd backend
python manage.py audit_pilot_consent_governance --require-approved
```

The second command must fail until all external evidence is current and approved.

## 6. Evidence handling

Source control may contain:

- public policy references;
- evidence status;
- accountable role;
- review and expiry dates;
- opaque approval references.

Source control must not contain:

- signed contracts;
- patient consent records;
- CNDP private correspondence;
- credentials;
- private processor audit reports;
- personal contact details.

Restricted evidence must be held in the approved private compliance repository and referenced by opaque identifier only.

## 7. Approval checklist

The roadmap gate remains open until all of the following are true:

- [ ] final patient notice and consent wording approved;
- [ ] CNDP health-data processing authorization reference recorded;
- [ ] foreign-transfer authorization/basis recorded for every destination;
- [ ] exact processors and subprocessors approved;
- [ ] exact deployment regions approved;
- [ ] DPA and service terms approved;
- [ ] retention, deletion and no-training behavior approved;
- [ ] security review approved;
- [ ] privacy review approved;
- [ ] `audit_pilot_consent_governance --require-approved` passes;
- [ ] approval evidence is current on pilot launch day.
