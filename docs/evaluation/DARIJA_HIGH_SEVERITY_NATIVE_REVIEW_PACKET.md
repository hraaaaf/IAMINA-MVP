# Darija High-Severity Native Review Packet

Status: **WORKING REVIEW PACKET / FAIL-CLOSED / NO RUNTIME APPROVAL**

Date: 2026-08-15  
Locale: Moroccan Darija (`ar-MA`)  
Source branch base: `228b5e5d4e31f219086a02e3a5eddbb660d1a82a`

## Purpose

Review the exact `ar-MA` phrases already present in the deterministic glycemic-emergency gate. This packet does **not** add vocabulary and does **not** change triage behavior.

The machine-readable packet is locked by test to the exact current `ar-MA` runtime inventory. Any runtime inventory drift must break the packet test rather than silently bypassing native review.

## Governance boundary

- Native-language evidence concerns meaning, naturalness, spelling/transliteration and dangerous ambiguity.
- Native evidence is not clinical approval, safety-owner approval or runtime authorization.
- `restricted_approval` remains `false` for every row in this lot.
- Clinical appropriateness of high-severity classification remains a separate restricted review.
- Exact phrase decisions must not be inferred from merely similar phrases.

## Current inventory

- 36 exact `ar-MA` high-severity variants.
- 29 Latin/Arabizi transliterations.
- 7 Arabic-script variants.
- Prior exact native evidence already exists for only three runtime phrases:
  - `غادي يغمى عليا`
  - `كنترعد`
  - `كنرجف`
- The remaining 33 variants require exact review in this packet.

## Review protocol

For each exact phrase, record only one native-evidence outcome:

- `accepted_exact_native_evidence`: natural/understandable enough for the intended meaning, with no unrecorded dangerous ambiguity;
- `rejected_exact_native_evidence`: unnatural, wrong, misleading, ambiguous enough to be unsafe, or not representative;
- leave `pending_exact_review` when uncertain.

When rejecting, preserve the original phrase in the packet and document the reason before any separate runtime-remediation lot. Do not silently rewrite a runtime phrase inside this review lot.

## Review batches

To reduce fatigue and anchoring, review in small semantic groups rather than accepting all variants mechanically:

1. Fall/presyncope forms: `ghadi ntih`, `ghadi ntah`, `ghadi nti7`, `ghadi nte7`, `kantih`, `غادي نطيح`.
2. Consciousness/cognition forms: `fqad l3ql`, `fqdt l3ql`, `fqedt l3a9l`, `f9edt l3a9l`, `f9dt l3ql`, `غادي نغمى عليا`, `غادي يغمى عليا`.
3. Tremor/shivering forms: `tahwid`, `kayrjraj`, `kanrjef`, `kanrjaf`, `kanr3ed`, `kanr3ad`, `rj fou`, `rajef`, `كنترعد`, `كنرجف`.
4. Intolerance/distress wording: `ma kan7ml`, `ma kan7mlch`.
5. Dizziness forms: `dwakht`, `dayakht`, `dwekh`, `dawkhani`.
6. Vision-loss forms: `ma kanchoufch`, `ma kanchofch`, `ma kanchufch`, `ma kanchouf walou`, `ma kanchouf walo`, `ما كنشوفش`, `ما كنشوف والو`.

## Exit condition for this lot

This packet lot can close when every exact runtime `ar-MA` variant has a recorded native-evidence outcome and the packet still matches the exact runtime inventory. That closure still does **not** close the full restricted safety manifest because clinical, safety-owner and parity approvals remain separate gates.
