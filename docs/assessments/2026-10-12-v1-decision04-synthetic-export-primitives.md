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
