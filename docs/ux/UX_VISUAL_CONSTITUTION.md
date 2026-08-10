# IAmina — Visual Constitution

> Baseline date: 2026-08-10
> Scope: current Flutter product surface on `main@1331a4ef67573409eb62d43f702f0183225c49e0`.
> Purpose: durable visual-quality rules and evidence boundaries for future UX/UI LOTs. This document is not a duplicate forward backlog; `docs/ROADMAP.md` remains the single forward tracker.

## 1. Evidence hierarchy

Visual claims must use the strongest available rendered evidence, not source-code impression alone.

1. Fresh exact-head rendered capture of the affected state.
2. Recent rendered certification whose affected frontend files have not changed.
3. Widget/integration contracts and source inspection.
4. Source-code-only visual inference is supporting evidence only and must not override a stronger rendered certification.

Historical evidence still applicable to current frontend:

- P2-UX-14 global matrix: UX 9.2/10, 40/40 FR/AR views, desktop/tablet/390x844/360x560, run `31267173791`, artifact `9024558783`, digest `sha256:fcb730b7c32b8b2a8435072109f6a879170414f81e39ec8f139c28b421d5e902`.
- P1-JOURNAL-7 Profile/Ramadan + Add: UX 9.3/10, 24/24 FR/AR views, run `31377323425`, artifact `9058462463`.
- P2-JOURNAL-9 post-save: UX 9.3/10, 16/16 FR/AR views, run `31389858816`, artifact `9063210662`. No frontend files changed between PR #77 merge and this baseline main.

## 2. UX-0 fresh rich-state audit

The historical global matrix exercised the first-use/empty Dashboard. UX-0 added a temporary audit-only synthetic-data seed behind the existing compile-time + loopback-only visual-cert access boundary, captured the populated Dashboard, then removed the seed and temporary workflow completely before preparing this document.

Fresh evidence:

- run `31403179971` — SUCCESS;
- artifact `9068596037`;
- digest `sha256:e03dada2ae5d4003ac0ba3c2b9ee43a2e0dc39f1ca896c98b8e225aa3ba42e66`;
- exact audit source `30e242f4c75d741d9d9be88b4b39aabb8b74b131`;
- 8/8 populated Dashboard renders: FR/AR x 1440x1000, 768x1024, 390x844 and 360x560;
- one Flutter view per capture;
- zero page errors.

### UX-0 finding

The populated Dashboard is not yet locale-parity certified.

Observed directly in the rendered matrix:

- meal context can surface raw canonical values such as `dinner` in both French and Arabic;
- Arabic Dashboard KPI content contains French labels/copy, including GMI, CV and event/analysis text;
- source inspection confirms the issue is systematic rather than a capture artifact: several rich-state Dashboard widgets contain hard-coded French strings, while `AuditedPageCopy.meal()` returns unknown meal values verbatim.

Scoring for this newly exercised state:

- populated Dashboard FR: approximately **9.1/10**;
- populated Dashboard AR/RTL: approximately **7.7/10** because a primary MENA locale is visibly mixed-language on high-salience KPI surfaces;
- populated Dashboard cross-locale baseline: **8.4/10 — CHANGES REQUIRED**.

This does not invalidate the previously certified empty/first-use Dashboard, Journal, Profile, Importer or post-save surfaces. It identifies a previously untested product state.

## 3. Visual doctrine

IAmina should read as a calm, trustworthy clinical companion rather than a showcase dashboard.

- One dominant focal point per viewport. Secondary cards must support it rather than compete with it.
- Teal is the primary brand/clinical accent. Amber/red/blue are semantic, not decorative.
- Gradients and glow are reserved for deliberate emphasis. Do not add decorative effects merely to increase perceived polish.
- Prefer clinical surfaces, restrained shadows and stable spacing over glassmorphism proliferation.
- Use the established radius family consistently; new arbitrary radii require evidence.
- Typography must preserve a clear hierarchy: page title -> primary measurement -> section heading -> supporting copy -> metadata.
- Dense clinical information must use progressive disclosure where possible, especially at 390x844 and 360x560.
- Primary and recovery actions must remain reachable without being hidden behind bottom navigation, keyboard, sheet chrome or long receipts.
- Desktop content must remain bounded/readable; tablet must not be treated as reduced desktop; mobile must not be a squeezed desktop composition.

## 4. Locale and RTL doctrine

FR, EN and AR are product surfaces, not translation afterthoughts.

- No hard-coded patient-facing language in routed production UI when an equivalent localized key is required.
- Canonical stored identifiers such as meal/context IDs must never be displayed raw when a localized patient-facing label exists or is required.
- Arabic must be audited visually in RTL, not only through ARB presence or string tests.
- Numeric units/ranges may preserve LTR isolation where required, without breaking surrounding RTL flow.
- A high-salience mixed-language residue on a primary Arabic surface is a blocking UX finding for a >9/10 certification.

## 5. Protected certified surfaces

Do not reopen or cosmetically rewrite a previously certified surface merely for stylistic uniformity.

A certified surface may be changed only when one of these is true:

1. fresh rendered evidence shows a score <=9.0 or a critical/high defect;
2. a new product requirement necessarily changes that surface;
3. a cross-cutting accessibility, locale, safety or platform contract requires remediation.

The Journal redesign, including P2-JOURNAL-9, is specifically protected by this rule. Any future work must preserve its factual/non-prescriptive behavior and existing 9.3/10 visual contract.

## 6. Mandatory UX/UI closure gate

Every future UX/UI remediation LOT must:

1. inspect the exact current implementation and prior certifications;
2. capture a real baseline for the affected state;
3. make the smallest evidence-backed change;
4. run analyzer/tests and relevant non-regression contracts;
5. capture FR/AR and required viewport matrix on the exact final product head;
6. receive an isolated UX Auditor pass;
7. score **strictly above 9.0/10**, with no unresolved critical/high finding;
8. remove temporary capture/scaffolding files from the final diff;
9. receive Release Certifier approval, expected-head merge and post-merge verification.

## 7. Evidence-backed next target

The first justified remediation is the **populated Dashboard locale parity and hierarchy**, not a global redesign. Scope should remain limited to rich-state Dashboard presentation: localize all patient-facing KPI/chart/insight/event strings and canonical meal labels, preserve clinical calculations and data semantics, then recapture the full FR/AR rich-state matrix and continue only if the final score remains <=9.0.
