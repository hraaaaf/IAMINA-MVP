# P0-MENA-4 / #319 — Benchmark candidate freeze — 2026-08-18

Status: **PRE-RUN FREEZE / NO PAID OR NETWORK BENCHMARK EXECUTED**

Base SHA: `55cc5957c109f98cb217a942619087d8833a2745`

## Goal

Freeze a small, reproducible candidate set for the already-merged synthetic/minimized multimodal benchmark before any paid/network invocation.

## Candidate set

### Text

1. OpenAI API — `gpt-5.6`
2. Google Vertex AI — Gemini family candidate, exact account-visible model ID to be confirmed immediately before execution
3. Mistral API — `mistral-medium-3-5`

### STT

1. OpenAI API — `gpt-4o-transcribe`
2. OpenAI API — `gpt-4o-mini-transcribe`
3. Mistral API — Voxtral Mini Transcribe 2, exact account-visible model ID to be confirmed immediately before execution

### Vision / OCR

1. OpenAI API — `gpt-5.6` with image input
2. Google Vertex AI — Gemini multimodal family candidate, exact account-visible model ID to be confirmed immediately before execution
3. Mistral API — `mistral-ocr-4-0` for document OCR

## Execution constraints

- Synthetic/minimized repository fixtures only.
- No patient data.
- No credential committed to Git.
- Exact provider/model/API/region identity must be captured in each run record.
- Account-visible model IDs and regions are checked immediately before execution because provider catalogs are mutable.
- Missing credential, model identity, region, budget authorization or execution authorization is STOP.
- Benchmark success does not authorize production or real-patient cutover.

## Evidence snapshot used for the freeze

- OpenAI official API overview currently documents `gpt-5.6` as a Responses API model with text and image capability.
- OpenAI official audio API currently lists `gpt-4o-transcribe` and `gpt-4o-mini-transcribe` for `/v1/audio/transcriptions`.
- Google Vertex AI release notes show the Gemini 3.x line is active in 2026; the exact benchmark model ID must be confirmed in the target project before invocation rather than inferred from stale repository documentation.
- Mistral official model documentation currently lists Mistral Medium 3.5, Voxtral Mini Transcribe 2, and OCR 4; OCR 4 exposes ID `mistral-ocr-4-0`.

## Pre-run gate

Required before the first paid/network call:

1. credentials available out of source control;
2. explicit network/API authorization;
3. explicit total spend ceiling;
4. exact account/project region and model ID confirmed for each candidate;
5. dry-run manifest validation passes locally/CI without invoking providers.

## Accounting

This freeze does not close any #319 live benchmark outcome and does not change the MENA numerator.
