# FoodPicker B31 — Egypt core — current-main rebuild

## Goal
Rebuild B31 from current `main@40af628e7087d5daf92acadba4397bc8a192338d` after the previous candidate accumulated 56 commits of drift, while preserving the certified 392-item B30 prefix.

## Catalog
- before: 392
- target: 395
- concepts: `egyptian_koshary`, `egyptian_ful_medames`, `egyptian_molokhiya`
- labels: FR/EN/AR retained from the reviewed B31 candidate.

## Provenance
- Experience Egypt Gastronomy: https://www.experienceegypt.eg/en/attraction-details/315/gastronomy
- Experience Egypt Culture: https://www.experienceegypt.eg/en/home/Culture
- UNESCO ICH Koshary: https://ich.unesco.org/en/RL/koshary-daily-life-dish-and-practices-associated-with-it-02278
- UNESCO Egypt listing: https://ich.unesco.org/en/state/egypt-EG

## Drift decision
The 56 incoming commits from the old merge-base to current main do not touch the FoodPicker frontend paths changed by B31; they are preserved by rebuilding from current main rather than merging the stale branch.

## UI proof
BEFORE: B30 `Pizza Margherita`.
Goal: expose native B31 Egypt artwork without geometry/category regression.
AFTER: `Kochari égyptien`.
Viewports: 390x844, 768x1024, 1280x900.

## Gates required
CI; P5-5 End-to-End Pilot Rehearsal; UI geometry golden audit; UI browser screenshot certification; exact-head artifact SHA256 and manual screenshot inspection.

## Merge / deployment
Never auto-merge. Human approval only after certified principal screenshot. No Vercel deployment.
