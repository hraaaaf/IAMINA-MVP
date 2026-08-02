# Pilot Onboarding, Monitoring, Escalation and Exit Checklists

## Status

Approved operating procedure for one founder-selected pilot cohort. The checklist
registry is versioned in code; completed cohort evidence remains restricted and is
never committed to source control.

Policy owner: IAmina Pilot Operations  
Effective: 2026-08-02  
Review due: 2026-11-02

## Permanent registry audit

```bash
python manage.py audit_pilot_checklists
```

The command fails when a phase is missing, IDs collide, required fields are absent
or the policy review date is stale.

## Create a restricted cohort checklist

Use an opaque cohort identifier, never a person's name, email or phone number:

```bash
python manage.py create_pilot_checklist \
  --cohort-id PILOT_001 \
  --output /secure/pilot/PILOT_001-checklist.json
```

The generated file is written atomically with mode `0600`. Every item starts as
`PENDING` and contains no participant-level information.

## Evidence rules

- `PASS` requires an opaque evidence reference, the configured owner role and a
  review timestamp.
- `NOT_APPLICABLE` is forbidden for blocking items.
- A non-blocking item may use `NOT_APPLICABLE` only with a meaningful rationale.
- Evidence references point to restricted systems; they do not contain patient
  identifiers or raw clinical content.
- A checklist cannot pass with missing or duplicate registry items.

Validate the completed file:

```bash
python manage.py validate_pilot_checklist \
  --file /secure/pilot/PILOT_001-checklist.json
```

## Onboarding

Before enrolment, the team must establish cohort scope and stop criteria, verify
identity and eligibility, capture approved consent and active media permissions,
confirm locale and emergency resources, disclose IAmina's companion limits and
self-care-only emergency mode, verify all readiness gates and complete a synthetic
safety/support-channel test.

## Monitoring

During the pilot, owners review service health, failed requests, provider
availability, safety refusals, emergency detections, unexpected clinical output,
consent changes, processor-policy changes, retention/authentication/secret audits,
support requests, withdrawals, outcomes and stop criteria at the configured daily
or weekly cadence.

## Escalation

Each incident must be classified, assigned to all mandatory roles, contained in a
fail-closed manner, assessed for patient outreach and notification duties, and
closed only after recovery, recurrence monitoring and postmortem actions are
approved. The incident-response procedure remains authoritative.

## Exit

Participant or cohort exit requires a recorded reason, data-export offer, access
revocation, retention/deletion/legal-hold decision, outcome lock with limitations,
and a cross-functional clinical, security, privacy and product debrief.

## Non-claims

This repository certifies that complete procedures and executable validation exist.
It does not claim that a particular cohort has passed. The real pilot remains
blocked until its restricted checklist file validates and all external human,
privacy, processor and country-specific approvals are current.
