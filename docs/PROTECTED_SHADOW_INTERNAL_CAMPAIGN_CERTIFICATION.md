# IAMINA — Protected Shadow Internal Campaign Certification

Status: **CERTIFIED — PRE-MERGE**

PR: #834  
Branch: `conversation/protected-shadow-internal-campaign`  
Evidence HEAD: `f0c363d8d6fc3c4e6f11f3ad03fcc36a8ec514de`  
Certification commit: documentation-only; it does not alter runtime or tests.

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

## Exact-head evidence

Evidence HEAD `f0c363d8d6fc3c4e6f11f3ad03fcc36a8ec514de`:

1. CI #5134 — SUCCESS;
2. Django migration drift #4157 — SUCCESS;
3. Companion real chat E2E screenshots #305 — SUCCESS;
4. PR #834 mergeable against main at certification time.

The certification commit changes this Markdown file only. Required CI must also remain
green on the final PR HEAD before merge.

## Governance invariants

This PR does not:

- approve Groq processor policy;
- alter processor policy;
- enable patient provider egress;
- expose deterministic clinical bodies to the provider;
- increase clinical authority;
- activate patient-visible generated narration;
- deploy Vercel.

## Certification boundary

This certifies the bounded internal dry-run campaign infrastructure and synthetic
adversarial evidence only. It does **not** authorize real patient-data provider traffic.
That remains blocked until explicit processor-governance approval.
