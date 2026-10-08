/// Patient-facing facts from this device only, never AI-generated analysis.
bool refersToRecordedGlucose(String message) {
  final normalized = message.toLowerCase();
  return RegExp(
    r'\b(mesure|glyc[eé]mie|glucose|reading|blood sugar)\b|قياس|سكر',
    caseSensitive: false,
  ).hasMatch(normalized);
}

String localReadingFact(double mgdl, String language) {
  final value = mgdl == mgdl.truncateToDouble()
      ? mgdl.toStringAsFixed(0)
      : mgdl.toStringAsFixed(1);
  if (language == 'en') {
    return 'The most recent reading saved on this device is $value mg/dL. '
        'Whether IAmina can access it on the server has not been verified. '
        'This reading alone does not establish a trend.';
  }
  if (language == 'ar') {
    return 'آخر قياس مسجل على هذا الجهاز هو $value mg/dL. '
        'لم يتم التحقق من توفره لدى IAmina على الخادم. '
        'هذا القياس وحده لا يثبت وجود اتجاه.';
  }
  return 'Votre dernière mesure enregistrée sur cet appareil est de '
      '$value mg/dL. Sa disponibilité auprès d’IAmina sur le serveur '
      'n’est pas vérifiée. Cette mesure seule ne permet pas '
      'd’établir une tendance.';
}
