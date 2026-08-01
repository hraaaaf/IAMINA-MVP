# P0-MENA-4 — Provider benchmark execution runbook

## Preconditions

1. Select exact provider, model, service tier and region.
2. Attach current official and account-level evidence for training use, retention, residency and subprocessors.
3. Approve synthetic-only credentials and a bounded cost budget.
4. Confirm raw-output retention and deletion rules.
5. Obtain required linguistic, clinical and privacy reviewers.

## Execution order

1. Build a readiness report for each modality.
2. Stop if any candidate is not ready; preserve the explicit reason.
3. Run only the canonical synthetic/minimized cases for that modality.
4. Persist dataset fingerprints, model identifiers, timestamps, latency and raw machine-verifiable results.
5. Apply deterministic judges and weighted scoring.
6. Record unavailable or disqualified candidates rather than omitting them.
7. Produce the modality-specific decision and rejected-alternative ledger.
8. Require human review for language and clinical-safety dimensions.
9. Run the production cutover gate separately from the benchmark.

## Required output package

- readiness reports;
- provider manifests without credentials;
- dataset fingerprints;
- versioned benchmark report;
- cost and latency evidence;
- human-review sign-offs;
- modality-specific decision matrix;
- rejected alternatives with reasons;
- processor-policy approval or explicit denial.

## Fail-closed rules

- No key means no network call.
- Missing or stale evidence means no network call.
- A successful benchmark does not authorize production.
- No provider is selected when every candidate is disqualified.
- Scores must never be entered manually without linked run evidence.
