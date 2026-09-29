# IAMINA — Protected Shadow Promotion Gate Certification

Status: **CERTIFIED — PRE-MERGE**

PR: #835  
Branch: `conversation/protected-shadow-promotion-gate`  
Evidence HEAD: `c572904095fa1e9a872064ba8ee884b34dfdf63d`

## Goal

Certify the fail-closed promotion evaluator without authorizing processor governance,
provider activation, patient egress, or patient-visible generated narration.

## Exact-head evidence

Evidence HEAD `c572904095fa1e9a872064ba8ee884b34dfdf63d`:

1. CI #5137 — SUCCESS;
2. Django migration drift #4160 — SUCCESS;
3. Companion real chat E2E screenshots #307 — SUCCESS.

## Certified behavior

Promotion remains blocked unless every explicit prerequisite is satisfied. The current
governance state is intentionally non-promotable because Groq processor governance is
not approved for patient-data egress.

## Boundary

This certification does not approve Groq processor governance and does not authorize
internal-live or patient provider traffic. No processor-policy edit and no Vercel deploy
are part of this lot.

The certification commit is documentation-only. Required CI must remain green on the
final PR HEAD before merge.
