# Pilot Emergency Operating Mode

## Adopted mode

`SELF_CARE_ONLY`

IAmina does not operate a monitored clinical response center. Emergency detections
produce deterministic guidance and direct the user to local emergency services or
a trusted person. No professional is automatically notified, and no response may
imply otherwise.

## Runtime requirements

- Every user-facing emergency response includes the no-monitoring disclosure.
- Structured replies expose `emergency_operating_mode=SELF_CARE_ONLY` and
  `human_monitoring=false`.
- Emergency detection bypasses generative conversation.
- Country-specific contact details are used only when the country is explicitly
  confirmed and the resource registry is current.
- Missing or stale country resources fall back to generic emergency guidance.

## Enabling monitored mode

`MONITORED_HUMAN` remains invalid unless all of the following exist and are current:

- a real monitored channel;
- a named escalation owner;
- documented staffed hours;
- a completed operational drill;
- approved incident, privacy and clinical procedures.

An environment variable or configured credential alone cannot enable monitored mode.

## Review

Policy owner: IAmina Safety & Compliance  
Effective: 2026-08-02  
Review due: 2026-11-02
