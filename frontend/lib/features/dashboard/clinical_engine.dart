import 'dart:math' as math;
import '../../data/drift/database.dart';

/// Clinical Intelligence Engine (Phase 6).
/// 
/// Centralizes all medical metric calculations (TIR, GMI, CV) to ensure
/// consistency between the dashboard, AI summaries, and clinical reports.
class ClinicalEngine {
  /// Time In Range (TIR) — offline fallback.
  /// Returns double to match /api/v1/kpis/ response type.
  /// Standard ADA range: 70–180 mg/dL.
  static double calcTIR(List<LogEntryData> logs, double low, double high) {
    if (logs.isEmpty) return 0.0;
    final inRange = logs.where((l) => l.bloodSugar >= low && l.bloodSugar <= high).length;
    return double.parse(((inRange / logs.length) * 100).toStringAsFixed(1));
  }

  /// Time Above Range (TAR) - High — offline fallback.
  static double calcHigh(List<LogEntryData> logs, double high) {
    if (logs.isEmpty) return 0.0;
    return double.parse(
      ((logs.where((l) => l.bloodSugar > high && l.bloodSugar <= 250).length / logs.length) * 100)
          .toStringAsFixed(1),
    );
  }

  /// Time Above Range (TAR) - Very High (> 250 mg/dL) — offline fallback.
  static double calcVeryHigh(List<LogEntryData> logs) {
    if (logs.isEmpty) return 0.0;
    return double.parse(
      ((logs.where((l) => l.bloodSugar > 250).length / logs.length) * 100).toStringAsFixed(1),
    );
  }

  /// Time Below Range (TBR) - Low — offline fallback.
  static double calcLow(List<LogEntryData> logs, double low) {
    if (logs.isEmpty) return 0.0;
    return double.parse(
      ((logs.where((l) => l.bloodSugar < low && l.bloodSugar >= 54).length / logs.length) * 100)
          .toStringAsFixed(1),
    );
  }

  /// Time Below Range (TBR) - Very Low (< 54 mg/dL) — offline fallback.
  static double calcVeryLow(List<LogEntryData> logs) {
    if (logs.isEmpty) return 0.0;
    return double.parse(
      ((logs.where((l) => l.bloodSugar < 54).length / logs.length) * 100).toStringAsFixed(1),
    );
  }

  /// Glucose Management Indicator (GMI) — offline fallback.
  /// ADA 2023 Formula: GMI(%) = 3.31 + 0.02392 × mean_glucose_mg/dL.
  static double calcGMI(List<LogEntryData> logs) {
    if (logs.isEmpty) return 0.0;
    final mean = calcMean(logs);
    return double.parse((3.31 + 0.02392 * mean).toStringAsFixed(1));
  }

  /// Coefficient of Variation (CV) — offline fallback.
  /// Formula: (stdDev / mean) × 100. Goal < 36%.
  static double calcCV(List<LogEntryData> logs) {
    if (logs.length < 2) return 0.0;
    final mean = calcMean(logs);
    final variance = logs.map((l) => math.pow(l.bloodSugar - mean, 2)).reduce((a, b) => a + b) / (logs.length - 1);
    return double.parse(((math.sqrt(variance) / mean) * 100).toStringAsFixed(1));
  }

  /// Mean blood glucose level — offline fallback.
  static double calcMean(List<LogEntryData> logs) {
    if (logs.isEmpty) return 0.0;
    return logs.map((l) => l.bloodSugar).reduce((a, b) => a + b) / logs.length;
  }
}
