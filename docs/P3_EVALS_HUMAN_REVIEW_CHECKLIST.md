# P3-EVALS — Human Review Checklist

Status: REQUIRED BEFORE CLOSEOUT

Use this checklist only after the automated EVALS implementation and post-merge CI are green.

## Required review record

For every reviewed scenario, record:

- reviewer identity;
- review timestamp;
- scenario identifier;
- decision: PASS or FAIL;
- optional note explaining the decision.

## Required dimensions

The review set must cover all four P3-EVALS dimensions:

- LONGITUDINAL;
- NEGATIVE;
- FALSE_POSITIVE;
- BOUNDARY.

## Closeout rule

P3-EVALS cannot be marked CLOSED until:

1. all automated hard scenarios pass;
2. required human-reviewed scenarios have explicit review records;
3. no required human review is missing;
4. the final canonical status is updated only from real review evidence.

A schema, automated test, CI result or generated receipt does not count as human review by itself.
