# P5-6 — Real-patient release gate

> **Status:** ACTIVE / BLOCKED_EXTERNAL  
> **Release posture:** `NOT_RELEASE_AUTHORIZED`  
> **Gate contract:** exact-candidate evidence binding required before any frozen release is eligible  
> **Pilot Readiness arithmetic:** 3/9 = 33.3%  
> **MENA arithmetic:** 32/38 = 84.2%  
> **Deployment:** no Vercel deployment is authorized by this gate.

## Goal

Permit real-patient pilot enablement only after one exact candidate release is backed by retained clinical-human, consent, processor, residency/transfer and deployment-specific approval evidence.

## Success

P5-6 may move to `CLOSED` only when all of the following are true for one exact candidate release SHA:

1. issue #318 qualified clinical-human review requirements are satisfied;
2. issue #320 CNDP/legal/processor/residency requirements are satisfied with deployment-specific evidence;
3. all three repository release audits below pass with `--require-approved` against restricted evidence for that candidate;
4. every audit receives the same explicit expected release SHA through `--expected-source-sha` or `PILOT_RELEASE_SOURCE_SHA`;
5. every restricted manifest carrying `source_commit_sha` matches that exact expected SHA;
6. runtime/provider topology matches the reviewed restricted manifests;
7. a human release decision explicitly authorizes the real-patient pilot.

Anything less remains `NOT_RELEASE_AUTHORIZED`.

## Exact-candidate binding contract

The candidate SHA is an input to the release audit. It must never be inferred from a mutable branch name or accepted merely because a manifest contains some syntactically valid 40-character SHA.

Canonical input:

```bash
export PILOT_RELEASE_SOURCE_SHA=<exact-40-char-git-sha>
```

Each `--require-approved` audit must fail closed when:

- the expected SHA is missing or malformed;
- an approved manifest lacks a valid `source_commit_sha`;
- a manifest `source_commit_sha` differs from `PILOT_RELEASE_SOURCE_SHA`;
- required restricted evidence is missing, stale, incomplete or rejected;
- the enabled runtime/provider topology differs from the reviewed evidence.

This prevents an approval created for candidate N from silently authorizing candidate N+1.

## Fail-closed release audits

### 1. Consent / processor governance

```bash
python manage.py audit_pilot_consent_governance \
  --manifest /restricted/iamina/pilot-consent-governance.json \
  --expected-source-sha "$PILOT_RELEASE_SOURCE_SHA" \
  --require-approved
```

The restricted manifest is read from `--manifest` or `PILOT_CONSENT_GOVERNANCE_MANIFEST_PATH`.

It must include:

- Morocco pilot identity and exact `source_commit_sha`;
- controller reference;
- approved patient notice;
- base AI consent wording;
- granular raw-media consent wording;
- health-data authorization evidence;
- privacy and security approval references;
- fresh review dates;
- account-specific approval records for every **runtime-approved external processor**.

The manifest must not list extra external processors. Providers whose runtime policy is still `pending` or `forbidden` are not made usable by a manifest; patient-data egress remains fail-closed in runtime policy.

### 2. Morocco residency / foreign transfer

```bash
python manage.py audit_pilot_data_residency \
  --manifest /restricted/iamina/pilot-residency.json \
  --expected-source-sha "$PILOT_RELEASE_SOURCE_SHA" \
  --require-approved
```

The residency manifest must still satisfy the existing exact-flow, location, retention, CNDP health-processing and foreign-transfer requirements. In addition, its `source_commit_sha` must equal the explicit expected candidate SHA.

### 3. Qualified clinical safety corpus

```bash
python manage.py audit_safety_corpus_review \
  --manifest /restricted/iamina/safety-review-manifest.json \
  --expected-source-sha "$PILOT_RELEASE_SOURCE_SHA" \
  --require-approved
```

The safety manifest must still match the exact current corpus fingerprint, locale/case/parity coverage, freshness and approval requirements. Its `source_commit_sha` must also equal the explicit expected candidate SHA.

## Reopened external gates

### #318 — Qualified clinical review

Current state: `OPEN / BLOCKED_EXTERNAL_HUMAN`.

Required retained evidence includes:

- qualified clinical-human verdict over the exact fingerprinted enabled corpus;
- safety-owner approval;
- final parity approval across text, voice transcript, mixed-language and transliteration rows;
- explicit decision for rejected/staged variants;
- restricted safety manifest tied to the exact frozen candidate SHA.

Self-review, machine review or synthetic agreement does not satisfy this gate.

### #320 — CNDP, processor and Morocco residency approval gate

Current state: `OPEN / BLOCKED_EXTERNAL_RELEASE`.

Required retained evidence includes:

- exact frozen candidate Git SHA;
- exact runtime/database/cache/email/export/provider topology and countries/regions;
- approved patient notice and consent wording;
- applicable CNDP health-data processing evidence for the actual pilot;
- applicable foreign-transfer evidence/basis for every actual external destination;
- account-specific processor evidence for every enabled external provider;
- restricted consent and residency manifests tied to the same exact candidate SHA.

This repository contract does not replace legal review or infer authorization from public provider documentation.

## Current decision matrix

| Dimension | State | Evidence |
|---|---|---|
| P5-4A PWA engineering | VERIFIED | canonical P5-4A closeout |
| P5-5 synthetic/non-patient rehearsal | VERIFIED | retained P5-5 closeout |
| Three fail-closed audit commands | VERIFIED | repository commands + tests |
| Exact-candidate SHA binding in release audits | REQUIRED BY CONTRACT | candidate must be supplied explicitly at audit time |
| Qualified clinical-human release approval | BLOCKED_EXTERNAL | #318 open |
| Deployment-specific CNDP/legal evidence | BLOCKED_EXTERNAL | #320 open |
| Processor/account-specific approvals | BLOCKED_EXTERNAL | #320 open where external egress is enabled |
| Residency/foreign-transfer restricted manifest approved | BLOCKED_EXTERNAL | #320 open |
| Consent/processor restricted manifest approved | BLOCKED_EXTERNAL | #320 open |
| Exact candidate release audit outputs retained | MISSING | cannot exist before restricted approvals are supplied |
| Real-patient pilot authorization | **NO** | required external/human gates remain open |

## Freeze rule

Do **not** freeze a candidate for external approval until:

1. all gate-hardening changes are merged;
2. exact-main CI is green;
3. that resulting immutable `main` SHA is recorded as the candidate;
4. no further code/configuration change is made without invalidating the candidate approval package.

Documentation or issue comments may record the frozen SHA after merge. The repository must not be modified merely to write the SHA into code, because that would produce a new SHA.

## Stop conditions

Real-patient enablement must stop if any of these is true:

- #318 is not satisfied;
- #320 is not satisfied;
- any `--require-approved` audit exits non-zero;
- `PILOT_RELEASE_SOURCE_SHA` is absent or differs from restricted evidence;
- the safety corpus fingerprint differs from the reviewed manifest;
- deployment/runtime topology differs from reviewed manifests;
- a required human/legal release decision is absent.

## Non-claims

P5-6 does **not** claim legal advice, CNDP authorization, processor approval, production geography, clinical-human approval, real-device packaging approval, production deployment approval or permission to process real patient data.

P5-4A closure and P5-5 synthetic rehearsal do not waive P5-6. External approval gates do not change the retained MENA arithmetic until the canonical roadmap explicitly closes a whole P5 lot.

## Next exact action

Merge and verify the exact-candidate release-evidence binding contract. Then freeze the resulting exact-main SHA and hand that immutable SHA, plus the restricted packet requirements, to #318 and #320. Only after the external evidence exists may all three `--require-approved` audits be executed and retained.

Until those steps pass, P5-6 remains `ACTIVE / BLOCKED_EXTERNAL`, release posture remains `NOT_RELEASE_AUTHORIZED`, and Pilot Readiness remains **3/9 = 33.3%**.
