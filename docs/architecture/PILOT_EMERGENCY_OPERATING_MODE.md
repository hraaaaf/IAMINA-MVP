# Pilot emergency operating mode

## Status

**Decision:** `SELF_CARE_ONLY`

IAMINA does not currently operate a staffed or continuously monitored human escalation service. Until such a service is designed, contracted, staffed, tested and approved, every emergency path must state only what the patient can do directly and which verified public emergency resources can be contacted.

## Safety invariants

1. Emergency classification is deterministic and runs before generative AI.
2. Emergency responses must never claim that a clinician, support agent or emergency operator has been notified.
3. No alert is described as monitored unless a real staffed channel, named owner, service hours, SLA, fallback and test evidence are configured.
4. Country-specific emergency resources are selected only from a confirmed patient country and a current versioned registry.
5. Missing, unknown or expired country resources fail closed to a generic instruction to contact local emergency services immediately.
6. IAMINA does not place calls, dispatch services or guarantee response times.
7. Emergency events may be recorded for audit, but audit storage is not clinical monitoring.

## Conditions required before `HUMAN_MONITORED`

A future human-monitored mode requires all of the following evidence:

- named operational owner and backup owner;
- documented service hours and supported countries;
- staffed channel with tested delivery and acknowledgement;
- response-time SLA and escalation ladder;
- privacy and consent basis for transmitting the alert;
- outage, duplicate-alert and missed-alert procedures;
- training and competency requirements for responders;
- end-to-end drills with retained evidence;
- explicit product copy distinguishing monitoring from emergency services;
- approved rollback to `SELF_CARE_ONLY`.

A configuration flag alone must never enable human-monitoring claims.

## Pilot acceptance criteria

- All emergency text, streaming and voice paths use deterministic responses.
- Product copy contains no unproven notification or monitoring claim.
- Morocco resources are current, versioned and selected only after country confirmation.
- Unknown or expired resources produce a safe generic fallback.
- CI includes a permanent search/test gate for prohibited monitoring claims.
