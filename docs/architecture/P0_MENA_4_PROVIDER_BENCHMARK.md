# P0-MENA-4 — Permanent multimodal provider benchmark

## Purpose

IAMINA selects providers by reproducible evidence, per modality. Text, STT, document OCR, glucometer OCR and meal vision are evaluated independently.

## Non-negotiable rules

1. Fixtures are synthetic and minimized. Real patient data is forbidden.
2. Safety and privacy are hard eligibility floors. Quality, latency or cost cannot compensate for failure on either dimension.
3. Contractual facts require an owner, source, verification date and review date.
4. Unknown, stale or incomplete privacy evidence disqualifies the provider.
5. A benchmark result cannot authorize production egress. The processor-policy registry remains the final runtime gate.
6. Decisions are modality-specific. No universal provider is assumed.
7. Every rejected alternative keeps explicit reasons.

## Evaluation dimensions

| Dimension | Weight | Gate |
|---|---:|---|
| Safety | 30% | minimum 80/100 |
| Privacy | 25% | minimum 80/100 and no disqualification |
| Quality | 20% | scored per modality and locale |
| Availability | 10% | measured success rate |
| Latency | 10% | bounded percentile score |
| Cost | 5% | normalized per accepted unit |

## Dataset coverage

The canonical dataset covers:

- French, English and Modern Standard Arabic;
- Moroccan Darija in Arabic and Latin transliteration;
- mixed-language and mixed-script inputs;
- high-severity refusal/escalation cases;
- STT concept preservation;
- structured document OCR;
- glucose value and unit extraction;
- meal-vision uncertainty.

Every case has a stable identifier and deterministic fingerprint.

## Execution phases

### 4A — Evaluation set

Strict immutable case contract, synthetic/minimized enforcement, coverage tests and stable fingerprints.

### 4B — Framework

Provider-neutral adapter protocol, deterministic scoring, provenance-preserving runs and versioned reports.

### 4C — Provider evaluation

Live provider calls may run only in an explicitly authorized benchmark environment using synthetic payloads. Credentials are never committed. Raw responses must be retained only according to the benchmark retention policy.

### 4D — Decision matrix

Eligible providers are ranked per modality. Disqualified providers remain documented with reasons. If no provider passes, the selected provider is `null` and production cutover fails closed.

## Production cutover gate

A provider may be proposed for production only when all conditions hold:

- benchmark dataset version and fingerprints are recorded;
- score is reproducible;
- safety and privacy floors pass;
- legal/processor evidence is current;
- rejected alternatives are documented;
- runtime processor policy is separately approved;
- CI is green on SQLite, PostgreSQL, security, OpenAPI, Flutter and migration drift.
