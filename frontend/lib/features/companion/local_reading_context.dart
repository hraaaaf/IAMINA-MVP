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

 
/// Truthful local empty state: never infer what a remote account has stored.
String localReadingUnavailableFact(String language) {
  if (language == 'en') {
    return 'No glucose reading is recorded on this device yet. '
        'I have not verified whether a reading exists on the server.';
  }
  if (language == 'ar') {
    return 'لا يوجد قياس سكر مسجل على هذا الجهاز حتى الآن. '
        'لم أتحقق من وجود قياس على الخادم.';
  }
  return 'Aucune mesure de glycémie n’est enregistrée sur cet appareil '
      'pour le moment. Je n’ai pas vérifié si une mesure existe sur le serveur.';
}
