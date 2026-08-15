# IAmina UI global coherence certification — 2026-08-15

## Scope

Presentation-only coherence lot merged by PR #236. The lot standardized the canonical patient mobile header, bridged Add Log and Document Import into the same chrome, simplified focused-task microcopy, and added regression coverage. No clinical thresholds, persistence, routing authority, medication logic, import parsing, or backend behavior changed.

## Pre-merge certification

Final exact head: `856dd0ac4c9f6ab648acbff8656a518a6871ba52`.

- CI #2381: PASS.
- Django migration drift #2193: PASS.
- Native UI screenshot audit #58: PASS.
- Real Chrome browser certification #17 at 390x844: PASS.
- Browser artifact: `iamina-ui-browser-cert-390x844`, artifact `9247842392`, digest `sha256:f33dbcea88deef9fc8b3396b304d42a0aaf59db8958a6548299389c07e748b13`.
- Ten Chrome surfaces were visually inspected side by side: dashboard, companion, summary, profile, journal, importer, document import, add log, medications, reminders.

The first Chrome comparison exposed inherited yellow text decoration on Document Import. The defect was corrected in the canonical header and locked by the visual-language contract test. The final Chrome #17 comparison showed the decoration removed and the header rhythm, first-card placement, and primary CTA hierarchy coherent enough for merge.

## Merge

PR #236 was squash-merged with expected-head protection.

Merge commit: `8b8190250928ae8e4e42d214ffa9c595e4e0100a`.

## Roadmap impact

`docs/ROADMAP.md` was inspected during closeout. This maintenance/certification lot does not create, close, or reopen a numbered roadmap workstream and does not change the MENA critical-path numerator or denominator. The existing UX visual rebase remains closed; this document records the fresh evidence required for the subsequent coherence maintenance change.

## Post-merge gate

Post-merge CI/drift/UI workflow evidence must be attached to this closeout before it is considered fully certified. Until then, the runtime merge is complete but the documentation closeout remains pending post-merge recertification.
