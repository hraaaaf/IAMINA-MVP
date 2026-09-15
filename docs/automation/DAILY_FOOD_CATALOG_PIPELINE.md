# IAMINA Daily Food Catalog Pipeline

Status: ACTIVE PROTOCOL — human merge required

## Goal

Continuously enrich the IAMINA FoodPicker catalog with a small number of culturally verified MENA foods every day, without degrading catalog quality, historical ordering, UI clarity, or validated behavior.

## Observable success

A daily run is successful only when it produces either:

1. a verified PR containing a coherent new food batch with all required evidence; or
2. an explicit no-op / blocked report explaining why no safe batch should be created that day.

A run is never successful merely because candidates were generated.

## Daily cadence

Target: 1 run per day.

Default batch size: 3–6 new food concepts.

Do not create a second concurrent food-catalog batch while a previous food-catalog PR is still open, failing, awaiting remediation, or awaiting human merge approval. Continue the existing lot first.

## Geographic strategy

Prioritize real catalog gaps rather than arbitrary novelty.

Default expansion order:

1. Morocco depth and regional coverage
2. Gulf / GCC depth
3. Maghreb outside Morocco
4. Levant
5. Egypt / Sudan
6. other MENA regional foods with clear provenance

The order may change when the existing catalog already has strong coverage in one area and a documented gap elsewhere.

## Candidate acceptance gate

Every candidate must pass all gates below before implementation:

- not already represented by an existing food concept, alias, transliteration, or near-synonym;
- meaningful enough to be selected independently by a user;
- culturally/provenance verified by at least 2 serious sources;
- primary or official sources preferred whenever available;
- provenance not materially disputed or ambiguous;
- category assignment verified;
- clean FR / EN / AR labels available;
- no trademark-dependent naming when a generic food concept is more appropriate.

If provenance remains ambiguous after verification, reject the candidate for that run.

## Source policy

Minimum: 2 serious sources per food concept or tightly related regional group.

Preferred hierarchy:

1. official tourism, ministry, cultural authority, government, national culinary institution;
2. recognized academic, museum, heritage, institutional or major reference source;
3. established specialist or major publication as supporting evidence.

Do not certify provenance from a single recipe blog, marketplace, social-media post, SEO list, or generative answer.

Record source URLs and the exact claim they support in the lot handover / PR.

## Data and naming rules

Each accepted concept must define:

- stable ID;
- French label;
- English label;
- Arabic label;
- MealFoodCategory;
- regional/provenance note when useful;
- visual/pictogram route.

Do not silently recategorize existing foods as part of a daily append batch unless a demonstrated defect requires it.

Cuisine-specific categories must remain semantically clear. In particular, Gulf foods must not visually appear to belong to Cuisine marocaine, and vice versa.

## Append-only / non-regression policy

Daily batches should be append-only whenever possible.

Preserve the previously certified catalog entries and ordering byte-for-byte where the architecture allows it.

Do not modify backend, patient data, database schema, CGM logic, medication logic, documents, authentication, or unrelated UI in a food-catalog batch.

Any required refactor must be minimal, documented, and separately justified.

## Pictogram policy

Every added concept must receive a native FoodPicker pictogram through the current painter architecture.

Generic fallback is not an acceptable final representation for an accepted daily concept.

Pictograms must remain visually distinguishable at the FoodPicker rendering size and should reflect the concept without relying on text inside the art.

## Required tests

At minimum, each batch must prove:

- expected catalog count delta;
- unique IDs;
- previous certified baseline remains intact;
- previous batch ordering remains intact;
- new IDs are searchable;
- FR / EN / AR serialization/labels are present;
- new IDs route to native pictograms;
- full catalog visual-contract coverage remains complete;
- category behavior is correct;
- any regression discovered during certification gets a dedicated test before re-certification.

## UI / UX certification

For any FoodPicker visual impact:

BEFORE → written Goal → implementation → AFTER using the same viewports.

Required viewports:

- 390×844
- 768×1024
- 1280×900

Inspect the FoodPicker fixture/query that exposes the new concepts.

Verify:

- correct active category state;
- no misleading category association;
- no overflow;
- no clipping;
- no collisions;
- readable labels;
- pictograms visibly distinct;
- responsive behavior consistent with the certified baseline.

## Required gates

For FoodPicker-impacting batches, the standard certification set is:

- CI
- P5-5 End-to-End Pilot Rehearsal
- UI geometry golden audit (Ahem text)
- UI browser screenshot certification

Additional gates may be required when the diff crosses another subsystem.

Do not reuse green evidence from an older HEAD after any commit changes the candidate HEAD.

## Artifact integrity

For UI browser certification:

- fetch the exact-head artifact;
- compare the locally computed ZIP SHA256 with the GitHub artifact digest;
- inspect the actual generated screenshots;
- retain the artifact ID, digest, query/fixture and visual observations in the evidence.

## Branch and PR contract

One daily lot = one dedicated branch / PR.

The PR must contain:

- Goal;
- exact before/after catalog count;
- accepted food concepts;
- rejected candidates when rejection is informative;
- source evidence;
- non-regression proof;
- exact HEAD SHA;
- gate run IDs and conclusions;
- screenshot artifact ID + SHA256;
- visual score / findings;
- explicit merge status.

## Human gate

NEVER auto-merge a daily food PR.

Human approval is mandatory after the user has been shown the principal certified screenshot and the exact evidence state.

After human approval, merge may proceed only if:

- the PR HEAD is unchanged;
- main has not introduced an unsafe conflict/drift;
- required gates are green;
- review threads/blockers are clear.

## Main drift handling

If main moves while a batch is under certification:

1. determine whether the new main changes any touched path or baseline contract;
2. rebuild/rebase the batch safely on current main when necessary;
3. preserve unrelated incoming changes;
4. re-run exact-head certification;
5. never merge a stale certified HEAD merely because its previous gates were green.

## Post-merge closeout

After merge:

1. verify main points to the merge result;
2. inspect post-merge workflows once;
3. if pending, perform any independent closeout work;
4. if no independent work remains, report the exact asynchronous block instead of polling;
5. once green, update the canonical handover/roadmap state to the real verified status.

## Stop / no-op conditions

Do not force a batch when quality is insufficient.

A daily run should stop without a PR when:

- fewer than 3 good non-duplicate candidates pass provenance gates;
- credible sources disagree materially;
- an earlier food PR still requires work;
- main is unstable in a way that makes a new batch unsafe;
- required evidence cannot be obtained reliably.

A no-op with evidence is better than low-quality catalog growth.

## Deployment

No Vercel deployment is part of this pipeline unless explicitly authorized by the user.

## Daily report format

Result → proof → next action.

Always report known values only:

- lot / geographic theme;
- Goal;
- before/after count;
- repo / branch / PR / HEAD;
- gate runs + state;
- screenshot artifact + digest when available;
- real blocker;
- Next exact;
- remaining sequence.
