/// D22 G1/G4/G7 — ISOLATED, NOT WIRED INTO PATIENT RUNTIME.
///
/// This pure Dart contract preserves an expressly declared input unit and
/// the original value. It does not modify Drift, API, glycemic targets,
/// CGM metrics, saved patient data, or production conversion behavior.
///
/// A patient's display preference is NOT evidence of a stored value's unit.
/// Historical rows without explicit source units remain unclassified.
enum GlucoseSourceUnit {
  mgDl('mg/dL'),
  mmolL('mmol/L');

  const GlucoseSourceUnit(this.ucumCode);

  /// UCUM case-sensitive code; never infer aliases silently.
  final String ucumCode;

  static GlucoseSourceUnit? fromExplicitUcumCode(String? code) {
    return switch (code) {
      'mg/dL' => GlucoseSourceUnit.mgDl,
      'mmol/L' => GlucoseSourceUnit.mmolL,
      _ => null,
    };
  }
}

/// 'User entered' is an audit provenance, NOT validation by a clinician,
/// certified device, laboratory, or authenticated external source.
enum GlucoseValueProvenance {
  userEntered,
  legacyUnknown,
}

final class GlucoseConversionContract {
  const GlucoseConversionContract._();

  /// NIST glucose molar mass = 180.1559 g/mol:
  /// 1 mmol/L = 18.01559 mg/dL.
  /// This calculation is staged; the existing app still uses legacy factors
  /// (18.0 / 18.018) until G4 and a backward-compatibility policy are signed.
  static const double mgDlPerMmolL = 18.01559;

  static double toMgDl(double value, GlucoseSourceUnit sourceUnit) {
    _checkReading(value);
    return sourceUnit == GlucoseSourceUnit.mgDl
        ? value
        : value * mgDlPerMmolL;
  }

  static double convert(
    double mgDl,
    GlucoseSourceUnit displayUnit,
  ) {
    _checkReading(mgDl);
    return displayUnit == GlucoseSourceUnit.mgDl
        ? mgDl
        : mgDl / mgDlPerMmolL;
  }

  static void _checkReading(double value) {
    if (!value.isFinite || value <= 0) {
      throw ArgumentError.value(
        value,
        'value',
        'Glucose value must be finite and positive',
      );
    }
  }
}

/// An immutable evidence object, not a migration or a persistence model.
/// Both creation paths keep the ORIGINAL unrounded numeric value.
final class GlucoseQuantityEvidence {
  const GlucoseQuantityEvidence._({
    required this.originalRawValue,
    required this.originalUnit,
    required this.provenance,
  });

  factory GlucoseQuantityEvidence.userEntry({
    required double originalValue,
    required GlucoseSourceUnit declaredUnit,
  }) {
    GlucoseConversionContract._checkReading(originalValue);
    return GlucoseQuantityEvidence._(
      originalRawValue: originalValue,
      originalUnit: declaredUnit,
      provenance: GlucoseValueProvenance.userEntered,
    );
  }

  /// Never guess units from magnitudes, target defaults, or display settings.
  ///
  /// Invalid historical numerics must also remain UNCLASSIFIED; preserving a
  /// raw value here is not a claim it is valid for display or calculation.
  const GlucoseQuantityEvidence.unknownLegacy({
    required double storedValue,
  }) : originalRawValue = storedValue,
       originalUnit = null,
       provenance = GlucoseValueProvenance.legacyUnknown;

  final double originalRawValue;
  final GlucoseSourceUnit? originalUnit;
  final GlucoseValueProvenance provenance;

  /// Manual source-unit declaration is not device/lab verification.
  bool get hasExplicitSourceUnit =>
      provenance == GlucoseValueProvenance.userEntered &&
      originalUnit != null &&
      originalRawValue.isFinite &&
      originalRawValue > 0;

  /// Fails CLOSED for legacy readings with unknown original unit.
  double? get canonicalMgDl => hasExplicitSourceUnit
      ? GlucoseConversionContract.toMgDl(
          originalRawValue,
          originalUnit!,
        )
      : null;

  /// Display conversion does not mutate the original value or source unit.
  /// Returns null instead of fabricating units for historical values.
  double? displayValue(GlucoseSourceUnit displayUnit) {
    final mgDl = canonicalMgDl;
    if (mgDl == null) return null;
    if (displayUnit == originalUnit) return originalRawValue;
    return GlucoseConversionContract.convert(mgDl, displayUnit);
  }
}
