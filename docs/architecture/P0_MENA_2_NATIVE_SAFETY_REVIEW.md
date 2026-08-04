# P0-MENA-2 — Native and clinical safety review

**Status:** executable review package prepared; native and clinical approvals remain external.

**Schema version:** `2026-08-04.1`

## 1. Purpose

Automated tests can prove deterministic behavior. They cannot prove that a phrase is natural, unambiguous, culturally appropriate or clinically safe in French, Modern Standard Arabic, English or Moroccan Darija.

This gate separates four kinds of evidence:

1. deterministic classifier behavior;
2. exact-phrase native review;
3. clinical severity review;
4. parity review across channel, script and transliteration.

All four must cover the exact same fingerprinted corpus before a real-patient pilot.

## 2. Corpus composition

The review packet contains:

- representative text cases for FR, AR, EN and Darija;
- representative numeric distress cases;
- Darija Arabic-script cases;
- Darija Latin transliteration cases;
- mixed-language cases;
- voice-transcript cases;
- every exact French, Arabic and Darija high-severity phrase currently recognized by `core.triage_classification`.

The exact variant inventory is exposed by:

```python
core.triage_classification.glycemic_emergency_variant_inventory()
```

Every variant becomes a stable corpus case whose ID is derived from locale, input form and phrase content. A phrase addition, removal or change modifies the packet fingerprint and invalidates previous manifests.

## 3. Generate the packet

```bash
cd backend
python manage.py export_safety_corpus_review_packet \
  --output /restricted/iamina/safety-review-packet.json
```

The file is written atomically with mode `0600`.

The packet contains synthetic phrases only, but the restricted location prevents accidental edits, partial reviewer copies and uncontrolled review versions.

## 4. Reviewer requirements

### Native-language review

Each enabled locale requires one qualified native reviewer reference:

- `fr`
- `ar`
- `en`
- `ar-MA`

The manifest stores opaque references only. Reviewer names, e-mail addresses and phone numbers must not be placed in Git or in the manifest.

The native reviewer assesses:

- intended meaning;
- naturalness;
- ambiguity;
- spelling and orthographic variation;
- whether the phrase is plausibly used in the target locale;
- whether a false positive could be dangerous.

### Clinical review

Every case requires a clinical decision confirming whether the expected high-severity classification is appropriate. A global clinical approval reference and a per-case decision are both required.

### Parity review

Every tuple represented by the corpus requires explicit review:

- locale;
- channel (`text` or `voice_transcript`);
- input form (`native_script`, `arabic_script`, `latin_transliteration`, `mixed_language`, `numeric`).

The manifest cannot omit a channel or input form that exists in the packet.

## 5. Restricted manifest

The manifest records:

- exact corpus fingerprint;
- exact full Git SHA reviewed;
- review batch reference;
- global clinical and safety-owner approval references;
- review and expiry dates;
- one locale review per required locale;
- one native and clinical decision per case ID;
- one parity decision per required locale/channel/input-form tuple.

Only `approved` and `rejected` decisions are accepted. A rejected decision may carry an opaque issue reference. Any rejection blocks the pilot gate.

The manifest must remain outside Git. A deliberately incomplete schema example is stored at:

`docs/examples/safety-corpus-review-manifest.example.json`

It is not valid approval evidence.

Configure only the restricted path:

```bash
export SAFETY_CORPUS_REVIEW_MANIFEST_PATH=/restricted/iamina/safety-review-manifest.json
```

## 6. Audit commands

Preparation status, expected to remain pending without a restricted manifest:

```bash
cd backend
python manage.py audit_safety_corpus_review
```

Real-patient release gate:

```bash
cd backend
python manage.py audit_safety_corpus_review \
  --manifest /restricted/iamina/safety-review-manifest.json \
  --require-approved
```

The release command fails when:

- the manifest is missing or stale;
- the corpus fingerprint changed;
- the reviewed Git SHA is not a full SHA;
- any locale is missing or duplicated;
- any exact case is missing, duplicated or unexpected;
- any parity dimension is missing, duplicated or unexpected;
- any native, clinical or parity decision is rejected;
- a reviewer or evidence field contains direct contact data instead of an opaque reference.

## 7. Change control

After approval, any of the following requires a new packet and review batch:

- adding or deleting a classifier phrase;
- changing spelling or punctuation of a reviewed phrase;
- changing expected severity;
- adding a locale, channel or input form;
- changing normalization behavior in a way that alters case interpretation.

The fingerprint gate prevents a stale approval from silently surviving those changes.

## 8. Roadmap closure criteria

The three remaining P0-MENA-2 human gates can close only after:

- [ ] all four locale reviews are approved;
- [ ] every exact high-severity Darija variant is approved;
- [ ] every case has native and clinical approval;
- [ ] all channel/script/transliteration parity rows are approved;
- [ ] the manifest fingerprint matches the current packet;
- [ ] evidence is current on pilot launch day;
- [ ] `audit_safety_corpus_review --require-approved` passes.

Engineering preparation does not close these human gates.
