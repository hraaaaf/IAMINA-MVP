# P5-1 Morocco linguistic remediation

## Trigger
Exact-main v7 packet reached retained human review. The human reviewer accepted the overall direction but corrected two Morocco Darija formulations.

## Retained exact-main v7 evidence
- run #34659978472 SUCCESS on `de5faf68e2139a9842b3b6bead20e0a1a78e4b87`
- artifact #10287096700
- digest `sha256:348763fdcfbb2d3b39440a9bdcf3c5cf088f3ee62b51550941e662e561e23cf7`
- synthetic only, no patient data

## Retained human findings
- Darija Arabic: prefer `ما تقلقش، غدا تقدر ترجع بلا ضغط.` over `ما تشدش، غدا تقدر ترجع بلا ضغط.`
- Darija Latin: prefer direct second-person wording such as `Mashi mouchkil, ghdda t9der terja3 bla daght.` over first-person-plural `...nrj3...`

## v8 remediation
- keep the v7 MSA/no-pressure/safety constraints;
- reject `ما تشدش` in the Darija Arabic lane;
- reject `nrj3` in the Darija Latin lane;
- require explicit second-person ability-to-resume wording (`t9der/t9dar` + return verb) in Darija Latin;
- remove `nrje3` from the Darija Latin synthetic source prompt so the benchmark no longer seeds the rejected form;
- bind the retained report identity explicitly to dataset `iamina-p5-1-current-sha-linguistic-review-v8`;
- keep exact-SHA binding and one bounded provider call.

The first v8 exact-head run #34660826264 failed only the Darija Latin retained-human-feedback check and also exposed a report identity bug (`dataset_id` still v7). CI and migration on that SHA were green. Both root causes are corrected in the next exact-head attempt.

This document records engineering rationale and retained human feedback only. It is not clinical, CNDP, legal, provider, deployment, or real-patient approval.
