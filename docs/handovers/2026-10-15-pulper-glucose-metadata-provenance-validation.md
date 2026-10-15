# IAMINA — Pulper source-bound glucose metadata — 15 octobre 2026

## Goal / Success / Proof
- **Goal**: prevent any LLM-generated glucose timestamp, meal context, original value/unit or lab report date from appearing in preview/persistence without its own verified source citation, even when an associated critical numeric value is sourced.
- **Success**: negative synthetic fixtures remove uncited/wrong-time data but retain valid numeric glucose; positive fixtures preserve an exact explicitly cited timezone-aware timestamp and report date. Deterministic CSV/XLS/XLSX path is unchanged. Confirmation/store skips a glucose reading without a trusted timestamp.
- **Proof expected**: tests in `backend/diabetes/tests/test_pulper_provenance.py`, plus exact-head full CI (SQLite/PostgreSQL, macOS/Windows, Protected Shadow, Pulper synthetic corpus), and artifact readback. Issue [#1042](https://github.com/hraaaaf/IAMINA-MVP/issues/1042).
- **Status**: implementation candidate, NOT yet CI-qualified. Initial defect identified by static code review, not an observed patient incident.

## Boundary
- A field-level cited text occurrence is evidence for human review, NOT a medical interpretation or physician acceptance.
- This is a **follow-up** distinct from closed technical #1011/#1019/#1023; do not retroactively inflate the previously passed 16-case corpus.
- No patient data, no merge main, no Vercel. Parent [#1005](https://github.com/hraaaaf/IAMINA-MVP/pull/1005) remains DRAFT. Separate real-world clinical/provider/privacy gates are outside this technical lot.

## Reliability follow-up #1045 — prompt refinement candidate
- Two live synthetic attempts on prior head `c82e93d13c605536a487fde9ee9250ff76501b84` failed DOCX fasting field (17/18 critical, no false positive). First HTTP 400, second ungrounded/omitted field; cause of second is not proven from provider response. See [#1045](https://github.com/hraaaaf/IAMINA-MVP/issues/1045).
- This candidate adds a **source-grounded fasting glucose example** to prompt version `pulper-parse-v6-fasting-evidence` and tests correct strict reply, rejection of unsourced exemplar, and timestamp non-invention. **No deterministic fallback**, no change of Groq parameters, no threshold relaxation.
- Status: source/test change created, exact SHA CI and one live synthetic benchmark not yet verified. If it fails, keep child open and do not merge parent; investigate provider separately, no further blind reruns.

## 15 octobre 2026 — Source rule P1 fallback gated to explicit, unambiguous text
- A subsequent exact-HEAD synthetic qualification at `0747243` FAILED 17/18 on the **prompt-injection HbA1c** case although all patient-source controls failed closed. Prompt-only v6 is insufficient to prove repeated extraction reliability.
- Corrective design: after a SUCCESSFUL Groq JSON extraction, source-only deterministic recovery of **a single entire exact laboratory line**, restricted to `HbA1c: <number> %` or `Fasting glucose: <number> mg/dL`, and only when the model **omitted the field and its evidence** (never after malformed/failed provider calls, explicit contradiction, multiple candidates, or ambiguous line).
- Recovery creates **separately verified, source-line-bound** `FieldEvidence`, a generic review-required warning, and a separately reported `source_rule_recovered_fields` metric and per-case `source_rule_recovered` flag in the synthetic corpus report. This is a **transparent deterministic parser safety net**, NOT Groq accuracy; no fallback is hidden and numeric/clinical guardrails are unchanged.
- New negative/positive tests include injection contamination, fasting line, duplicates/target line/wrong unit, contradicted LLM fact, malformed envelope; no real-patient egress.
- **NOT YET CI VALIDATED** at commit creation. Existing strict 99% critical precision/recall and 100% provenance/fail-closed thresholds remain. If a 400 is returned by provider, ingestion remains fail-closed; reliability issue #1045 remains open.

## Final one-run qualification gate, code finalized
- Explicitly malformed `evidence` maps such as `[]`, `null`, or a string now fail closed: only ABSENT maps may default to `{}`. Negative tests cover this.
- A new Django database test enforces no `LogEntry` persistence of a glucose event with LLM-invented timestamp or meal context even if the numeric value is source-verified.
- The benchmark emits `source_rule_recovered_fields` and a per-case `source_rule_recovered` boolean to distinguish an exact independent source-literal recovery from Groq model extraction; existing thresholds remain untouched.
- **FINAL CODE READY FOR FIRST CONTROLLED BENCHMARK; NOT YET SUCCESS**. HEAD of this doc-trigger commit must pass exact-head Pulper/CI/Protected Shadow/Django/Companion/portability before integration. No real patient, no main merge or Vercel.
