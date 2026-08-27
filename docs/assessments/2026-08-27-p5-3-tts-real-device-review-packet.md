# P5-3 — Native TTS real-device listening packet

Status: **HUMAN_DEVICE_GATE**. This packet does not certify acoustic adequacy by itself.

## Goal

Collect one reproducible human listening verdict on a current iOS device and one current Android device for IAMINA's native/on-device TTS path.

## Build binding

Before review, record:

- exact app/repo SHA;
- app version/build;
- device model;
- OS version;
- system TTS engine;
- selected voice/locale when exposed.

A review without exact build/device identity is not retained evidence.

## Frozen non-patient fixtures

Use these exact texts. Do not substitute a clinical or patient sentence merely to make a voice sound better.

### FR baseline

`Je suis là avec toi. On peut reprendre simplement demain.`

Expected language/locale: French, neutral patient-facing register.

### MSA baseline

`أنا معك. يمكننا أن نبدأ من جديد ببساطة غداً.`

Expected language/locale: Modern Standard Arabic.

### EN baseline

`I'm here with you. We can restart simply tomorrow.`

Expected language/locale: English.

### Moroccan Darija exploratory lane

`أنا معاك. نقدروا نرجعو ببساطة غدا.`

This lane is **optional / exploratory**. An Arabic system voice reading the characters does not prove Darija support. If pronunciation/register is materially wrong, record `UNQUALIFIED` and keep the lane disabled rather than claiming support.

## Human listening rubric

Score every executed fixture 0 / 1 / 2:

1. intelligibility;
2. pronunciation;
3. number/unit fidelity, when the canonical tested copy contains one;
4. language/register fidelity;
5. pacing;
6. naturalness;
7. emotional neutrality/appropriateness;
8. no omitted/added wording that changes meaning.

For the four fixtures above, `number/unit fidelity` is `N/A`; do not invent a medical numeric sentence to populate it. A later canonical safety fixture may add that check only if its exact upstream wording is already approved.

## Hard failures

Automatic FAIL for the affected device/voice if:

- playback fails, truncates or skips text;
- wording is omitted or added in a way that changes meaning;
- the wrong language/voice makes the message materially misleading;
- FR, MSA or EN baseline becomes unintelligible;
- any future approved numeric/unit fixture is spoken incorrectly.

No average score can override a hard failure.

## Evidence row template

| Field | Value |
| --- | --- |
| Date | |
| Repo SHA | |
| App version/build | |
| Device model | |
| OS version | |
| TTS engine | |
| Voice / locale | |
| Fixture | FR / MSA / EN / Darija |
| Intelligibility 0/1/2 | |
| Pronunciation 0/1/2 | |
| Language/register 0/1/2 | |
| Pacing 0/1/2 | |
| Naturalness 0/1/2 | |
| Emotional appropriateness 0/1/2 | |
| No meaning-changing omission/addition 0/1/2 | |
| Hard failure | yes / no |
| Verdict | PASS / FAIL / UNQUALIFIED |
| Concise note | |

## P5-3 success

P5-3 can close only when:

- one current iOS and one current Android device are reviewed;
- FR + MSA + EN pass hard floors on both retained device lanes;
- every claimed Darija/dialect voice has explicit listening evidence;
- failed or misleading device/voice combinations remain disabled or unqualified;
- evidence is bound to exact build/SHA and device/OS identity.

No patient audio, patient text, provider cutover, CNDP/legal approval or Vercel deployment is implied.
