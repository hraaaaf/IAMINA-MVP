/// D22-B candidate only. NOT wired to patient UI, storage or metrics.
/// G1/G4 clinical authority and G7 migration approval are still pending.
/// The retained source text must be persisted verbatim when an approved
/// schema exists; derived numeric representations are never authoritative.
enum D22GlucoseUnit {
  mgDl('mg/dL'),
  mmolL('mmol/L');

  const D22GlucoseUnit(this.code);
  final String code;
}

/// Reject aliases and unsupported/missing units rather than guessing from
/// a display preference. A typed import boundary may explicitly normalize
/// known aliases, but must do so under its own reviewed contract.
D22GlucoseUnit? d22ParseGlucoseUnit(String? unit) {
  switch (unit) {
    case 'mg/dL':
      return D22GlucoseUnit.mgDl;
    case 'mmol/L':
      return D22GlucoseUnit.mmolL;
    default:
      return null;
  }
}

/// Mathematically derived candidate from NIST glucose molecular weight
/// 180.1559 g/mol. NOT activated for clinical production or approved as
/// the shared D19/D22 software conversion constant.
const double d22CandidateMgDlPerMmolL = 18.01559;

/// Never takes a target/unit from an untyped PatientProfiles legacy column.
/// Its original text and explicitly captured source unit remain immutable.
final class D22CapturedGlucoseCandidate {
  const D22CapturedGlucoseCandidate({
    required this.rawInput,
    required this.sourceUnit,
    required this.ownerId,
  });

  final String rawInput;
  final String? sourceUnit;
  final int ownerId;

  D22GlucoseUnit? get typedSourceUnit => d22ParseGlucoseUnit(sourceUnit);

  double? get sourceValue {
    if (ownerId <= 0 || typedSourceUnit == null) return null;
    final parsed = double.tryParse(rawInput);
    if (parsed == null || !parsed.isFinite || parsed <= 0) return null;
    return parsed;
  }

  /// Returns null (unknown) rather than a silently assumed quantity.
  /// No clinical range or target classification is computed here.
  double? valueForDisplay(D22GlucoseUnit displayUnit) {
    final value = sourceValue;
    final originalUnit = typedSourceUnit;
    if (value == null || originalUnit == null) return null;
    if (originalUnit == displayUnit) return value;

    final result = originalUnit == D22GlucoseUnit.mgDl
        ? value / d22CandidateMgDlPerMmolL
        : value * d22CandidateMgDlPerMmolL;
    return result.isFinite && result > 0 ? result : null;
  }
}

/// Can be submitted for clinical *review*, never used for in/out-target
/// classification. sourceReference is metadata, NOT trusted proof that
/// an endocrinologist has actually authenticated or approved the target.
final class D22UnapprovedTargetCandidate {
  const D22UnapprovedTargetCandidate({
    required this.ownerId,
    required this.sourceReference,
    required this.lower,
    required this.upper,
  });

  final int ownerId;
  final String? sourceReference;
  final D22CapturedGlucoseCandidate lower;
  final D22CapturedGlucoseCandidate upper;

  bool canBeSubmittedForReview(int requestedOwner) {
    if (ownerId <= 0 ||
        requestedOwner != ownerId ||
        lower.ownerId != ownerId ||
        upper.ownerId != ownerId ||
        sourceReference == null ||
        sourceReference!.trim().isEmpty) {
      return false;
    }
    final low = lower.valueForDisplay(D22GlucoseUnit.mgDl);
    final high = upper.valueForDisplay(D22GlucoseUnit.mgDl);
    return low != null && high != null && low < high;
  }
}
