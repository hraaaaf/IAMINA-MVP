# IAMINA D20 — real ProfileScreen visual gate, 15 October 2026

## BEFORE (reference)
Actual `ProfileScreen` from D18-C, 2 synthetic patient-declared weights (70.00 kg UTC 11 Oct, 72.50 kg UTC 14 Oct), AppLock explicitly simulated. Capture the existing screen before any D20 code UI change with this branch's baseline SHA. Languages FR/AR; viewports **390×844 / 430×932 / 768×1024 / 1280×900**; states top/open/history. Same captures after UI implementation with identical seeds/viewports and audit fonts. Never use patient data.

## Goal and observable success
After D18 history, show an OPTIONAL local descriptive weight trend:
- 0/1 observed weight = truthful unavailable comparison, without fake change.
- 2+ valid patient-owned UTC readings = signed difference in 0.01 kg, baseline/latest patient-local dates, source patient-declared, no diagnosis or color-coded danger. Do not alter clinical targets, therapies or safety warnings.
- No notification OS permission, opt-in control or push enabled by this visual slice. Keep D20-B/C/D fail-closed.
- Logical reading order FR/AR and RTL, contrast, text accessibility at four widths. No overflow. Original ProfileScreen header and patient history remain intact.

## Text mockup / reference (not yet implemented)
```
[Historique du poids]
  ... mesures précédentes ...
  ┌ Évolution du poids · facultatif ─────────┐
  │ Entre [date A] et [date B]               │
  │ Variation descriptive : +2,50 kg         │
  │ Source : mesures saisies par le patient  │
  │ Non utilisé pour ajuster les traitements │
  └──────────────────────────────────────────┘
```
For insufficient rows: `Pas assez de pesées pour comparer.` Label `Évolution` must not imply medical progression or weight goal.

## Proof ledger
- BEFORE exact SHA: PENDING first workflow run / PNG list.
- AFTER exact SHA: PENDING new UI implementation and workflow.
- Pixel diff & visual score: NOT YET VERIFIED. Do not claim validation or a score before inspecting both.
- D20 parent D18 unmerged; no Vercel and no patient release. P5 historical 6/12 = 50% unchanged.

## Next
Capture BEFORE and inspect artifact -> implement widget without changing historical data paths -> run AFTER at same viewports -> compare raster, a11y and Flutter tests -> fix until stable -> record visual proof and reviewer status.

## AFTER candidate (D20 read-only visual slice)

Implemented `D20WeightTrendCard` after D18 weight history in the canonical `D18ProfilePanel` (itself included only for unlocked native patient vault in real `ProfileScreen`). Card uses sorted/validated local descriptive `LocalWeightTrendSnapshot`, explicit empty state for 0/1/untrusted facts, UTC source evidence, localized FR/EN/AR, neutral fixed-point signed kg, separate numeric LTR rendering in RTL, patient declaration provenance and no-medical-adjustment wording. No notification preference switch, OS permission, callback, LLM or network logic was introduced; D20-B/C/D remain separate draft gates.

**Source BEFORE**: CI #38775995975 success exact HEAD `592f26f2c99399a2936814fe022717ae410fee07`, artifact `11994430142` `d20-profile-real-raster` (24 synthetic ProfileScreen PNGs). AFTER is a new commit and will independently run the same four viewport+two locale captures plus eight closeups, Flutter component tests, and a downloaded baseline pixel diff. Do not claim passed AFTER, artifact inspection or a visual score until its CI completes.

## AFTER evidence and manually inspected result — 15 October 2026

- **AFTER exact source SHA**: `0fc298f6f419d68ba9dd5b8fff9a5686e50e17e6`. [GitHub Actions #38776557590](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38776557590) **COMPLETED SUCCESS**. Six UI widget cases (FR/EN/AR; 0/1 data fail-closed, signed +/−, same-owner, mixed/ambiguous rejection, numeric LTR RTL; four-width no-overflow) PASSED. Full real ProfileScreen synthetic raster test also PASSED.
- **Artifacts**: 32 real ProfileScreen PNG captures (24 canonical before/after matching states, 8 dedicated new trend FR/AR closeups) in artifact `11994326135`, zip SHA256 `e6e153d07876eb6fe7ec2268a0c84078d9873ff6fb01124c14a3ea8901a8b87a`; BEFORE reference run #38775995975 / artifact `11994430142`. Identical fixture (2 dated patient-declared measures), audit fonts and viewport dimensions FR+AR 390×844, 430×932, 768×1024, 1280×900.
- **Automated pixel comparator**: 24 exact-size image pairs compared by Pillow; top view **8/8 pixel-identical (0 pixels changed)**. Expansion `open`: 6/8 identical; on 768px FR/AR, 6.086%/7.786% pixel changes, consistent with new content affecting scroll geometry. History view shows 21.854%–54.070% changed pixels; changes are **not** automatically benign, but expected after new card changes scrolling. Eight additional new-card captures produced with no widget/renderer exception.
- **Manual model visual inspection** of FR 390×844 and 430×932, AR 390×844 and 1280×900, FR 768×1024: card is legible, neutral, left-to-right numeric sign remains readable in Arabic RTL, no observed clipping. **Internal D20-card visual score: 8.5/10 provisional** (coherent style/responsiveness, limited date typography and content density); NOT a human/native accessibility certification.
- **Inherited visual issue**: square glyph placeholders and blank bars visible outside D20 card in AR and FR Flutter raster existed already in the BEFORE reference, e.g. `d18-real-profile-ar-390x844-history.png` and AFTER. Root cause could be synthetic audit-font rendering rather than production; **not fixed** here and not attributed to D20. Needs targeted font/device investigation before any claim of complete polished UX.
- **Boundaries**: no actual OS notification, user-facing opt-in form, push transport, diagnosis, profile/clinical target changes or Vercel D20 deploy. D20 #20 remains OPEN; parent PRs #1066, #1074, #1076, #1077, #1078, child #1079 DRAFT/unmerged. Human privacy/clinical review and patient consent gates remain. P5 canonically historical 6/12=50%.

## Exact-head CI recovery status — 15 Oct 2026
- D20-E parent code `f2062df341616e928e1adf4c49c8f630d448558a` qualified by D20 visual run #38777413881 plus UI geometry #38777423971 and browser #38777423631, all SUCCESS.
- CI-only change `f21048ea10a8905bdca7c4e8a34ce7e4aef033a8` adjusts D18 raster artifact expectations for the added 430×932 real ProfileScreen viewport: 24 original D18 isolated rasters + 30 real ProfileScreen images. No Dart product code changed from `f2062df`.
- GitHub Action runs #38780334937, #38780334849, #38780335059 and #38780335020 were marked failure at runner allocation: 0 steps, no runner name, logs inaccessible. They do NOT establish an application regression or successful updated raster check.
- This documentation change deliberately triggers dedicated D20 visual workflow on new exact SHA; inspect runner availability and 24+8 raster comparison, keep PR DRAFT and clinical/privacy/mobile gates open. **Do not assert green before new proof.**

## Correction démontrée du contrat D18 raster, 15 Oct
La CI nouvelle #38784022484 (SHA `70f461d`) a exécuté avec succès les tests D18 + rendu des captures mais a échoué dans le contrôle de fichiers. Le script attendait à tort **30** captures réel ProfileScreen pour les viewports `360/390/430/768/1280`, alors que la fixture intégrée (source `d18_profile_integrated_capture_test.dart`) ne rend que `390/430/768/1280`, soit **4 × 2 × 3 = 24**. L'étalon D18 isolé reste 24 (360/390/768/1280). Le script de validation est désormais aligné sur la production réelle **sans masquer un fichier manquant**. La CI doit encore confirmer ce nouveau SHA. Ne pas déduire certification médicale. Pas de modifications Dart.
