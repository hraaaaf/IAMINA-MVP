# P0-MENA-2 / #318 — Darija high-severity AI clinical pre-review

Status: **AI PRE-REVIEW ONLY / NOT QUALIFIED-HUMAN APPROVAL / NOT RUNTIME AUTHORIZATION**

Date: 2026-08-18  
Issue: #318  
Candidate branch: `fix/mena-318-clinical-review-readiness-v2`

## Goal

Reduce the qualified-human review burden by separating low-risk native-rejected removals from removals that could create a clinically meaningful detection-coverage gap unless an approved replacement is promoted atomically.

## Clinical basis

The 2026 ADA Standards define level 3 hypoglycemia by altered mental and/or physical functioning requiring assistance from another person, irrespective of glucose level. They list symptoms such as shakiness and confusion, and note progression of severe events to loss of consciousness, seizure, coma or death. CDC guidance also lists shaking, dizziness, confusion, difficulty seeing and fainting among possible manifestations of worsening low glucose.

These references support the existing IAMINA boundary: symptom vocabulary is relevant safety evidence but cannot independently establish hypoglycemia or another diagnosis.

References checked 2026-08-18:

- ADA Professional Practice Committee. *6. Glycemic Goals, Hypoglycemia, and Hyperglycemic Crises: Standards of Care in Diabetes—2026*. Diabetes Care 2026;49(Suppl. 1):S132–S149. DOI 10.2337/dc26-S006.
- CDC. *Low Blood Sugar (Hypoglycemia)*. https://www.cdc.gov/diabetes/about/low-blood-sugar-hypoglycemia.html

## Pre-review decisions

These are recommendations to the qualified reviewer, not approvals.

### A. Removal appears coverage-preserving from the current native-reviewed set

Recommended human decision: `REMOVE_APPROVED`, subject to verifying the deterministic fixed-response behavior.

| Rejected token(s) | Semantic group | Why coverage appears preserved |
|---|---|---|
| `ghadi ntah`, `kantih` | fall / presyncope | accepted `ghadi ntih`, `ghadi nti7`, `ghadi nte7`, `غادي نطيح` remain |
| `tahwid`, `kayrjraj`, `kanr3ed`, `kanr3ad`, `rj fou`, `rajef` | tremor / shivering | accepted `kanrjef`, `kanrjaf`, `كنترعد`, `كنرجف` remain |
| `ma kan7ml` | distress / intolerance | accepted `ma kan7mlch` remains |
| `ma kanchoufch` | vision difficulty/loss wording | accepted `ma kanchofch`, `ma kanchufch`, `ma kanchouf walou`, `ma kanchouf walo`, `ما كنشوفش`, `ما كنشوف والو` remain |

### B. Do not remove without an atomic approved replacement or explicit clinical decision that the semantic group is not required

Recommended human decision: `KEEP_PENDING` until the replacement/cutover condition is satisfied.

| Rejected token(s) | Semantic group | Coverage risk |
|---|---|---|
| `fqad l3ql`, `fqdt l3ql`, `fqedt l3a9l`, `f9edt l3a9l`, `f9dt l3ql`, `غادي نغمى عليا`, `غادي يغمى عليا` | consciousness / fainting | native review rejected every proposed runtime form in this group; `ghadi nskhef` / `غادي نسخف` are only pending candidates. `ghadi nti7` must not be silently reinterpreted as loss of consciousness. |
| `dwakht`, `dayakht`, `dwekh`, `dawkhani` | dizziness | native review rejected all current runtime forms; `Ddokha` → `ddokha` is pending. Removing all without a replacement may eliminate the group's lexical coverage. |

## Replacement candidate recommendations

Again, these are pre-review recommendations only.

| Candidate | AI pre-review recommendation | Reason |
|---|---|---|
| `ghadi nskhef` | `APPROVE_FOR_SAFETY_REVIEW_CONTINUATION` | provides direct fainting/presyncope-style safety language, but must not equal a diagnosis of actual loss of consciousness |
| `غادي نسخف` | `APPROVE_FOR_SAFETY_REVIEW_CONTINUATION` | Arabic-script counterpart; same clinical boundary |
| `kantr33d` | `APPROVE_FOR_SAFETY_REVIEW_CONTINUATION` | tremor/shivering is relevant symptom language, but never proof of hypoglycemia |
| `Ddokha` → `ddokha` | `REQUIRES_NARROWER_CONTEXT` | dizziness is non-specific; safest promotion requires explicit context/behavior tests proving it cannot establish a glucose state alone |

## Required human checks before any PASS

1. Confirm that every proposed `REMOVE_APPROVED` token has a semantically adequate accepted form still active.
2. For consciousness/fainting, require atomic replacement promotion or explicitly document why direct lexical coverage is not required.
3. For dizziness, decide whether the high-severity detector should recognize isolated dizziness at all; if yes, require the approved native replacement plus contextual ambiguity tests.
4. Confirm no symptom-only match becomes a hypoglycemia diagnosis.
5. Confirm emergency escalation remains conservative and does not delay urgent care when the user's state is unresponsive/unable to self-treat.
6. Confirm no treatment, dose, correction factor or insulin instruction is introduced.

## Result

AI pre-review result: **READY_FOR_QUALIFIED_HUMAN_REVIEW_WITH_TWO_COVERAGE_WARNINGS**.

Coverage warnings:

- consciousness/fainting group: do not atomically remove all rejected forms before a replacement/coverage decision;
- dizziness group: do not atomically remove all rejected forms before a replacement/coverage decision.

No clinical-human, safety-owner, parity or runtime approval is claimed.
