# IAmina Diabetes Evidence — Core Source Map

> **Checked:** 2026-08-12  
> **Rule:** this is a starting index, not frozen truth. Re-verify finality, corrections and version status online before any LOT changes a governed clinical rule.

## 1. ADA Standards of Care in Diabetes — 2026

**Status:** current final annual ADA clinical-practice recommendations as of this check. ADA states the Standards are updated annually or more frequently as warranted.

Primary collection / methodology:
- Standards of Care in Diabetes—2026, *Diabetes Care* 49(Suppl. 1), published 2025-12-08 for the 2026 standards.
- Introduction and Methodology identifier: DOI `10.2337/dc26-SINT`.
- Summary of Revisions: https://diabetesjournals.org/care/article/49/Supplement_1/S6/163930/Summary-of-Revisions-Standards-of-Care-in-Diabetes

High-signal sections for IAmina:
- Section 2 — Diagnosis and Classification: https://diabetesjournals.org/care/article/49/Supplement_1/S27/163926/2-Diagnosis-and-Classification-of-Diabetes
- Section 5 — Positive Health Behaviors and Well-being: https://diabetesjournals.org/care/article/49/Supplement_1/S89/163932/5-Facilitating-Positive-Health-Behaviors-and-Well
- Section 6 — Glycemic Goals, Hypoglycemia, and Hyperglycemic Crises: DOI `10.2337/dc26-S006`
- Section 7 — Diabetes Technology: DOI `10.2337/dc26-S007`
- Section 9 — Pharmacologic Approaches to Glycemic Treatment: https://diabetesjournals.org/care/article/49/Supplement_1/S183/163934/9-Pharmacologic-Approaches-to-Glycemic-Treatment
- Section 10 — Cardiovascular Disease and Risk Management: https://diabetesjournals.org/care/article/49/Supplement_1/S216/163933/10-Cardiovascular-Disease-and-Risk-Management
- Section 11 — Chronic Kidney Disease and Risk Management, abridged DOI `10.2337/doc26-a011`
- Section 12 — Retinopathy, Neuropathy, and Foot Care: DOI `10.2337/dc26-S012`
- Section 13 — Older Adults: DOI `10.2337/dc26-S013`
- Section 14 — Children and Adolescents: DOI `10.2337/dc26-S014`

### Important IAmina implications
- Population goals are individualized; do not turn guideline population targets into autonomous patient commands.
- CGM interpretation depends on modality/data sufficiency and must not be inferred from sparse manual readings.
- Diabetes technology selection/use is individualized and coupled to education/support.
- Religious fasting now has an updated comprehensive prefasting risk-assessment recommendation in the 2026 Standards.

## 2. ISPAD Clinical Practice Consensus Guidelines

**Status:** authoritative pediatric/adolescent diabetes source family; 2024 guideline set is the latest comprehensive ISPAD set surfaced by the official site at this check, with updated chapters published through 2025.

Official index:
- https://www.ispad.org/resources/ispad-clinical-practice-consensus-guidelines/2024-cpcg.html

High-signal updated chapters include:
- screening/staging and beta-cell preservation in type 1 diabetes;
- type 2 diabetes in children/adolescents;
- glycemic targets;
- insulin and adjunctive treatments;
- insulin-delivery technology;
- glucose-monitoring technology.

### IAmina implication
Never reuse an adult rule for a child/adolescent merely because the metric name is the same. Development, caregiver role, school context, psychosocial context and pediatric evidence must be checked.

## 3. KDIGO — Diabetes and CKD / CKD

**Current status checked 2026-08-12:**
- KDIGO 2022 Diabetes in CKD guideline remains the latest **final** dedicated KDIGO diabetes/CKD guideline listed by KDIGO.
- KDIGO 2024 CKD Evaluation and Management guideline is final and relevant to CKD context.
- KDIGO 2026 Diabetes and CKD guideline is still presented by KDIGO as a **public-review draft**, not final. It must therefore remain `EMERGING_EVIDENCE`/draft inside IAmina until a final publication is verified.
- KDIGO published a 2025 commentary on GLP-1 receptor agonists/incretin mimetics for diabetes and CKD; commentaries do not silently supersede a final governed IAmina rule.

Official sources:
- Diabetes and CKD guideline suite: https://kdigo.org/guidelines/diabetes-ckd/
- KDIGO 2024 CKD guideline: https://kdigo.org/guidelines/ckd-evaluation-and-management/kdigo-2024-ckd-guideline/
- 2026 Diabetes and CKD public-review notice: https://kdigo.org/kdigo-2026-diabetes-and-ckd-guideline-draft-available-for-public-review/

### IAmina implication
A draft recommendation can inform horizon review or clinician discussion but cannot become a patient-facing deterministic rule without explicit governed adoption.

## 4. IDF / Diabetes and Ramadan (DaR)

**Status checked 2026-08-12:**
- IDF hosts the **IDF-DAR Risk Calculator Update 2026**, described as a refined evidence-based framework for evaluating fasting risk in people with diabetes.
- ADA Standards of Care 2026 Section 5 recommends use of the updated IDF/DaR comprehensive prefasting risk assessment for religious fasting.
- IDF also retains the 2021 practical Ramadan guidelines and a patient safe-fast guide; do not assume an older document supersedes the 2026 risk update.

Official sources:
- IDF-DAR Risk Calculator Update 2026: https://idf.org/news-and-resources/resources/idf-dar-risk-calculator-update-2026/
- IDF fasting resource hub: https://idf.org/managing-diabetes/fasting/
- ADA 2026 Section 5: https://diabetesjournals.org/care/article/49/Supplement_1/S89/163932/5-Facilitating-Positive-Health-Behaviors-and-Well

### IAmina implication
Ramadan expertise is a first-class MENA competency, but fasting risk remains individualized. IAmina must not autonomously alter medication dose/timing; it may support risk-aware education, preparation and clinician handoff inside repository authority limits.

## 5. Evidence-horizon separation

Examples of sources that must remain below `STANDARD_OF_CARE` until promoted through the governed process:
- peer-reviewed but not yet guideline-adopted prediction/AI methods;
- preprints and conference abstracts;
- new device capabilities not yet regulator-approved in the target jurisdiction;
- mechanistic hypotheses or single-study associations;
- draft guidelines such as the KDIGO 2026 Diabetes and CKD public-review draft at this check.

## Maintenance rule
On every clinical-evidence LOT:
1. re-open the authoritative source;
2. check for a newer final version, correction or erratum;
3. update `Checked`/status only if the source map itself changes;
4. never cite this file as the clinical authority when the underlying primary source can be cited directly.
