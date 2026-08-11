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
3. `+` — real add-entry action.
4. Rapports — real summary/report surface.
5. Profil — Profile.

Import remains reachable elsewhere but is not a primary bottom-nav item in the approved reference.

## Gates

- FR/EN/AR and RTL parity.
- No fabricated patient data, treatment, reminder, notification, or clinical capability.
- No button may be dead or mislabeled.
- Rendered visual + functional parity score >= 9.2/10 against the approved reference.
- Exact-head CI and migration drift green before merge.
