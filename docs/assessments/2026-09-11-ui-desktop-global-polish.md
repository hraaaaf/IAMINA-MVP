# UI-DESKTOP-GLOBAL-POLISH — Global desktop density and action polish

**Date:** 2026-09-11  
**Status:** ACTIVE

## Goal

Polish the entire IAMINA patient-facing application for desktop so every product page uses the available canvas intentionally, avoids under-filled wide layouts, and avoids unnecessarily full-width primary actions, without degrading the certified mobile/tablet experience or changing clinical, persistence, authentication, CGM, or release behavior.

## Success criteria

1. Every real patient-facing route is present in retained browser evidence at 390x844, 768x1024 and 1280x900.
2. Desktop pages no longer look like stretched mobile screens: content width, grid, secondary rail, empty states and action placement are intentional per page.
3. Primary desktop actions are content-sized or column-sized by default; full-width actions are retained only when the interaction itself legitimately owns the full region.
4. Forms that have meaningful secondary/context content use two-column desktop composition where appropriate.
5. Empty/error states use a bounded focal width instead of spanning the full desktop canvas.
6. Existing Dashboard, Journal and Trend density is not regressed.
7. Mobile/tablet information architecture and interaction order remain intact unless evidence shows a defect.
8. FR/EN/AR, RTL, accessibility, clinical boundaries, data flows and route behavior remain unchanged.
9. Analyze/tests and real Chrome evidence are green on the exact implementation head.
10. Same-viewport BEFORE/AFTER review supports a desktop visual score >= 9.0/10 for every audited real product page before closeout.

## BEFORE evidence already retained

Canonical global browser run before this lot:

- workflow: `UI browser screenshot certification`;
- run: `34629126600` / #392 — **SUCCESS**;
- exact head: `aa753f06a9b06a3ebe369169f17f0bf0f9c8083c`;
- artifact: `iamina-ui-browser-cert-multi-viewport`;
- artifact id: `10276350839`;
- digest: `sha256:8d0d47000db5e16e4afcceeebdcc1d57e2e9ab49088f41ce59a9bf607f369335`;
- 42 retained PNGs: 14 surfaces x 390/768/1280.

The existing global run covers these real product pages: Dashboard, Journal, Reports/Summary, Profile, Importer, Document Import/Pulper, New Reading, Medications, Reminders and Companion. It also covers four isolated Dashboard surfaces: Trend, KPI, Insight and Next Action.

## Coverage gap found before implementation

The production router contains additional real patient-facing routes not present in the 42-image global artifact:

- `/login`;
- `/reset-password`;
- `/consent`;
- `/onboarding`;
- `/companion/chat`;
- `/cgm`;
- `/journal/:id/edit`.

A dedicated missing-route browser certification is therefore required before claiming a whole-application desktop audit.

## Verified baseline observations from the 1280x900 contact review

Strong reference surfaces:

- Dashboard;
- Journal;
- Trend.

Systemic desktop weaknesses visible across the current application:

- multiple full-screen flows retain a mobile-first single-column composition on wide canvases;
- several forms place one primary card near the top and leave a large inactive lower canvas;
- several `FilledButton` / `OutlinedButton` actions inherit the full width of their parent despite short labels and low information density;
- some empty/error states span almost the full content width despite containing only a small amount of copy;
- headers and body grids are not always aligned to the same desktop content rail;
- page-specific max widths vary enough to make the application feel assembled rather than governed by one desktop system.

## Locked desktop design rules

These rules are the implementation reference for this lot:

1. **Desktop content rail:** use a consistent bounded central canvas, normally 1040–1120 px depending on the page's information density.
2. **Action width:** primary/secondary buttons on desktop should size to content or to the owning column. A full-width button is allowed only for a genuine full-region action such as a drop zone or a bottom save bar whose purpose is deliberately page-wide.
3. **Forms:** prefer 7/5, 8/4 or equivalent two-column desktop composition when a contextual/detail/history panel already exists or can truthfully reuse existing information.
4. **Empty/error states:** focal content max width roughly 560–680 px, centered or intentionally anchored.
5. **Information pages:** use two-column composition when existing content can be grouped without inventing data or features.
6. **Headers:** align header content with the body content rail.
7. **No decorative filler:** do not invent statistics, recommendations, patient data or fake cards merely to occupy space.
8. **Responsive preservation:** below the desktop breakpoint, preserve the current mobile/tablet reading and action order unless the audit proves an existing defect.

## Initial page-level priority

P0 desktop polish based on retained evidence:

- New Reading;
- Document Import/Pulper;
- Importer;
- Medications;
- Reminders;
- Companion;
- Reports/Summary;
- Next Action.

P1 polish after the full-route baseline is complete:

- Profile;
- KPI;
- Insight;
- CGM;
- Companion Chat;
- Edit Reading;
- authentication/consent/onboarding pages if their retained 1280 evidence scores below 9.0.

Dashboard, Journal and Trend are reference surfaces and should receive only regression-safe micro-polish if needed.

## Scope boundary

This lot is presentation/responsive UX only. It does not authorize Vercel deployment, change Pilot Readiness or MENA arithmetic, or change clinical/data/security behavior.
