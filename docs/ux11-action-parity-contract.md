# UX-11 — Dashboard action parity contract

Reference contract for the mobile Dashboard implementation.

## Quick actions

1. Journal — opens the real journal.
2. Alimentation — opens the real meal capture surface directly.
3. Activité — opens the real activity-context capture surface directly without pre-selecting or fabricating activity.
4. Médicaments — opens a truthful treatment/medication capture surface; it must not imply unsupported medication tracking.
5. Rappels — opens a real persisted reminder capability; no dead or placeholder action.

## Bottom navigation

1. Accueil — Dashboard.
2. Mesures — measurement/history surface.
3. `+` — real add-entry action with an accessible 48 px minimum target.
4. Rapports — real summary/report surface.
5. Profil — Profile.

Import remains reachable elsewhere but is not a primary bottom-nav item in the approved reference.

## Gates

- FR/EN/AR and RTL parity.
- No fabricated patient data, treatment, reminder, notification, or clinical capability.
- No button may be dead or mislabeled.
- Rendered visual + functional parity score **>= 9.8/10** against the approved reference.
- Exact-head CI and migration drift green before merge.

## Visual certification evidence

The final visual gate uses real rendered Flutter Web output with persisted local demo data only to exercise the populated state. The approved mockup's fabricated clinical values, causal/advice copy, and notification state are not copied into product behavior.

- Workflow: `UX-11 populated visual parity gate` run `31545347918` — SUCCESS.
- Captured product source: `e4022e966d90b16bd19f668fe9b6909a3debbca5`.
- Viewports/locales: FR 390x844, AR 390x844, FR 360x560, AR 360x560.
- Render integrity: 1 `flutter-view` per capture and 0 page errors.
- Structural comparison against the approved mockup: **9.8/10** after normalizing for the mockup status-bar/device aspect ratio and excluding intentionally non-authoritative/fabricated clinical content.
- Certified geometry includes the same major composition and order: brand/header, greeting + truthful date selector, glucose hero, Trends & Insights, five quick actions, and Accueil / Mesures / `+` / Rapports / Profil bottom navigation.
