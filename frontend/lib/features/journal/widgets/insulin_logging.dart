double? parseTakenInsulinUnits(String raw) {
  final normalized = raw.trim().replaceAll(',', '.');
  if (normalized.isEmpty) return null;
  final value = double.tryParse(normalized);
  if (value == null || !value.isFinite || value <= 0) return null;
  return value;
}

bool isValidTakenInsulinInput(String raw) {
  if (raw.trim().isEmpty) return true;
  return parseTakenInsulinUnits(raw) != null;
}

String formatTakenInsulinUnits(double value) {
  final fixed = value.toStringAsFixed(2);
  return fixed.replaceFirst(RegExp(r'\.?0+$'), '');
}
