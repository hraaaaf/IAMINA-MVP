# IAMINA — Protected Shadow Internal Campaign Certification

Status: **PENDING EXACT-HEAD CI**

PR: #834  
Branch: `conversation/protected-shadow-internal-campaign`  
Candidate HEAD: `bdc0ec6c64e42c1169da600158e7882e5b2ff581`

## Goal

Prove that the next protected narration step can be exercised as a bounded internal
campaign without weakening processor governance, exposing patient content to a provider,
or changing patient-visible clinical output.

## Evidence implemented

- hard campaign bound through `max_turns`;
- single provider: `groq`;
- single family: `clinician_prep`;
- exact telemetry field allowlist;
- content-free aggregate reporting;
- fail-closed rejection of extra telemetry fields;
- policy-blocked dry-run proves provider construction is not reached;
- synthetic accepted candidate path;
- synthetic adversarial rejected paths;
- synthetic provider-error path;
- deterministic patient reply assertion across synthetic candidate paths;
- existing protected narration adversarial suite remains part of repository validation.

## Governance invariants

This PR does not:

- approve Groq processor policy;
- alter processor policy;
- enable patient provider egress;
- expose deterministic clinical bodies to the provider;
- increase clinical authority;
- activate patient-visible generated narration;
- deploy Vercel.

## Certification gate

Do not change this document to CERTIFIED until all exact-head required CI checks for the
candidate HEAD are successful.

Required final evidence:

1. CI exact HEAD — SUCCESS;
2. Django migration drift exact HEAD — SUCCESS;
3. Companion real chat E2E screenshots exact HEAD — SUCCESS;
4. PR mergeable against current main;
5. candidate HEAD unchanged after those checks.

If any required check fails, certification remains blocked and the failure must be
corrected on the branch before reassessment.
