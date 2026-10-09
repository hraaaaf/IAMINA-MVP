import 'dart:math';

class GlucoseFormatter {
  /// Same precision as the active backend log-entry normalization contract.
  /// Display-only conversion; no change to clinical target thresholds.
  static const double mgdlToMmolFactor = 18.016;

  /// Formate une valeur de glycémie selon la préférence de l'utilisateur.
  /// [valueMgDl] : Valeur brute en mg/dL (stockage standard).
  /// [unit] : "mg/dL" ou "mmol/L".
  static String format(double valueMgDl, String unit) {
    if (unit.toLowerCase() == 'mmol/l') {
      final mmolValue = valueMgDl / mgdlToMmolFactor;
      return '${mmolValue.toStringAsFixed(1)} mmol/L';
    }
    return '${valueMgDl.toStringAsFixed(0)} mg/dL';
  }

  /// Convertit pour les calculs ou les graphiques si nécessaire.
  static double convert(double valueMgDl, String unit) {
    if (unit.toLowerCase() == 'mmol/l') {
      return valueMgDl / mgdlToMmolFactor;
    }
    return valueMgDl;
  }

  /// Only these persisted profile units can authorize a glucose write.
  /// Read-only legacy screens are audited separately; writes fail closed.
  static bool isSupportedUnit(String unit) {
    final normalized = unit.trim().toLowerCase();
    return normalized == 'mg/dl' || normalized == 'mmol/l';
  }

  /// Converts user-entered values into canonical mg/dL storage.
  /// An unknown profile unit must never silently become mg/dL.
  static double toMgDl(double value, String unit) {
    if (!isSupportedUnit(unit)) {
      throw ArgumentError.value(unit, 'unit', 'Unknown glucose unit');
    }
    return unit.trim().toLowerCase() == 'mmol/l'
        ? value * mgdlToMmolFactor
        : value;
  }

  /// An unchanged rounded display must never rewrite the recorded glucose.
  static double editedToMgDl(
    double value,
    String unit, {
    double? initialDisplayedValue,
    double? initialMgDl,
  }) {
    if (!isSupportedUnit(unit)) {
      throw ArgumentError.value(unit, 'unit', 'Unknown glucose unit');
    }
    if (initialDisplayedValue != null &&
        initialMgDl != null &&
        value == initialDisplayedValue) {
      return initialMgDl;
    }
    return toMgDl(value, unit);
  }

  /// Calcule les bornes optimales pour l'axe Y du graphique.
  /// Retourne [min, max] avec une marge de respiration.
  static List<double> getChartBounds(List<double> values, String unit) {
    if (values.isEmpty) {
      return unit.toLowerCase() == 'mmol/l' ? [4.0, 10.0] : [70.0, 180.0];
    }

    final convertedValues = values.map((v) => convert(v, unit)).toList();
    final minValue = convertedValues.reduce(min);
    final maxValue = convertedValues.reduce(max);

    // Marge de 10% en haut et en bas
    final range = maxValue - minValue;
    final padding = range > 0 ? range * 0.1 : (unit.toLowerCase() == 'mmol/l' ? 1.0 : 20.0);

    return [
      max(0.0, minValue - padding),
      maxValue + padding,
    ];
  }
}
