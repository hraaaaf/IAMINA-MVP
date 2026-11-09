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

## 09/11/2026 — D4-B follow-up: doctor-readable PDF template (SYNTHETIC ONLY)

Decision D4 remains multi-format, **including the eventual doctor-readable PDF** (not a separate business decision). The CSV/JSON formatter remains confined to synthetic fixtures. This follow-up adds `SyntheticDoctorReport` (manual glucose entries only, UTC period and generation timestamp, explicit missing values), and `SyntheticDoctorPdf` built with the pure-Dart `pdf` library and the already-vendored Inter/NotoSansArabic fonts. **No patient ID, patient vault, network, file writes, route, share sheet, printing or download is connected in the product.** Synthetic PDF generation to files occurs only in the CI tool `frontend/tool/d4_generate_synthetic_pdf.dart` using artificial observations.

The PDF has an explicit **SYNTHETIC / NON CLINIQUE** banner, sources and period, manual observations in mg/dL and no CGM/TIR/GMI, recommendation, threshold, diagnosis or invented value. The Arabic layout keeps dates and numbers in independent left-to-right spans and Arabic labels in right-to-left spans. This avoids naive string reversal, but does **not** by itself certify complete typographic Arabic or accessibility compliance; the CI workflow renders actual FR/EN/AR pages and publishes screenshots for review. Dates and rows are bounded (12 observations), UTC only, sorted/unique and within the chosen period. CSV/JSON are byte-stable on identical typed inputs; PDF source content is deterministic, but PDF output byte-for-byte identity is **not** claimed without auditing the library document IDs.

**Gates remain CLOSED:** CAL-12 independent clinical, DPO/privacy, recipient/consent and FR/AR/RTL visual/accessibility review before reading real patient data or exposing a PDF export/share action; D32 governs nontrivial derived clinical metrics. `LocalReportPdf` ASCII-only remains untouched and unqualified for clinical export. Flutter's `pdf: ^3.13.1` adds a new dependency; dependency resolution and license/security review are required by CI. Any new PDF clinical functionality needs a new explicit owner acceptance for release and a separate Vercel authorization. Never mistake synthetic CI artifacts for a doctor-ready clinical report.

**Proof required:** exact-HEAD Flutter analyzer/full tests/PWA, D4 synthetic fixture tests, successful generation of 3 actual PDFs and screenshot/visual audit at identical page size, plus review of any RTL numeric ordering. No merger just from green synthetic tests when privacy/clinical gates remain open.
