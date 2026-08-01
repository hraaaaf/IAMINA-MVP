# P0-MENA-4B — Text provider evidence ledger

> Last verified: 2026-08-01
>
> This ledger records evidence intake only. It does not approve a provider, model, account, region or production cutover.

## Rules

- Official provider documentation is necessary but not sufficient.
- Account-level settings, region, retention configuration and subprocessors must match the benchmark environment.
- Missing or stale evidence leaves the provider `PENDING` and blocks live execution.
- Synthetic benchmark authorization is separate from production processor-policy approval.

## OpenAI API

- Status: `PENDING`
- Official no-training evidence: API/business inputs and outputs are not used for training by default unless the organization opts in.
- Official source: `https://help.openai.com/en/articles/5722486-api-data-usage-policies`
- Additional data-sharing source: `https://help.openai.com/en/articles/10306912-sharing-feedback-and-api-inputs-and-outputs-with-openai`
- Still required before execution:
  - account-level retention/ZDR confirmation;
  - residency configuration for the actual project;
  - current subprocessor register review;
  - model identifier and pricing evidence;
  - synthetic benchmark credential authorization.

## Google Vertex AI / Gemini

- Status: `PENDING`
- Official no-training evidence: customer data is not used to train or fine-tune managed models without permission or instruction.
- Official retention evidence: zero-data-retention requires feature-specific configuration; some grounding and session features retain data.
- Official source: `https://docs.cloud.google.com/vertex-ai/generative-ai/docs/vertex-ai-zero-data-retention`
- Security controls source: `https://docs.cloud.google.com/vertex-ai/generative-ai/docs/security-controls`
- Still required before execution:
  - exact Vertex project, region and model;
  - abuse-monitoring exception or documented retention posture;
  - cache configuration evidence;
  - grounding/session features disabled for the benchmark;
  - current subprocessor register review;
  - synthetic benchmark credential authorization.

## Claude, Kimi, Mistral, Qwen and local candidates

- Status: `PENDING`
- No eligibility is inferred from repository support or model availability.
- Required:
  - official contractual/privacy sources;
  - exact service tier and region;
  - retention and training posture;
  - subprocessors;
  - pricing and model version;
  - synthetic benchmark credential authorization.

## Decision

No text provider is currently approved for live benchmark execution. The runtime must remain fail-closed until a complete `TextProviderManifest` is reviewed and supplied outside source control.
