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

The class vocabulary is broader than any individual runtime LOT. **P2-COMPANION-4 Smart Suggestions V1 activates only `UNDERSTAND_DATA`, `MONITOR` and `PREPARE_CLINICIAN_DISCUSSION` because those classes can reuse already-certified proactive authority.** `COLLECT_MISSING_DATA`, `LEARN` and `FOLLOW_UP_RECORD` remain fail-closed in Smart Suggestions V1 unless a later LOT explicitly adds their prerequisite governed action authority. P2-COMPANION-5 may use `COLLECT_MISSING_DATA` only inside the certified consultation-brief sub-contract when a bounded change is explicitly `unknown`; that does not silently expand Smart Suggestions authority.

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
- the anchor records an IAmina **companion review**, not a clinician consultation. Consultation history remains a separate concern from this review anchor.

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

### 5.4 Smart-suggestion contract

P2-COMPANION-4 translates **existing** governed observation/proactive authority into at most one bounded non-urgent companion suggestion; it creates neither clinical truth nor a second prioritization system:

- the projection consumes the one non-urgent item already selected by the certified P2-PROACTIVE engine, then requires exactly one matching P2-COMPANION-2 governed pattern and its P2-COMPANION-3 evidence/uncertainty envelope;
- the existing proactive priority vector, material-state delivery signature and `one_non_urgent_item_per_24h` attention budget remain authoritative. The companion layer does not calculate another risk, urgency, relevance or confidence score;
- current V1 mappings are deterministic: a first eligible proactive `MONITOR` observation maps to `UNDERSTAND_DATA`; eligible `MONITORING` / `IMPROVING` / `RESOLVED` proactive states map to `MONITOR`; existing proactive `PREPARE_CLINICIAN_DISCUSSION` authority maps to the identically named companion class;
- `COLLECT_MISSING_DATA`, `LEARN` and `FOLLOW_UP_RECORD` are valid canonical classes but are intentionally not emitted by Smart Suggestions V1; unsupported class/state/action combinations fail closed;
- the matched evidence ID and approved producer must agree across proactive output, personal-pattern projection and evidence envelope. Optional P2-COMPANION-1 `change_since_review` is descriptive metadata only and cannot grant suggestion authority;
- the suggestion projection wraps proactive delivery and downstream provenance validation in one transaction so a failed validation cannot consume the attention budget for a suggestion that was never safely produced;
- every emitted suggestion carries explicit limitations preserving the no-diagnosis/no-causality/no-prediction/no-treatment/no-dose ceiling and the separate upstream emergency boundary;
- P2-COMPANION-4 adds no detector, clinical threshold, database model/migration, endpoint, Flutter surface, generative/free-text authority input, medication/dose logic, treatment optimization/change or clinician override.

### 5.5 Consultation Companion contract

P2-COMPANION-5 deterministically assembles a patient consultation-preparation dossier into the already-certified `consultation-brief.v1` contract. It is a read-only projection and does not create a new clinical reasoning authority.

Certified runtime boundaries:

- public assembly accepts only `patient_id`, `window_start` and `window_end`; callers cannot supply a review checkpoint, free text, diagnosis, action, model output or medical conclusion;
- synchronized non-demo glucose rows may contribute latest recorded value, timestamp, capture provenance and a descriptive arithmetic average only; the average is explicitly not CGM time-weighted and not a target assessment;
- Clinical Twin content is consumed only through the governed P2-COMPANION-2/3 projection, with producer/evidence/density consistency checks and dossier-window bounds;
- since-review semantics require the persisted server-captured P2-COMPANION-1 review anchor to fall inside the requested dossier window; otherwise the dossier truthfully falls back to `CURRENT_SNAPSHOT` rather than fabricating history;
- bounded `new`, `persisting`, `improving` and `resolved` change states authorize only `MONITOR` in this consultation assembler; change state alone cannot manufacture clinician-discussion authority;
- `unknown` may authorize only `COLLECT_MISSING_DATA`, with missing evidence preserved explicitly;
- evidence that postdates the requested dossier window is excluded/fails closed rather than leaking future state into the brief;
- patient-row serialization prevents consultation reads from racing governed Clinical Twin refresh/erasure or companion-review capture;
- all output remains under `clinician_review_support_only` and `approved_structured_fields_only`; no diagnosis, causality, prediction, urgency, prescription, dose, treatment optimization/change or clinician override is introduced;
- no endpoint, Flutter surface, database model/migration, notification behavior or LLM/provider change was introduced by this runtime LOT.

**Runtime closure:** PR #155 exact head `d15d35592fb1e118951cde4f806c3e30d12c40e2` passed Clinical Safety Reviewer, CI #1945 + migration drift #1757, zero review threads and Release Certifier GO. Expected-head merge produced `135d284a5b16df853d74ef791233060b4fffe815`; post-merge `main` CI #1946 + migration drift #1758 passed.

## 6. Consultation is a sub-capability, not the product identity

The certified `consultation-brief.v1` contract from PR #143 remains valid as a **restricted consultation-support sub-contract**, now implemented by the P2-COMPANION-5 deterministic assembler.

It does not define IAmina as a doctor-facing or doctor-replacement product. The consultation surface exists to help the patient arrive better prepared and to organize evidence-qualified information for review. The clinician remains the medical decision authority.

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
| **P2-COMPANION-3** | **Evidence + Uncertainty** | ✅ Certified in PR #151: governed evidence/uncertainty envelope for material P2-COMPANION-1/2 observations; post-merge CI #1929 + drift #1741 green |
| **P2-COMPANION-4** | **Smart Suggestions** | ✅ Certified in PR #153: bounded transactional projection reusing proactive priority/anti-repeat authority; merge `71c63ef8…`; post-merge CI #1933 + drift #1745 green |
| **P2-COMPANION-5** | **Consultation Companion** | ✅ Certified in PR #155: deterministic `consultation-brief.v1` assembler; merge `135d284a…`; post-merge CI #1946 + drift #1758 green |
| **P2-COMPANION-6** | **After-Visit Continuity** | ✅ Certified: explicit visit/fact continuity with provenance and no treatment-efficacy inference from chronology |
| **P2-COMPANION-7** | **Companion UX** | ✅ Certified: read-only overview API + FR/EN/AR patient-first Flutter surface + dashboard discoverability; final merge `bb5b9cb8…`; post-merge CI #1966 + drift #1778 green |
| **P2-COMPANION-8** | **Safety + Certification** | ▶️ NEXT: permanent negative/safety evals prevent diagnosis, prescription, dosing, treatment-change, false-certainty and doctor-replacement drift |

### 5.6 After-Visit Continuity and Companion UX closure

P2-COMPANION-6 and P2-COMPANION-7 preserve the same authority ceiling through persistence, API and patient UX. Final P2-COMPANION-7 dashboard merge `bb5b9cb87fdd48197657cb38011509876756b5ea` passed post-merge CI #1966 and migration drift #1778.

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
