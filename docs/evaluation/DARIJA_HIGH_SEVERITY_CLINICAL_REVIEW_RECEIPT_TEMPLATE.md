# Darija High-Severity Clinical Review Receipt — TEMPLATE

Status: **UNSIGNED / NO CLINICAL APPROVAL**

Issue: #318  
Source packet: `docs/evaluation/DARIJA_HIGH_SEVERITY_CLINICAL_REVIEW_PACKET.md`  
Native-review receipt: `docs/evaluation/DARIJA_HIGH_SEVERITY_NATIVE_REVIEW_RECEIPT.md`  
Remediation plan: `backend/core/tests/fixtures/darija_high_severity_runtime_remediation_plan.json`

## Reviewer evidence

Use opaque references only. Do not commit names, email addresses, phone numbers, credentials, signed documents or private certificates to Git.

- reviewer_reference: `PENDING`
- qualification_reference: `PENDING`
- diabetes_safety_relevance_reference: `PENDING`
- review_date: `PENDING`
- exact_candidate_commit_sha: `PENDING`
- packet_content_sha: `PENDING`
- review_batch_reference: `PENDING`

## Required reviewer assertions

The reviewer must explicitly confirm or reject each assertion:

- [ ] Vocabulary alone never establishes hypoglycemia, hyperglycemia, loss of consciousness or another diagnosis.
- [ ] Fainting/presyncope language is handled conservatively without silently confirming loss of consciousness.
- [ ] Tremor/shivering language is not treated as proof of hypoglycemia without deterministic glucose/safety context.
- [ ] Dizziness remains non-specific and does not establish a glucose state by itself.
- [ ] Vision-loss wording does not silently infer a cause.
- [ ] Distress/intolerance wording does not establish a diagnosis.
- [ ] CGM LOW/HIGH remains an instrumental reading rather than automatic biological confirmation.
- [ ] Sensor failure/disagreement remains an explicit uncertainty state.
- [ ] Medication uncertainty never becomes confirmed administration, insulin advice or dose recommendation.
- [ ] Fixed emergency responses do not delay urgent care and stay inside the documented SELF_CARE_ONLY/emergency boundary.

## Decision on the 21 native-rejected runtime variants

Allowed values per row: `REMOVE_APPROVED`, `KEEP_PENDING`, `CLINICAL_FINDING`.

| # | Exact token | Decision | Finding / evidence reference |
|---:|---|---|---|
| 1 | `ghadi ntah` | PENDING | |
| 2 | `kantih` | PENDING | |
| 3 | `fqad l3ql` | PENDING | |
| 4 | `fqdt l3ql` | PENDING | |
| 5 | `fqedt l3a9l` | PENDING | |
| 6 | `f9edt l3a9l` | PENDING | |
| 7 | `f9dt l3ql` | PENDING | |
| 8 | `tahwid` | PENDING | |
| 9 | `kayrjraj` | PENDING | |
| 10 | `kanr3ed` | PENDING | |
| 11 | `kanr3ad` | PENDING | |
| 12 | `rj fou` | PENDING | |
| 13 | `rajef` | PENDING | |
| 14 | `ma kan7ml` | PENDING | |
| 15 | `dwakht` | PENDING | |
| 16 | `dayakht` | PENDING | |
| 17 | `dwekh` | PENDING | |
| 18 | `dawkhani` | PENDING | |
| 19 | `ma kanchoufch` | PENDING | |
| 20 | `غادي نغمى عليا` | PENDING | |
| 21 | `غادي يغمى عليا` | PENDING | |

Reviewer question for every removal: does removal avoid a clinically meaningful loss of necessary high-severity detection, considering the accepted forms and any separately approved replacement?

## Decision on native replacement candidates

Allowed values: `APPROVE_FOR_SAFETY_REVIEW_CONTINUATION`, `REJECT_CLINICALLY`, `REQUIRES_NARROWER_CONTEXT`.

| Candidate | Intended group | Decision | Finding / evidence reference |
|---|---|---|---|
| `ghadi nskhef` | consciousness / fainting | PENDING | |
| `غادي نسخف` | consciousness / fainting | PENDING | |
| `kantr33d` | tremor / shivering | PENDING | |
| `Ddokha` → runtime candidate `ddokha` | dizziness | PENDING | |

## Unresolved clinical findings

- `NONE RECORDED` / replace with opaque issue references.

## Overall clinical result

Choose exactly one:

- [ ] `PASS`
- [ ] `PASS_WITH_REQUIRED_CHANGES`
- [ ] `FAIL`

clinical_approval_reference: `PENDING`

## Important boundary after PASS

A signed clinical PASS is necessary but not sufficient for runtime promotion. Safety-owner approval, cross-channel/input-form parity approval, exact safety-corpus fingerprint matching, ambiguity/hyperbole/context regression evidence and explicit `approved_for_runtime` authorization remain separate fail-closed gates.

This template itself carries **no approval**.
