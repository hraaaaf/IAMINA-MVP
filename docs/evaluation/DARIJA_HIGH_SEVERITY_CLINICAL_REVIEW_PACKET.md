# Darija High-Severity Clinical Review Packet

Status: **READY FOR QUALIFIED HUMAN CLINICAL REVIEW / NO APPROVAL RECORDED**

Date prepared: 2026-08-17  
Locale: Moroccan Darija (`ar-MA`)  
Native review source: `docs/evaluation/DARIJA_HIGH_SEVERITY_NATIVE_REVIEW_RECEIPT.md`  
Remediation plan: `backend/core/tests/fixtures/darija_high_severity_runtime_remediation_plan.json`  
Reviewed runtime baseline: `b8cf00076b1e84562a460b08221a5ceb3178dc81`

## Purpose

Provide a bounded worksheet for the qualified clinical-human review still required by P0-MENA-2 and the Darija lexicon runtime-promotion contract.

This packet does not approve any runtime change. It exists so the remaining clinical gate can be performed against the exact native-reviewed delta rather than an informal conversation.

## Reviewer qualification requirement

Reviewer must be a qualified healthcare professional familiar with diabetes safety communication and able to verify that deterministic detection/fixed responses:

- do not diagnose from vocabulary alone;
- do not prescribe or optimize treatment;
- do not delay urgent-care escalation when clinically appropriate;
- do not convert ambiguity into a confirmed biological state;
- preserve the product's self-care-only/emergency governance boundary.

A controlled reviewer identifier may be used instead of public personal details.

## Native-reviewed delta

### Existing runtime variants accepted by native review

These remain unchanged by the staged remediation:

- `ghadi ntih`
- `ghadi nti7`
- `ghadi nte7`
- `غادي نطيح`
- `kanrjef`
- `kanrjaf`
- `كنترعد`
- `كنرجف`
- `ma kan7mlch`
- `ma kanchofch`
- `ma kanchufch`
- `ma kanchouf walou`
- `ma kanchouf walo`
- `ما كنشوفش`
- `ما كنشوف والو`

### Existing runtime variants rejected by native review

The remediation plan contains 21 exact variants to remove atomically if the complete promotion gate later passes:

1. `ghadi ntah`
2. `kantih`
3. `fqad l3ql`
4. `fqdt l3ql`
5. `fqedt l3a9l`
6. `f9edt l3a9l`
7. `f9dt l3ql`
8. `tahwid`
9. `kayrjraj`
10. `kanr3ed`
11. `kanr3ad`
12. `rj fou`
13. `rajef`
14. `ma kan7ml`
15. `dwakht`
16. `dayakht`
17. `dwekh`
18. `dawkhani`
19. `ma kanchoufch`
20. `غادي نغمى عليا`
21. `غادي يغمى عليا`

Clinical review question: **Does removing each rejected variant avoid a clinically meaningful loss of necessary high-severity detection that is not adequately covered by remaining/approved language?**

### Native replacement candidates, not runtime-authorized

| Candidate | Input form | Intended semantic group | Clinical decision |
|---|---|---|---|
| `ghadi nskhef` | Latin transliteration | consciousness / fainting | PENDING |
| `غادي نسخف` | Arabic script | consciousness / fainting | PENDING |
| `kantr33d` | Latin transliteration | tremor / shivering | PENDING |
| `Ddokha` → proposed runtime token `ddokha` | Latin transliteration | dizziness | PENDING |

For each candidate, reviewer must record one of:

- `APPROVE_FOR_SAFETY_REVIEW_CONTINUATION`
- `REJECT_CLINICALLY`
- `REQUIRES_NARROWER_CONTEXT`

This is not the final `approved_for_runtime` decision. Safety-owner and restricted parity gates remain separate.

## Evidence-based clinical pre-review

This section is **AI-assisted preparation only**, not the required qualified-human verdict.

Current ADA Standards of Care in Diabetes—2026 define level 3 hypoglycemia as an event with altered mental and/or physical functioning requiring assistance from another person, irrespective of glucose level. The same standards list shakiness and confusion among possible hypoglycemia symptoms and note that severe hypoglycemia can progress to loss of consciousness, seizure, coma, or death. CDC patient guidance likewise lists shaking, dizziness, confusion, difficulty seeing and fainting among possible manifestations of worsening low blood glucose.

Clinical consequence for this packet:

- symptom vocabulary such as tremor, dizziness or vision difficulty is clinically relevant for safety detection, but **must not by itself establish hypoglycemia**;
- fainting/presyncope language warrants conservative safety handling but must not be converted into a confirmed loss-of-consciousness diagnosis;
- removal of native-rejected spellings is acceptable only if the remaining accepted forms and/or separately approved replacements preserve adequate high-severity coverage;
- all four replacement candidates remain suitable only for safety-review continuation, not automatic runtime authorization, until a qualified reviewer confirms meaning and the safety/parity gates pass.

Primary clinical references checked 2026-08-18:

- American Diabetes Association Professional Practice Committee for Diabetes. *6. Glycemic Goals, Hypoglycemia, and Hyperglycemic Crises: Standards of Care in Diabetes—2026*. Diabetes Care 2026;49(Suppl. 1):S132–S149. DOI: 10.2337/dc26-S006.
- U.S. Centers for Disease Control and Prevention. *Low Blood Sugar (Hypoglycemia)*, current public guidance accessed 2026-08-18.

## Mandatory semantic checks

Reviewer must explicitly verify:

1. Fainting/presyncope wording does not become a diagnosis of loss of consciousness.
2. Tremor/shivering wording is not treated as proof of hypoglycemia without deterministic glucose/safety context.
3. Dizziness wording is non-specific and must not establish a glucose state by itself.
4. Vision-loss wording does not silently infer cause.
5. Distress/intolerance wording is not enough by itself to trigger a clinical diagnosis.
6. CGM LOW/HIGH readings remain instrumental readings, not automatically biologically confirmed states.
7. Device/sensor failure and sensor/symptom disagreement remain explicit uncertainty states.
8. Medication uncertainty is never converted into confirmed insulin administration or a dose recommendation.
9. No candidate authorizes diagnosis, prescription, dose calculation, correction factor, insulin advice or treatment optimization.
10. Emergency fixed responses must not delay urgent care and must remain inside the documented operating mode.

## Required evidence receipt

Controlled review evidence must record:

- reviewer identifier;
- healthcare qualification and diabetes-safety relevance;
- review date;
- exact baseline SHA and packet version;
- decision for all 21 removals as a set or individually where needed;
- decision for each of the four replacement candidates;
- unresolved clinical findings;
- explicit overall result: `PASS`, `PASS_WITH_REQUIRED_CHANGES`, or `FAIL`.

## Gates after clinical PASS

A clinical PASS alone does not authorize runtime promotion. Remaining requirements include:

- safety-owner evidence reference;
- restricted cross-channel/input-form parity approval;
- exact current safety-corpus fingerprint;
- positive, negative, contextual, hyperbole and ambiguity regression evidence;
- explicit `approved_for_runtime` decision;
- atomic implementation and exact-head recertification.

## Current state

The packet now matches the native-review outcome fixture for the accepted/rejected token split, including `ma kanchoufch` as **rejected**. No clinical-human approval is recorded by this document. Runtime remains unchanged and fail-closed.
