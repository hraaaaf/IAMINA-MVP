# IAMINA / Pulper — isolated browser OCR spike (#1067)

**Research-only. Never upload patient documents.** Compare **Tesseract.js 7.0.0** with **PaddleOCR.js 0.4.2** on *synthetic* French PNG/JPEG images in actual desktop Chromium, while Tesseract also runs Arabic and mixed examples. This does **not** modify the Flutter app, the backend, or Vercel production.

## Goal / success / proof

Goal: local-only OCR of photo text with exact preservation of critical numbers, units, and labels. Exploratory success: same-origin inference with no external browser request, precise match of numeric/unit **multisets** and expected literal labels, and observed timing. This does **not** establish clinical provenance or readiness to import medical data. Medical qualification additionally needs document-position evidence, safe preprocessing, real-photo sensitivity/specificity, iPhone/Safari memory and HEIC tests, and human clinical/privacy validation.

Run on a connected **test** machine (Node >=22, Python/Pillow, DejaVu and Noto fonts):

```bash
cd experiments/pulper-photo-ocr
npm install --no-audit --no-fund
npm test
npm run fixtures
npm run assets
npx playwright install chromium
npm run bench
cat out/report.json
```

Models are fetched **at build/setup time**, only from official allowlisted Tesseract/Paddle hosts, then copied to same-origin `public/assets/`. The browser page has a restrictive CSP; Playwright **aborts any external HTTP call**. They are **not** hash-pinned until an audited asset manifest and npm lockfile have been approved; the generated `.assets-manifest.json` is initial evidence, not proof of supply-chain immutability.

`npm run native-reference` uses **system Tesseract** on the identical fixtures and writes `out/native-reference.json`. That is *not* Tesseract.js accuracy. Preliminary native local signal: 1/8 synthetic images preserved every numeric token, unit, and critical label. It misread HbA1c, µmol/L, or Arabic units in other cases; browser results are pending independent measurement.

**No clinical integration:** Existing Pulper receives files, and its image OCR deliberately fails closed. Any future integration must add an authorized **browser-local image → OCR text → provenance review → safe-text endpoint → pseudonymization / PulperShield → explicit confirmation** pathway. This spike never calls patient API, never transmits image bytes to an LLM, and never stores raw OCR transcript in reports.

Unsupported today: HEIC iPhone image decoding, scanned PDF OCR, Arabic PaddleOCR.js default models, real photos, Safari iOS benchmarking. PaddleOCR.js `lang=fr` uses PP-OCRv6-small default and is not an Arabic qualification. No fallback to raw-cloud OCR.

Existing native, *non-browser* evidence in repository: `scripts/run_local_ocr_smoke.py`, `scripts/run_tesseract_arabic_robustness.py` (C23), `scripts/run_paddleocr_local_benchmark.py` (C12), `scripts/run_paddleocr_hardening_benchmark.py` (C15). The smoke records `HbA1c` misread as `HbAlc`. None certify this spike or Safari.

**Status:** Initial CI #38737928952 failed before any OCR with a browser CSP `EvalError`. The follow-up benchmark isolates engines via lazy PaddleOCR import, emits bounded browser failure details and limits each engine to 180 seconds. No production deploy or merge. Track P0 #1067.

## CI browser evidence and strict scoring

- Run [#38744267632](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38744267632): Tesseract.js v7 executed 1/8 synthetic cases under initial token/label checks (FR 1/5, AR 0/2, mixed 0/1), no external requests. PaddleOCR.js failed at runtime because its dependency uses `new Function` and strict CSP forbids `unsafe-eval`.
- This revised spike binds exact numbers and units to their **original synthetic source rows**; unordered token multisets alone can falsely pass swapped glucose/HbA1c values. It deliberately rejects ambiguity and is still **not** a clinical provenance certification.
- `paddle.html` permits `unsafe-eval` exclusively in this synthetic test harness so we can measure **candidate accuracy**. The real IAMINA page retains strict CSP. PaddleOCR.js remains **not production CSP compatible** until an audited alternative removes the requirement. Do not copy this test exception into the application or load patient files here.
- Browser warnings such as Tesseract `Estimating resolution as N` are informational and no longer incorrectly counted as runtime errors.

## Static bundle correction (CI #38745491710)
The third run proved Tesseract.js v7 still measures 1/8 under stricter source-row checks. Paddle no longer failed on CSP inside the dedicated synthetic probe, but Vite's **dev** middleware rejected ONNX Runtime `.mjs?import` from `public/assets/ort` before OCR. The harness now performs an actual Vite multi-page **build** and serves its static output with `vite.preview` to avoid this dev-server-only importer restriction. See `npm run build && npm run bench`. The **production** IAMINA CSP remains unchanged and Paddle's experimental `unsafe-eval` remains research-only. No patient data.
