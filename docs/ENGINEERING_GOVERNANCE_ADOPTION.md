# Engineering governance adoption

IAmina explicitly adopts the central engineering-governance baseline:

- version: `1.0.0`
- exact source commit: `4c0ed295cc095fc5e7f9d0ddde3b1af95ac8dba9`
- adoption manifest: `.governance/adoption.json`

## Precedence

The central doctrine is a minimum engineering baseline. Existing IAmina governance remains authoritative wherever it is stricter or domain-specific, including:

- the canonical forward authority of `docs/ROADMAP.md`;
- the patient-companion authority ceiling and prohibition on diagnosis, prescription, dose advice, treatment optimization/change, or autonomous medical instruction;
- deterministic clinical and emergency logic remaining authoritative over generative models;
- privacy, consent, outbound AI/media egress, payload-minimization, processor and real-patient gates;
- the local-first patient-runtime boundary and the distinction between development/certification infrastructure and patient production;
- the Builder → Reviewer → Release Certifier chain;
- exact-head evidence, double scoring, critical-dimension minimums, caps, and the mandatory Perfection Pass.

This adoption does not authorize release, deployment, real-patient processing, external-provider activation, database/schema/data mutation, merge, or any irreversible action. It does not alter the current roadmap priority or unlock gated work.

There are no exceptions to central doctrine v1.0.0 in this adoption.

Future doctrine upgrades require a new immutable version and exact source SHA. Moving references such as `main` or `latest` are not valid governance pins.
