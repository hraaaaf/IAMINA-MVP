# FoodPicker B31 — Egypt core

## Goal
Append a small, culturally verified Egypt batch after certified B30 without disturbing the 392-item prefix.

## Baseline / target
- baseline: 392 concepts
- target: 395 concepts
- branch: `feat/foodpicker-b31-egypt-core-v3`

## Accepted concepts
1. `egyptian_koshary` — FR: Kochari égyptien — EN: Egyptian koshary — AR: كشري مصري
2. `egyptian_ful_medames` — FR: Foul medames égyptien — EN: Egyptian ful medames — AR: فول مدمس مصري
3. `egyptian_molokhiya` — FR: Molokhiya égyptienne — EN: Egyptian molokhiya — AR: ملوخية مصرية

## Provenance evidence
- Experience Egypt gastronomy: https://www.experienceegypt.eg/en/attraction-details/315/gastronomy — explicitly describes foul medames, koshary and molokhiya as Egyptian cuisine.
- Experience Egypt culture: https://www.experienceegypt.eg/en/home/Culture — identifies foul and koshary among Egyptian food favourites.
- UNESCO ICH: https://ich.unesco.org/en/RL/koshary-daily-life-dish-and-practices-associated-with-it-02278 — Egypt, inscribed in 2025; documents ingredients and cultural practice of koshary.
- UNESCO Egypt listing: https://ich.unesco.org/en/state/egypt-EG — independently lists Koshary for Egypt.

## UI proof contract
BEFORE: B30 fixture `Pizza Margherita` at 390x844, 768x1024, 1280x900.
Goal: expose B31 Egypt artwork without geometry/category regression.
AFTER fixture: `Kochari égyptien` at the same three viewports.

## Required gates
- CI
- P5-5 End-to-End Pilot Rehearsal
- UI geometry golden audit
- UI browser screenshot certification
- exact-head artifact SHA256 verification and manual inspection of all three FoodPicker captures

## Merge / deployment
No automatic merge. Human approval is required after certified visual proof. No Vercel deployment.
