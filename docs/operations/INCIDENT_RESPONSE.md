# Pilot Incident Response and Escalation Procedure

## Policy status

Approved operating procedure for the IAmina pilot. Named people and contact details
must live in the restricted on-call roster, not in source control.

Policy owner: IAmina Safety & Security  
Effective: 2026-08-02  
Review due: 2026-11-02

## Severity matrix

| Severity | Acknowledge | Incident commander | Containment target | Mandatory escalation |
|---|---:|---:|---:|---|
| SEV1 | 15 min | 30 min | 60 min | Executive, clinical safety, security and privacy |
| SEV2 | 60 min | 120 min | 240 min | Incident commander; clinical/privacy according to impact |
| SEV3 | 240 min | 480 min | 1,440 min | Service owner |
| SEV4 | 1,440 min | 2,880 min | 4,320 min | Backlog owner |

Patient-safety events, suspected data exposure, authentication compromise and
incorrect clinical outputs default to SEV1. A provider outage defaults to SEV2.
Severity may be raised at any time and may never be lowered merely to meet a target.

## Required roles

- incident commander;
- clinical safety lead;
- security lead;
- privacy lead;
- communications owner.

SEV1 response does not proceed with any of these roles silently omitted. One person
may temporarily hold more than one role, but every responsibility remains explicit.

## Response phases

### 1. Detect and open

Create a minimized, restricted incident record:

```bash
python manage.py create_incident_record \
  --category patient_safety \
  --summary "Potential unsafe output detected in synthetic validation" \
  --systems clinical-summary,ai-gateway \
  --output /secure/incidents/INCIDENT.json
```

Do not put names, email addresses, telephone numbers, patient IDs, clinical values
or message contents into the incident summary. Store sensitive evidence separately
with access controls and reference it by an opaque evidence ID.

### 2. Triage and assign

- assign all required roles;
- confirm severity and category;
- mark patient-safety impact and data-exposure status as confirmed, ruled out or
  still under investigation;
- identify affected versions, services and time window;
- preserve relevant logs without expanding access.

### 3. Contain

Possible containment actions include:

- disable a provider or purpose in the processor policy;
- revoke IAMINA tokens or rotate credentials;
- switch the emergency or AI path to fail-closed mode;
- block a release or rollback a deployment;
- suspend affected processing while preserving deterministic safety functions.

Containment must not erase evidence or create an unsafe clinical fallback.

### 4. Assess notifications

The privacy lead evaluates contractual and regulatory notification obligations using
verified facts and the applicable pilot-country rules. The clinical safety lead
evaluates patient outreach. No notification deadline or recipient is inferred from
this generic procedure.

### 5. Recover

Recovery requires:

- documented root cause or bounded working hypothesis;
- corrective change reviewed and tested;
- security, privacy and clinical-safety acceptance where applicable;
- monitoring for recurrence;
- explicit incident-commander decision to restore normal operation.

### 6. Close and learn

- preserve the final timeline and decisions;
- complete a blameless postmortem for SEV1 and SEV2;
- create owned corrective actions with deadlines;
- update tests, runbooks and policy registries;
- verify temporary access and emergency credentials are revoked.

## Permanent policy audit

```bash
python manage.py audit_incident_response
```

The command fails when the policy is stale, required roles are missing or the
severity matrix is incomplete.

## Drill requirement

Before a real pilot, conduct at least one tabletop exercise covering:

1. unsafe clinical output;
2. suspected data exposure;
3. authentication compromise;
4. provider outage during an emergency interaction.

The drill record, participants and findings remain restricted operational evidence.
