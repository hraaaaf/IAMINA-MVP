# P0-MENA-2 — Native and clinical safety review

**Status:** executable review package prepared; independent native and clinical approvals remain external.

**Schema version:** `2026-08-04.1`

Canonical real-patient release gate: `docs/P5_6_REAL_PATIENT_RELEASE_GATE.md`.

## 1. Purpose

Automated tests can prove deterministic behavior. They cannot prove that a phrase is natural, unambiguous, culturally appropriate or clinically safe in French, Modern Standard Arabic, English or Moroccan Darija.

The release gate separates:

1. deterministic classifier behavior;
2. exact-phrase native review;
3. clinical severity review;
4. parity review across channel, script and transliteration;
5. exact candidate SHA binding.

All must cover the same fingerprinted corpus and final candidate before real-patient use.

## 2. Corpus composition

The review packet contains representative FR/AR/EN/Darija cases, numeric distress cases, Darija Arabic-script and Latin-transliteration cases, mixed-language and voice-transcript cases, plus every exact high-severity phrase recognized by `core.triage_classification`.

Every reviewable change that modifies the packet fingerprint invalidates the prior manifest.

## 3. Generate the packet

Generate from the code that will become the candidate:

```bash
cd backend
python manage.py export_safety_corpus_review_packet \
  --output /restricted/iamina/safety-review-packet.json
```

The file is written atomically with mode `0600`.

## 4. Reviewer requirements

Each enabled locale requires a qualified native reviewer reference:

- `fr`
- `ar`
- `en`
- `ar-MA`

Every case requires a clinical decision. Every represented locale/channel/input-form tuple requires parity review.

The manifest stores opaque references only. Reviewer names, e-mail addresses and phone numbers must not be placed in Git or the manifest.

Machine or owner self-review does not replace the independent human approvals required by #318/P5-6.

## 5. Restricted manifest

The manifest records:

- exact corpus fingerprint;
- exact full candidate Git SHA;
- review batch reference;
- clinical and safety-owner approval references;
- review/expiry dates;
- locale reviews;
- per-case native and clinical decisions;
- parity decisions.

Only `approved` and `rejected` decisions are accepted. Any rejection blocks the real-patient gate.

The manifest remains outside Git:

```bash
export SAFETY_CORPUS_REVIEW_MANIFEST_PATH=/restricted/iamina/safety-review-manifest.json
```

Example schema:

`docs/examples/safety-corpus-review-manifest.example.json`

## 6. Exact-candidate binding

The release operator supplies:

```bash
export PILOT_RELEASE_SOURCE_SHA=<exact-40-char-git-sha>
```

The approved audit compares this expected SHA with manifest `source_commit_sha`. A correct corpus fingerprint on the wrong candidate SHA is still a STOP.

Any code/configuration change after freeze invalidates the candidate package. Any corpus-affecting change also requires a new packet/fingerprint/review.

## 7. Audit commands

Preparation status:

```bash
cd backend
python manage.py audit_safety_corpus_review
```

Candidate-bound real-patient gate:

```bash
cd backend
python manage.py audit_safety_corpus_review \
  --manifest /restricted/iamina/safety-review-manifest.json \
  --expected-source-sha "$PILOT_RELEASE_SOURCE_SHA" \
  --require-approved
```

The release command fails when:

- expected candidate SHA is missing/malformed;
- manifest candidate SHA differs;
- manifest is missing or stale;
- corpus fingerprint changed;
- locale/case/parity coverage is incomplete, duplicated or unexpected;
- any native, clinical or parity decision is rejected;
- evidence fields expose direct contact data instead of opaque references.

## 8. Change control

After approval, any phrase, severity, locale, channel, input form or normalization change that alters reviewed behavior requires a new packet and review batch.

A candidate SHA change is also a release-gate mismatch even when the corpus fingerprint happens to remain unchanged.

## 9. Closure criteria

The human gate closes only after:

- [ ] final candidate SHA frozen after exact-main CI;
- [ ] all required locale reviews approved;
- [ ] every exact high-severity Darija variant approved;
- [ ] every case has native and clinical approval;
- [ ] all parity rows approved;
- [ ] manifest fingerprint matches the final packet;
- [ ] manifest SHA matches `PILOT_RELEASE_SOURCE_SHA`;
- [ ] evidence current on launch day;
- [ ] candidate-bound safety audit passes.

Engineering preparation does not close the human gate.
