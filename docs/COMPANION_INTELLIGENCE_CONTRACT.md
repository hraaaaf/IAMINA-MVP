# IAmina — Companion Intelligence Contract

> **Status:** P2-COMPANION-0 canonical product/authority contract.  
> **Purpose:** define what IAmina may observe, explain and suggest without becoming a physician, prescribing system or autonomous clinical decision-maker.  
> **Runtime precedence:** deterministic emergency/safety logic, truth provenance, evidence registry and existing no-diagnosis/no-prescription/no-dose gates remain authoritative.

## 1. Product identity

IAmina is a **patient companion**.

Its job is to help a person understand and follow their own diabetes data more consistently by organizing observations, comparing them with the person's own history, surfacing evidence-qualified changes, explaining uncertainty and proposing safe next steps for tracking, learning or discussion.

IAmina is **not a virtual doctor** and must not be designed, described or evaluated as a replacement for a physician or other qualified healthcare professional.

The desired product loop is:

`OBSERVE → COMPARE → EXPLAIN → SUGGEST → FOLLOW UP → PREPARE DISCUSSION WHEN USEFUL`

It is explicitly **not**:

`DATA → AI DIAGNOSIS → AI TREATMENT DECISION`

## 2. Companion authority ceiling

IAmina may:

- organize authoritative patient-entered or measured data;
- compare current observations with the patient's own governed longitudinal baseline;
- surface repeated or materially changed deterministic observations;
- explain what data supports an observation and what remains unknown;
- distinguish stronger from weaker evidence without inventing clinical confidence;
- point out missing context that could make later analysis more informative;
- suggest monitoring an observation;
- suggest recording relevant context next time;
- offer evidence-qualified educational information within the approved evidence boundary;
- help the patient prepare questions or discussion points for a clinician;
- summarize what changed before a consultation;
- help the patient follow the record after a consultation without judging or overriding the clinician's decision.

IAmina may not autonomously:

- diagnose or provide a differential diagnosis;
- present a pattern as a disease, syndrome or confirmed mechanism without the required authority;
- prescribe a medication or treatment;
- calculate, recommend or optimize an insulin/medication dose;
- instruct the patient to start, stop, increase, decrease or substitute treatment;
- convert an observational association into proven causality;
- claim that a clinician is wrong or override a clinician's decision;
- represent itself as a physician, medical consultation or substitute for professional care;
- let a generative model create clinical truth, urgency classification or treatment authority.

Changing this ceiling requires an explicit product/regulatory architecture decision. It is not a prompt-level change.

## 3. Allowed companion suggestion classes

Patient-facing suggestions under the companion lane are limited to non-prescriptive classes:

1. `UNDERSTAND_DATA` — explain an approved observation or metric in plain language.
2. `MONITOR` — keep watching an evidence-qualified observation over time.
3. `COLLECT_MISSING_DATA` — suggest recording relevant missing context or measurements when appropriate.
4. `LEARN` — offer approved educational material without personal treatment instruction.
5. `PREPARE_CLINICIAN_DISCUSSION` — turn an observation into a question or discussion point for a qualified clinician.
6. `FOLLOW_UP_RECORD` — help the patient track what happened after a consultation or over a defined period without judging treatment efficacy beyond governed descriptive evidence.

A suggestion must never silently become a treatment recommendation merely because it is personalized.

## 4. Analysis contract

Personalization must be evidence-qualified and patient-specific rather than generic model intuition.

For any material companion observation or suggestion, the system should be able to answer:

- **What did we observe?**
- **Compared with what?**
- **Which authoritative data supports it?**
- **Which deterministic rule/evidence ID, when applicable, authorized the derivation?**
- **How much eligible data is present?**
- **What is missing or uncertain?**
- **What safe non-prescriptive next step is allowed?**

Insufficient data must remain insufficient data. IAmina must prefer an explicit limitation over a confident guess.

## 5. Longitudinal behavior

IAmina should become more useful through governed history, not by pretending certainty.

Approved longitudinal semantics include:

- first observed;
- recurring;
- persisting;
- improving descriptively;
- resolved after eligible evidence;
- changed relative to the patient's own baseline;
- unknown because eligible evidence is insufficient.

These semantics do not by themselves establish diagnosis, causality, treatment response or future prediction.

### 5.1 Personal-pattern projection contract

P2-COMPANION-2 may make existing governed Clinical Twin observations easier to understand, but it cannot create or upgrade clinical truth:

- the projection is read-only and patient-scoped; it consumes only already-persisted governed `ClinicalObservationState`;
- first observed, activation-episode recurrence, active/resolved lifecycle, evidence density/trend and baseline-relative values come directly from the governed Clinical Twin state;
- observation key, kind and recorded context must match the existing approved personal-response vocabulary exactly; malformed or ungoverned stored state fails closed;
- `persisting`, `recurring`, `improving_descriptively` and `resolved` are bounded descriptive markers only;
- `improving_descriptively` means movement of the absolute baseline-relative delta toward the patient's own eligible window median. That median is descriptive rather than a clinical target, and the marker does not establish treatment response, therapeutic success, clinical outcome or causality;
- evidence density and its trend describe repetition density only, never probability, statistical significance or clinical confidence;
- resolved rows must disclose that numeric values describe their last eligible active evidence rather than current physiology;
- no governed patterns is not evidence that no disease or clinical issue exists, and presentation order must not be treated as clinical priority;
- this projection adds no detector, write, clinical threshold, prioritization, suggestion, narration or autonomous medical authority.

### 5.2 Change-since-review contract

P2-COMPANION-1 makes review history an explicit governed product event rather than an inferred timestamp:

- a review anchor is created server-side only when an explicit companion-review action is invoked; opening the app, reading data, chatting with IAmina or model output cannot create one;
- the anchor is patient-scoped and snapshots only approved deterministic Clinical Twin observations under their existing producer/evidence authority;
- the engine compares the latest anchor with current governed Clinical Twin state and may emit only `new`, `persisting`, `improving`, `resolved` or `unknown`; no anchor yields `insufficient_anchor`;
- `improving` means a descriptive baseline-relative delta moved toward the patient's own governed window baseline. It must never be narrated as treatment response, therapeutic success or clinical outcome;
- missing current state or insufficient post-review evidence is `unknown`, not silent resolution;
- source erasure/replacement invalidates anchors that may encode the removed evidence before Clinical Twin rebuild;
- persisted anchors/snapshots are patient-owned application records and remain subject to export, account deletion and retention governance;
- the anchor records an IAmina **companion review**, not a clinician consultation. Consultation history remains a separate P2-COMPANION-5 concern.

### 5.3 Evidence + uncertainty contract

P2-COMPANION-3 makes the evidence boundary itself inspectable without creating stronger clinical claims:

- every material P2-COMPANION-1/2 item carries one immutable `CompanionEvidenceContext` containing governed provenance plus explicit uncertainty;
- provenance includes evidence/rule ID, approved producer, rule topic/summary, evidence maturity, clinical authority, finality, review date, population/modality and registered supporting-source metadata;
- evidence maturity is governance/source status, not patient probability. `limited` / `moderate` / `strong` remains repetition density only and is not statistical or clinical confidence;
- supporting external sources retain their own maturity/finality and never inherit runtime authority from the product rule;
- candidate, narrative-only, source-only, unknown, superseded or non-versioned records cannot authorize a material companion observation;
- a globally governed product rule is still not automatically companion truth: a separate explicit rule↔producer admission registry currently allows only `rule.personal-response.repetition.v1` from `diabetes.personal_response.v1`;
- missing longitudinal/current evidence is represented in `missing_data` rather than hidden in prose or converted to certainty;
- the evidence envelope has no numeric confidence field and grants no diagnosis, causality, prediction, urgency, treatment/dose, suggestion or prioritization authority.

## 6. Consultation is a sub-capability, not the product identity

The certified `consultation-brief.v1` contract from PR #143 remains valid as a **restricted consultation-support sub-contract**.

It does not define IAmina as a doctor-facing or doctor-replacement product. Under the P2-COMPANION roadmap it belongs to **P2-COMPANION-5 — Consultation Companion**.

The consultation surface exists to help the patient arrive better prepared and to organize evidence-qualified information for review. The clinician remains the medical decision authority.

Existing `clinician_review_support_only` and `approved_structured_fields_only` limits remain valid and are stricter than, not exceptions to, this companion ceiling.

## 7. Emergency boundary

Emergency recognition and routing remain deterministic and upstream of companion intelligence.

When an emergency gate fires, IAmina may direct the patient toward the approved emergency resource/professional-care pathway according to the existing safety contract. This is not a companion-generated diagnosis and is never subject to the non-urgent proactive attention budget.

## 8. Generative-model boundary

A generative model may help verbalize approved structured observations, explanations and questions.

It may not:

- add facts not present in approved structured input;
- increase evidence maturity or certainty;
- create a diagnosis or causal mechanism;
- create treatment/dose advice;
- decide urgency;
- alter deterministic lifecycle or priority state;
- transform a suggestion into a medical instruction.

The deterministic structured result is authoritative; narration is optional presentation.

## 9. P2-COMPANION roadmap

| LOT | One responsibility | Acceptance target |
|---|---|---|
| **P2-COMPANION-0** | **Companion Intelligence Contract** | Product/authority ceiling is canonical; consultation is explicitly a sub-capability; no doctor-replacement framing |
| **P2-COMPANION-1** | **Change Since Last Review** | ✅ Certified in PR #147: governed explicit companion-review anchor + deterministic `new/persisting/improving/resolved/unknown`; post-merge CI #1913 + drift #1725 green |
| **P2-COMPANION-2** | **Personal Pattern Intelligence** | ✅ Certified in PR #149: read-only governed Clinical Twin projection; post-merge CI #1922 + drift #1734 green |
| **P2-COMPANION-3** | **Evidence + Uncertainty** | 🟡 MERGE GATE: PR #151 adds one governed evidence/uncertainty envelope to material P2-COMPANION-1/2 observations; no confidence/authority upgrade |
| P2-COMPANION-4 | Smart Suggestions | Non-prescriptive suggestions limited to understand/monitor/collect/learn/discuss/follow-up classes |
| P2-COMPANION-5 | Consultation Companion | Prepare the patient for a clinician review using the inherited `consultation-brief.v1` authority contract |
| P2-COMPANION-6 | After-Visit Continuity | Track the interval after a consultation without judging or changing the clinician's treatment decision |
| P2-COMPANION-7 | Companion UX | Patient-first surfaces organized around understand, follow and prepare rather than medical-software authority |
| P2-COMPANION-8 | Safety + Certification | Permanent negative/safety evals prevent diagnosis, prescription, dosing, treatment-change and doctor-replacement drift |

## 10. Permanent regression expectations

Future P2-COMPANION LOTs must prove at minimum that:

- unsupported or sparse data cannot produce confident personalized claims;
- generative narration cannot create new clinical truth;
- no companion suggestion can encode a treatment or dose change;
- clinician-discussion preparation remains a suggestion, not a referral/escalation authority unless a separate deterministic safety path already requires professional care;
- consultation history cannot be fabricated from app activity;
- patient-baseline comparisons preserve provenance and time-window semantics;
- source deletion/erasure cannot leave stale derived companion conclusions;
- emergency routing remains independent from non-urgent companion prioritization;
- all patient-facing wording preserves the identity: **companion that helps understand and prepare, never physician replacement**.
