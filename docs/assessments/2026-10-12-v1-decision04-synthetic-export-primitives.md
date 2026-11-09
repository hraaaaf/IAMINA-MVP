# V1 decision #4 — Synthetic deterministic CSV and JSON proof

**Decision #4** calls for deterministic, multi-format Reports exports. This is an isolated technical precursor, not a patient-facing export capability, PDF replacement, or consent approval. [Issue #953](https://github.com/hraaaaf/IAMINA-MVP/issues/953) records the Goal and baseline before implementation.

## BEFORE — code verified on main
- `reports_screen.dart` and `reports_screen_presentation.dart`: descriptive offline Reports, no patient-facing CSV/JSON/PDF sharing output.
- `local_report_pdf.dart`: PDF 1.4, printable ASCII-only, one page; rejects Unicode/Arabic and is not a clinical report. CAL-12 consent/privacy/RTL gate still OPEN, PDF patient OFF.
- `docs/operations/PATIENT_DATA_EXPORT.md`: a separate authenticated administrative JSON download with restricted delivery, not the Reports feature.

## Goal / scope
Pure Dart `SyntheticReportFormatter`, deterministic UTF-8 CSV and JSON **fixtures only**, fixed UTC generation instant required, each line has explicit label/value/unit/source and explicit `fixture_scope=synthetic_only` in bytes. No patient data, LLM, network, file system, printing, download, UI, migrations or cross-user storage. Test valid Arabic/FR Unicode and format semantics without implying full PDF RTL qualification.

CSV follows [RFC 4180](https://www.rfc-editor.org/rfc/rfc4180) field quoting/doubled quotes and CRLF separators. Reject spreadsheet formula prefixes or controls (including whitespace/fullwidth lookalikes) instead of trying a universal escape; [OWASP CSV injection guidance](https://owasp.org/www-community/attacks/CSV_Injection) stresses that mitigations vary across spreadsheet engines and save/re-open flows.

**Success proof:** same inputs produce byte-for-byte identical outputs for CSV and JSON, Unicode survives, formula/control variants fail closed, naive timestamps and missing provenance fail closed, tested on exact GitHub HEAD. This is deliberately a strict synthetic subset and **not compatible with all possible clinical values**, including negative numbers as text.

## Patient/release gate
To connect this primitive to actual Reports, resolve **CAL-12**: typed clinical field classes, patient/destination authorization, informed and revocable consent, local file retention, trusted data provenance/units, accessible PDF/RTL/Unicode and OS share behavior, privacy/legal review and threat-model CSV injection across real spreadsheet viewers. Then write end-to-end synthetic fixtures and UI BEFORE/mockup/AFTER same viewports. Until then **no user-visible export button**, no clinical PDF, no merge or Vercel without explicit owner approval.


## 09/11/2026 — D4-B proof via Web print (after incompatible Dart PDF dependency)

**Reason for strategy change (two verified CI dependency errors):** `pdf ^3.13.1` requires Dart >=3.12 while IAMINA pins Flutter 3.41/Dart 3.11. Pinning `pdf 3.12.0` also fails: `pdf <3.13` requires `xml ^6.3.0` while the existing `image 4.9.1` requires `xml ^7.0.1`. Never override the XML constraint, downgrade image or upgrade Flutter just to show a nonclinical fixture. No new Flutter dependency remains in this patch.

**Current safe implementation:** `SyntheticDoctorReport` (manual synthetic readings, UTC provenance, explicit missing values, max 12 observations, valid periods, no patient IDs) and the original `SyntheticReportFormatter` CSV/JSON; `SyntheticDoctorHtml` produces a deterministic offline HTML/CSS template with FR/EN/AR and explicit numerical LTR spans isolated from Arabic RTL labels. Local Inter/NotoSansArabic assets only, no CDN/network, scripting, printing, OS share or patient vault hookup. The **CI-only** tool `frontend/tool/d4_generate_synthetic_pdf.dart` saves artificial HTML and calls local Chromium headless `--print-to-pdf` to produce actual A4 PDFs. CI validates the document with `pdfinfo`/`pdftotext` and renders first pages to PNG via `pdftoppm`; artifacts are technical demonstration files, NOT clinical reports. The product has no D4 export/print UI.

**Limitations and gates:** browser-based printed PDF content is factually deterministic on fixed inputs but Chrome PDF metadata/bytes need not match exactly across runs; **byte-stability is asserted for CSV/JSON only**. The widget has not been validated with live clinical data, multilingual PDF text extraction, screen reader, pagination with more than 12 rows, app-lock, or recipient sharing. **CAL-12** independent medical, DPO, technical QA and linguistic RTL reviews plus D32 derived-metric gate remain open. The generated PDFs carry a visible SYNTHETIC ONLY / NOT FOR CLINICAL USE banner. No Vercel without fresh explicit approval.

**Success evidence needed:** Flutter pub get on existing locked dependencies, analyzer/full tests, dedicated D4 workflow PDF Chrome/Poppler render, inspect artifacts FR/AR/EN and CI status at exact SHA. Keep #954 Draft / unmerged until all applicable proofs.



## 09/11/2026 — Locale warning parity amendment (synthetic-only)

The CI HTML report disclaimer is localized in French and Arabic (alongside the existing English wording). The focused Flutter contract tests assert each locale warning. CI Poppler validates both French and English extraction and numerical content in all three PDFs; Arabic screenshot/glyph extraction still requires the MENA native-human CAL-12 gate before any patient-facing use. This text-only safety clarification does not connect reports to patient data or grant merge/deploy approval.
