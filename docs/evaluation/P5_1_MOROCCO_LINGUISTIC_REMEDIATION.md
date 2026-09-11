# P5-1 Morocco linguistic pre-human remediation

Status: PRE_HUMAN_REMEDIATION_REQUIRED

Frozen packet candidate reviewed: `db7531d8ee862eb9a3b0249fbee8abecd31ea27c`
Exact-main packet run: `#34654142883`
Artifact: `#10284573280`
Digest: `sha256:811b99c22216b49a727e81c38d792bc86bfd1bf32928c5d5e382c2a01ae6ad88`

## Goal
Remove obvious linguistic defects before spending a retained native/competent human review on the five Morocco pilot lanes.

## Observed outputs

1. French: `Demain, tu peux le faire, tu es capable.`
   - Pre-audit: acceptable candidate; no hard failure identified.

2. MSA: `غداً تستطيع ذلك، أنت قوي.`
   - Pre-audit: needs revision before certification because `قوي` is masculine-gendered and the product has no user-gender basis for selecting it.

3. Moroccan Darija, Arabic script: `غدا تقدر تديرها، راه ساهلة.`
   - Pre-audit: needs revision because `راه ساهلة` can trivialize the user's difficulty and conflicts with the non-patronizing review dimension.

4. Moroccan Darija, Latin/Arabizi: `Ghdda t9dar, nti qawi.`
   - Pre-audit: FAIL candidate. `nti` is feminine while `qawi` is masculine; the phrase is internally inconsistent and gender-selective.

5. FR↔Darija code-switching: `Demain t9dar, tu es قوي.`
   - Pre-audit: FAIL candidate. The code-switch is unnatural and combines French, Arabizi and Arabic-script Darija in one short sentence despite the intended French-Latin + Darija-Arabic lane contract.

## Required remediation contract

Before retained human certification:

- avoid gender-selective pronouns/adjectives unless user gender is explicitly and lawfully available for that purpose;
- avoid strength/capability clichés that become gendered in Arabic/Darija;
- avoid claims that the task is easy/simple when the user expressed difficulty;
- for FR↔Darija, use phrase-level natural code-switching with French in Latin script and Darija in Arabic script;
- reject Arabizi digits in the FR↔Darija lane;
- require at least two French-script words and at least two Arabic-script words in that mixed lane;
- retain deterministic medical/safety boundaries unchanged;
- keep the human reviewer as final linguistic authority.

## Success
A new exact-SHA packet must pass machine checks and no longer reproduce the defects above. Only then should the five Morocco lanes be sent to retained native/competent human scoring.

This document is engineering pre-audit evidence only. It is not native-speaker certification, clinical approval, CNDP/legal approval, or release authorization.
