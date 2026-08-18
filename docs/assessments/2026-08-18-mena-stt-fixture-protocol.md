# P0-MENA-4 / #319 — STT benchmark fixture protocol

Status: **FIXTURE CONTRACT / NO AUDIO COLLECTED BY THIS DOCUMENT**

## Goal

Create a small, traceable, non-patient speech corpus that can truthfully measure local and provider STT candidates for IAMINA before any runtime cutover.

## Success

A benchmark run is eligible to publish STT accuracy only when every scored case references a real repository-controlled audio fixture with a verified SHA-256 and a human-checked reference transcript.

## Evidence boundary

A transcript string alone is not STT evidence. Generated placeholder bytes, silent WAV files, copied provider transcripts, or an adapter that returns the reference text are not valid benchmark audio.

## Privacy and consent

- No patient recording.
- No real clinical encounter.
- No name, phone, identifier, address, appointment, device serial or other personal information.
- Use consenting project test speakers or explicitly labelled synthetic speech only.
- Human-recorded and synthetic-TTS clips must never be pooled without a `source_type` field.
- Speech content is fixed benchmark copy, not a speaker's real health state.

## Minimum initial corpus

The first useful corpus should contain at least 12 clips: 2 independently recorded renditions of each of the 6 canonical phrases below. This is a smoke/selection corpus, not a population-level language validation.

| ID | Locale | Controlled phrase | Critical tokens/concepts |
|---|---|---|---|
| stt_fr_low_54 | fr | `Ma glycémie est à 54, je me sens étourdi.` | `54`, low glucose, dizziness |
| stt_fr_hba1c | fr | `Mon HbA1c est à 7,4 pour cent.` | `HbA1c`, `7.4` |
| stt_ar_low | ar | `السكر عندي منخفض وأنا أشعر بالدوخة.` | low glucose, dizziness |
| stt_ar_number | ar | `قراءة السكر أربعة وخمسون مليغرام لكل ديسيلتر.` | `54`, `mg/dL` concept |
| stt_darija_latn | ar-MA-Latn | `sokkar tay7 بزاف, kan7ess b dowkha` | low glucose, dizziness, code-switch/script mix |
| stt_mixed_en | mixed | `sokkar tay7 بزاف, I feel dizzy` | low glucose, dizziness, Arabic/Darija + English |

Reference transcripts may preserve spelling variants, but numeric values and safety-critical concepts must remain explicit and separately scored.

## Capture profiles

For each phrase, capture two independent renditions rather than duplicating one file:

1. quiet-room, normal speaking rate;
2. realistic phone-distance rendition with mild room noise.

Initial canonical archive format:

- WAV PCM;
- mono;
- 16 kHz;
- 16-bit.

Later transport robustness may add derived AAC/m4a and Opus/WebM versions because IAMINA mobile/web currently uploads those formats. Derived encodings must reference the source clip and have independent SHA-256 values.

## Required fixture metadata

Each audio file must have a sidecar record containing:

- `fixture_id`;
- `audio_fixture` repository-relative path;
- `audio_sha256` lowercase SHA-256;
- `source_type`: `human_test_speaker` or `synthetic_tts`;
- `locale`;
- `reference_transcript`;
- `critical_tokens` and/or `required_concepts`;
- `capture_profile`;
- `sample_rate_hz`;
- `channels`;
- `encoding`;
- `duration_ms`;
- `consent_recorded`: true for human test speakers;
- `patient_data`: false;
- `created_on`;
- `reviewed_by` or `review_status`.

Do not store speaker name or other identity in the benchmark metadata.

## Scoring

Raw word error rate alone is insufficient for IAMINA.

Score separately:

1. exact numeric preservation;
2. glucose/HbA1c unit preservation where spoken;
3. critical concept recall: low glucose, dizziness, etc.;
4. language/code-switch preservation;
5. overall normalized WER/CER as a secondary metric;
6. latency and model/runtime footprint.

A candidate automatically fails the safety floor for a case if it materially changes a critical numeric value or drops a required high-severity concept, even if aggregate WER looks good.

## Local-engine benchmark order

After the corpus exists:

1. benchmark the smallest practical offline multilingual candidate first;
2. record model size, peak memory, cold-start/setup time and per-clip latency;
3. only test a larger local model when the smaller candidate fails the accuracy floor;
4. only move to paid/network STT after local candidates are measured or explicitly ruled out.

`sherpa-onnx` with a small multilingual Whisper-family model is an eligible local challenger because it can provide an offline cross-platform execution path, but no model is selected by this protocol. FR/Arabic/Darija quality must be measured on the corpus.

## Repository integration gate

Until valid audio exists, the canonical STT evaluation case may retain `transcript_reference` for semantic design, but `execute_local_stt_benchmark()` must reject it as non-measured evidence.

When fixtures are added, each scored STT case must carry:

```python
input_payload={
    "audio_fixture": "path/to/fixture.wav",
    "audio_sha256": "<64 lowercase hex chars>",
    "transcript_reference": "...",
}
```

The benchmark runner verifies the file and digest before constructing the STT adapter.

## Non-claims

This protocol is not a benchmark result, language validation, clinical validation, provider selection, production cutover, patient-data authorization or CNDP/legal approval.
