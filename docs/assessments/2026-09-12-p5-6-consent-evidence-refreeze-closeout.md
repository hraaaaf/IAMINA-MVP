# P5-6 consent evidence re-freeze closeout — 2026-09-12

## Goal

Retain proof that PR #591 changed the runtime consent/release boundary, merged cleanly, and therefore required an explicit P5-6 candidate re-freeze before any restricted approval evidence could be accepted.

## Result

Engineering sublot: **CLOSED / MERGED / GREEN**.

P5-6 overall: **ACTIVE / BLOCKED_EXTERNAL / NOT_RELEASE_AUTHORIZED**.

Frozen P5-6 candidate:

`fd3e4a53543e515100b493acc63c99cc9e8464ce`

Previous candidate `a25ec4dd1118784c8968588bab035dca4d0f71b6` is superseded for P5-6 because PR #591 changed runtime consent/release behavior.

## Retained proof

- PR #591 exact head: `b018f724aeaa7b34217cd2810c35e95881332ee1`;
- exact-head CI run #4145 / workflow `34708902735`: SUCCESS;
- exact-head Django migration drift run #3719 / workflow `34708902710`: SUCCESS;
- merge commit: `fd3e4a53543e515100b493acc63c99cc9e8464ce`;
- GitHub merge signature: verified/valid;
- merge tree: `b206837824cd67f05b541efd59336cb358851f21`;
- post-merge CI run #4148 / workflow `34709544750`: SUCCESS;
- post-merge Django migration drift run #3722 / workflow `34709544765`: SUCCESS;
- post-merge P5-5 rehearsal #101: SUCCESS;
- post-merge UI geometry #522: SUCCESS;
- post-merge UI missing-routes #58: SUCCESS;
- post-merge UI browser screenshot #525: SUCCESS.

## Runtime contract retained by candidate

PR #591 retains exact consent notice version/hash/locale evidence, invalidates timestamp-only legacy consent, persists acceptance receipts, clears proof/grants on withdrawal, verifies current consent evidence at outbound-AI egress, separates media grants by consent epoch, keeps Flutter fail-closed on server rejection, and requires local timestamp + verified Secure Storage evidence before local UI consent is considered current.

Notice version: `2026-09-12.1`.

## Safety corpus boundary

PR #591 changed 32 files and did not modify the safety corpus. Therefore the retained safety proof remains:

- 59 exact cases;
- 10 technical parity tuples;
- fingerprint `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`.

No new clinical review claim is created by this closeout.

## Remaining external gates

#318 still requires real restricted qualification/evidence references and a complete safety manifest bound to `fd3e4a53543e515100b493acc63c99cc9e8464ce`.

#320 still requires actual deployment topology, deployment-specific patient notice/consent approval, applicable CNDP evidence, foreign-transfer basis, processor/account evidence and a residency manifest bound to the same candidate.

The three `--require-approved` audits must all pass against that exact candidate before an explicit human release decision.

## Non-claims

This closeout does not claim CNDP/legal authorization, processor approval, production geography, production deployment, Vercel deployment, reviewer credential verification, or permission to process real patient data.

Pilot Readiness remains **4/9 = 44.4%**.

## Next exact action

Re-bind #318, #320 and #514 to frozen candidate `fd3e4a53543e515100b493acc63c99cc9e8464ce`; then obtain the missing restricted/deployment evidence and execute the three exact-SHA approved audits.
