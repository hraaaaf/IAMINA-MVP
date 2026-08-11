import 'dart:math';

class GlucoseFormatter {
  static const double mgdlToMmolFactor = 18.018;

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
    final padding = range > 0
        ? range * 0.1
        : (unit.toLowerCase() == 'mmol/l' ? 1.0 : 20.0);

    return [max(0.0, minValue - padding), maxValue + padding];
  }
}
