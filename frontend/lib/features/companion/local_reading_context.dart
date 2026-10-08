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


/// A Drift sync flag does not prove the backend AI has the reading in context.
/// This disclosure stays separate from the local measurement and AI reply.
String localReadingSyncDisclosure(
  String? syncStatus,
  String language, {
  bool syncFailed = false,
}) {
  if (syncFailed) {
    if (language == 'en') {
      return ' The last sync attempt failed. The reading remains on this device.';
    }
    if (language == 'ar') {
      return ' فشلت آخر محاولة للمزامنة. ما زال القياس محفوظًا على هذا الجهاز.';
    }
    return ' La dernière tentative de synchronisation a échoué. '
        'La mesure reste enregistrée sur cet appareil.';
  }
  if (syncStatus == 'pending') {
    if (language == 'en') {
      return ' This reading is still awaiting synchronization.';
    }
    if (language == 'ar') {
      return ' هذا القياس لا يزال في انتظار المزامنة.';
    }
    return ' Cette mesure est encore en attente de synchronisation.';
  }
  if (syncStatus == 'synced') {
    if (language == 'en') {
      return ' This device marks the reading as synchronized, '
          'but IAmina’s access to it is unverified.';
    }
    if (language == 'ar') {
      return ' يشير هذا الجهاز إلى مزامنة القياس، '
          'لكن لم يتم التحقق من وصول IAmina إليه.';
    }
    return ' Cette mesure est marquée comme synchronisée sur cet appareil, '
        'mais son accès par IAmina n’est pas vérifié.';
  }
  return '';
}
