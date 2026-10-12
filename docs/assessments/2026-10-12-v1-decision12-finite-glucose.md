# IAMINA V1 #12 — Glucose value finiteness guard before slider

**Goal**: fail closed on missing/non-numeric/NaN/Infinity glucose values and on overflow during existing mmol/L→mg/dL normalization, with no guessed measurement or new clinical thresholds.

**BEFORE verified in [issue #971](https://github.com/hraaaaf/IAMINA-MVP/issues/971)**: AddLogSheet held a blank TextEditingController, parsed freeform text with double.tryParse, normalized mmol/L via multiplication by 18.0 and checked null/positive only. Finite validation was not explicit. This is a code-level safety concern; it is NOT evidence the current text keyboard allows users to enter malicious strings.

**AFTER candidate**: pure parsePositiveFiniteGlucoseInput and normalizeFiniteGlucoseMgdl functions reject non-finite, negative, missing and unsupported units, and preserve valid pre-existing input and conversion factor. _hasValidGlucose and _saveLog reuse them, so no negative/nonfinite values can reach the existing Drift insertion via this form. Tests cover NaN/Infinity/negative, overflow, comma decimal, empty fields and two supported units.

**Not in this patch**: no glucose slider, new measurement min/max, dose, threshold, clinical recommendation, remote export, ML, CGM or new presentation. A bounded slider needs qualified medical + accessibility/UX decisions, direct text-entry escape route and BEFORE/mockup/AFTER across 390×844, 768×1024 and 1280×900. A finite-only number can still be clinically implausible; this is a narrow technical guard, not clinical certification.

**Release status**: DRAFT, CI exact HEAD pending, no merge or Vercel without permission. Original decisions #1 and #25 CGM last.
