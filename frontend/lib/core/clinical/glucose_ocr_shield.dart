// GlucoseOcrShield
// ─────────────────────────────────────────────────────────────────────────────
// Validates and sanitizes glucose values extracted from on-device OCR (ML Kit).
//
// Architecture principles:
//   • 100% deterministic — no LLM, no network call, no randomness.
//   • Never silently auto-fills — every result carries a confidence score
//     that the UI uses to decide whether to show a confirmation dialog.
//   • Handles all glucometer output variants:
//       – mg/dL numeric (most EU/MA devices)
//       – mmol/L numeric (UK/CA devices) → converted to mg/dL
//       – "HI"  → glucometer saturated above measurable range (> ~600 mg/dL)
//       – "LO"  → glucometer below measurable range (< ~20 mg/dL)
//   • Physiological bounds: 20–600 mg/dL (outside = rejected)
//
// No ADR violations: this class is pure client-side data validation.
// It does NOT touch the LLM pipeline.
// ─────────────────────────────────────────────────────────────────────────────

/// Result produced by [GlucoseOcrShield.extract].
class GlucoseOcrResult {
  /// Glucose value in mg/dL. Null when nothing valid was detected.
  final double? value;

  /// Confidence in [0.0, 1.0].
  /// ≥ 0.80 → can suggest auto-fill (UI still confirms).
  /// < 0.80 → must show correction dialog.
  final double confidence;

  /// Raw text returned by ML Kit (for debug / UX display).
  final String rawText;

  /// Glucometer displayed "HI" — glucose above measurable range (≳ 600 mg/dL).
  final bool isHI;

  /// Glucometer displayed "LO" — glucose below measurable range (≲ 20 mg/dL).
  final bool isLO;

  /// True if the glucometer unit was detected as mmol/L
  /// and [value] has already been converted to mg/dL (× 18).
  final bool unitWasMmol;

  const GlucoseOcrResult({
    this.value,
    required this.confidence,
    required this.rawText,
    this.isHI = false,
    this.isLO = false,
    this.unitWasMmol = false,
  });

  /// True when a usable numeric value was extracted (not HI / LO / empty).
  bool get hasValue => value != null && !isHI && !isLO;

  /// True when the UI should display a correction modal before accepting.
  bool get needsConfirmation => !hasValue || confidence < 0.80;
}

/// Pure-static shield. Call [GlucoseOcrShield.extract] on the raw OCR text.
class GlucoseOcrShield {
  GlucoseOcrShield._();

  // ── physiological constants ────────────────────────────────────────────────

  static const double _minMgdl = 20.0;
  static const double _maxMgdl = 600.0;

  // ── patterns ───────────────────────────────────────────────────────────────

  /// Matches glucometer "HI" or "HIGH" display.
  static final _hiPattern = RegExp(r'\bH[Ii](?:GH)?\b');

  /// Matches glucometer "LO" or "LOW" display.
  static final _loPattern = RegExp(r'\bL[Oo](?:W)?\b');

  /// Detects mmol/L unit anywhere in the OCR text.
  static final _mmolPattern = RegExp(r'mmol', caseSensitive: false);

  /// Core glucose number pattern.
  ///
  /// Matches 2–3 digit values that could be glucose readings:
  ///   40–99   (hypoglycemia zone)
  ///   100–399 (normal + hyperglycemia zone)
  ///
  /// Deliberately excludes:
  ///   00–39   too low to be a valid reading (sensor error)
  ///   400–600 caught by the 3-digit arm below
  ///   19xx / 20xx  years — excluded because max 3 digits AND bounds check
  static final _glucosePattern = RegExp(r'\b([4-9]\d|[1-3]\d{2}|400)\b');

  /// mmol/L readings: e.g. "6.5", "13.2", "3.8"
  /// Only valid after mmol unit is detected in the same text.
  static final _mmolValuePattern = RegExp(r'\b(\d{1,2}[.,]\d)\b');

  // ── public API ─────────────────────────────────────────────────────────────

  /// Extract and validate a glucose reading from raw ML Kit OCR text.
  ///
  /// Always returns a result (never throws). The caller checks
  /// [GlucoseOcrResult.hasValue] and [GlucoseOcrResult.confidence].
  static GlucoseOcrResult extract(String ocrText) {
    final raw = ocrText.trim();

    if (raw.isEmpty) {
      return GlucoseOcrResult(confidence: 0.0, rawText: raw);
    }

    // ── HI / LO special readings ─────────────────────────────────────────────
    if (_hiPattern.hasMatch(raw)) {
      return GlucoseOcrResult(confidence: 1.0, rawText: raw, isHI: true);
    }
    if (_loPattern.hasMatch(raw)) {
      return GlucoseOcrResult(confidence: 1.0, rawText: raw, isLO: true);
    }

    // ── mmol/L path ───────────────────────────────────────────────────────────
    if (_mmolPattern.hasMatch(raw)) {
      return _extractMmol(raw);
    }

    // ── mg/dL path (default) ─────────────────────────────────────────────────
    return _extractMgdl(raw);
  }

  // ── private helpers ────────────────────────────────────────────────────────

  static GlucoseOcrResult _extractMgdl(String raw) {
    final matches = _glucosePattern
        .allMatches(raw)
        .map((m) => double.tryParse(m.group(0)!))
        .whereType<double>()
        .where((v) => v >= _minMgdl && v <= _maxMgdl)
        .toList();

    if (matches.isEmpty) {
      return GlucoseOcrResult(confidence: 0.0, rawText: raw);
    }

    // Single unambiguous match → high confidence.
    // Multiple matches → lower confidence, UI must ask.
    final value = matches.first;
    final confidence = matches.length == 1 ? 0.92 : 0.58;

    return GlucoseOcrResult(value: value, confidence: confidence, rawText: raw);
  }

  static GlucoseOcrResult _extractMmol(String raw) {
    // Normalise decimal separators (comma → dot)
    final normalised = raw.replaceAll(',', '.');

    final matches = _mmolValuePattern
        .allMatches(normalised)
        .map((m) => double.tryParse(m.group(1)!))
        .whereType<double>()
        .toList();

    if (matches.isEmpty) {
      return GlucoseOcrResult(confidence: 0.0, rawText: raw);
    }

    final mmol = matches.first;
    final mgdl = mmol * 18.0;

    // Bounds check on converted value
    if (mgdl < _minMgdl || mgdl > _maxMgdl) {
      return GlucoseOcrResult(confidence: 0.0, rawText: raw);
    }

    final confidence = matches.length == 1 ? 0.88 : 0.62;

    return GlucoseOcrResult(
      value: mgdl,
      confidence: confidence,
      rawText: raw,
      unitWasMmol: true,
    );
  }
}
