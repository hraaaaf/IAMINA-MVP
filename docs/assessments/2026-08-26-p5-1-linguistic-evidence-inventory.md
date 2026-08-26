# P5-1 — retained linguistic evidence inventory

Date: 2026-08-26
Tracks: #515, #514, #319

## Purpose

Inventory the synthetic outputs already retained and identify exactly what can be handed to a human reviewer now versus what still needs a current-SHA controlled generation run.

This file is not a native-speaker certification.

## Current product baseline

Current product main before this documentation PR: `49f582fb619ad6cf441fb1c4cfd893b38c4c84b6`.

Companion exact-head controlled evidence from candidate `cb8248c83c8ea30818e31e499926e6800acb9dfd`:
- quality artifact: `iamina-companion-quality`, artifact id `9615230530`;
- synthetic/non-patient: yes;
- route mix: `2 safety / 7 zero_model / 1 llm`;
- machine gate: PASS;
- manual engineering audit: 9.3/10;
- only one provider-routed LLM turn in that 10-turn transcript.

### Retained French / Darija-Latin examples

French practical response:

> Commence par un seul repère : un rappel à heure fixe et une case à cocher. Si tu oublies, reprends simplement au rappel suivant.

French emotional response:

> Je comprends à quel point ça peut être épuisant de porter ce poids au quotidien.

French clinician-preparation response:

> Prépare ces 4 questions :
> - Quelles informations dois-je apporter ?
> - Quels changements dois-je vous signaler ?
> - Quels critères utilisez-vous pour réévaluer mon traitement ?
> - Quand dois-je vous recontacter ?

Darija Latin/Arabizi response:

> Bda b 7aja wa7da: reminder wa7ed f wa9t tabet, w case wa7da t3ellem 3liha. Ila nsiti, kmml m3a reminder li b3do.

These are suitable as reviewer seed material. Final P5-1 certification must still bind its verdict to the exact reviewed SHA/corpus.

## Retained Gulf product-prompt artifact

Run `32779489464`, head `ec057a90e725a0881cd2b54a05f75dc98252c6e4`.
Artifact `9539217548`, name `frug5-product-prompt-gulf`, digest `sha256:1feb7796e766b61e0c91232edb8af97fc45c5b3d1b63211ad293a71100125871`.

The artifact explicitly records:
- provider: Groq;
- model: `openai/gpt-oss-120b`;
- dataset: `iamina-frug5-product-prompt-gulf-v1`;
- synthetic: true;
- patient_data: false;
- 5/5 machine gate PASS;
- `human_linguistic_review.required = true`;
- `human_linguistic_review.status = pending`.

### Saudi / `ar-SA`

> أفهم إنك مرّيت بيوم صعب، بس بعودتك للروتين بكرة خطوة بسيطة تقدر تخليها سهلة ومريحة. أنا واثق إنك تقدر تسويها!

### Emirati / `ar-AE`

> أفهم إنك حاسس بضغط، لكن خطوة بسيطة غداً تساوي كثير. أنا واثق إنك تقدر تسترجع روتينك بسهولة.

### Kuwaiti / `ar-KW`

> أفهم إنك حسّيت اليوم صعب، بس إن شاء الله بكرة ترجع للروتين خطوة بخطوة. أنا معاك!

### Qatari / `ar-QA`

> أفهم شعورك، خطوة بسيطة بكرة ممكن ترجعك على الروتين. أنا واثقة إنك تقدر تسويها!

### Omani / `ar-OM`

> ما يهم، كلنا مرات نتوقف. خذ خطوة بسيطة بكرة، وأنا معاك!

Prior engineering review already noted that Qatar/Oman were less dialect-marked than Saudi/Emirati/Kuwaiti. That is not a native-speaker verdict.

## Coverage inventory

| Lane | Retained human-readable output exists | Current-SHA certification-ready | Status |
|---|---|---|---|
| French | Yes | Seed only; exact reviewed SHA still required | REVIEWABLE |
| MSA | No dedicated current review pack | No | MISSING_CORPUS |
| Darija Arabic script | No dedicated current review pack | No | MISSING_CORPUS |
| Darija Latin/Arabizi | Yes | Seed only; exact reviewed SHA still required | REVIEWABLE |
| FR ↔ Darija code-switch | Context-window fixture exists, but no retained current human-review response identified | No | MISSING_CORPUS |
| Saudi | Yes, retained historical controlled output | Historical seed only | REVIEWABLE_SEED |
| Emirati | Yes, retained historical controlled output | Historical seed only | REVIEWABLE_SEED |
| Kuwaiti | Yes, retained historical controlled output | Historical seed only | REVIEWABLE_SEED |
| Qatari | Yes, retained historical controlled output | Historical seed only | REVIEWABLE_SEED |
| Omani | Yes, retained historical controlled output | Historical seed only | REVIEWABLE_SEED |

## Exact remaining execution gate

P5-1 cannot close from the retained artifacts alone. Before final human certification, a single controlled current-SHA linguistic corpus must be frozen across all ten lanes and presented to competent reviewers using `2026-08-26-p5-1-mena-linguistic-review-protocol.md`.

Generating any missing provider-backed responses is a network/provider benchmark action and remains subject to the explicit authorization/spend boundary in #319. Until that gate is intentionally opened, retained outputs may be reviewed as seed evidence but must not be promoted to current product certification.

No patient data, provider cutover, legal/CNDP approval or Vercel deployment is claimed.