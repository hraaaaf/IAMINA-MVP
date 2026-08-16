import 'package:amina/l10n/app_localizations.dart';

extension DocumentImportLocalizedCopy on AppLocalizations {
  String get _languageCode => localeName.split(RegExp('[-_]')).first;

  String _pick({required String en, required String fr, required String ar}) {
    return switch (_languageCode) {
      'ar' => ar,
      'fr' => fr,
      _ => en,
    };
  }

  String get fileReadFailed => _pick(en: 'Unable to read this file.', fr: 'Impossible de lire le fichier.', ar: 'تعذر قراءة الملف.');
  String documentError(Object error) => _pick(en: 'Error: $error', fr: 'Erreur : $error', ar: 'خطأ: $error');
  String get documentAnalysisFailed => _pick(en: 'The server could not analyze this document. Please try again.', fr: 'Le serveur n’a pas pu analyser ce document. Veuillez réessayer.', ar: 'تعذر على الخادم تحليل هذا المستند. يرجى المحاولة مرة أخرى.');
  String get documentConfirmationFailed => _pick(en: 'Confirmation failed. The document was not saved.', fr: 'La confirmation a échoué. Le document n’a pas été enregistré.', ar: 'فشل التأكيد. لم يتم حفظ المستند.');
  String get analyzedDocument => _pick(en: 'Analyzed document', fr: 'Document analysé', ar: 'المستند المحلل');
  String get glucoseReadings => _pick(en: 'Glucose readings', fr: 'Glycémies', ar: 'قراءات الغلوكوز');
  String get labResults => _pick(en: 'Lab results', fr: 'Bilan biologique', ar: 'نتائج التحاليل');
  String get medicines => _pick(en: 'Medications detected — not imported', fr: 'Médicaments détectés — non importés', ar: 'أدوية مكتشفة — لن يتم استيرادها');
  String get clinicalNotes => _pick(en: 'Clinical notes', fr: 'Observations cliniques', ar: 'ملاحظات سريرية');
  String get confirmImport => _pick(en: '✓ Confirm import', fr: '✓ Confirmer l’import', ar: '✓ تأكيد الاستيراد');
  String get cancelImport => _pick(en: 'Cancel', fr: 'Annuler', ar: 'إلغاء');
  String get documentImported => _pick(en: 'Document imported!', fr: 'Document importé !', ar: 'تم استيراد المستند!');
  String get importFailed => _pick(en: 'Import failed', fr: 'Erreur lors de l’import', ar: 'فشل الاستيراد');
  String get importedGlucoseReadings => _pick(en: 'Glucose readings imported', fr: 'Glycémies importées', ar: 'قراءات الغلوكوز المستوردة');
  String get duplicatesIgnored => _pick(en: 'Duplicates ignored', fr: 'Doublons ignorés', ar: 'التكرارات المتجاهلة');
  String get backToDashboard => _pick(en: 'Back to dashboard', fr: 'Retour au tableau de bord', ar: 'العودة إلى لوحة المتابعة');
  String get importAnotherDocument => _pick(en: 'Import another document', fr: 'Importer un autre document', ar: 'استيراد مستند آخر');
  String get analyzingDocument => _pick(en: 'Analyzing document…', fr: 'Analyse du document en cours…', ar: 'جارٍ تحليل المستند…');
  String get savingDocument => _pick(en: 'Saving…', fr: 'Enregistrement en cours…', ar: 'جارٍ الحفظ…');
  String confidencePercent(int value) => _pick(en: 'Confidence: $value%', fr: 'Confiance : $value %', ar: 'الثقة: $value٪');
  String get verifyBeforeConfirming => _pick(en: 'Review the data below before confirming.', fr: 'Vérifiez les données ci-dessous avant de confirmer.', ar: 'راجع البيانات أدناه قبل التأكيد.');
  String additionalReadings(int value) => _pick(en: '+ $value more readings', fr: '+ $value autres mesures', ar: '+ $value قراءات إضافية');
  String get fastingGlucose => _pick(en: 'Fasting glucose', fr: 'Glucose à jeun', ar: 'غلوكوز الصيام');
  String get totalCholesterol => _pick(en: 'Total cholesterol', fr: 'Cholestérol total', ar: 'الكوليسترول الكلي');
  String get triglycerides => _pick(en: 'Triglycerides', fr: 'Triglycérides', ar: 'الدهون الثلاثية');
  String get creatinine => _pick(en: 'Creatinine', fr: 'Créatinine', ar: 'الكرياتينين');
  String get reportDate => _pick(en: 'Report date', fr: 'Date du bilan', ar: 'تاريخ التحليل');
  String get noMedicalDataDetected => _pick(en: 'No importable medical data was detected in this document.', fr: 'Aucune donnée médicale importable détectée dans ce document.', ar: 'لم يتم اكتشاف بيانات طبية قابلة للاستيراد في هذا المستند.');
}
